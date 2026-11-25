import json
import re
from typing import Optional, Dict

def extract_think_and_answer(output_text):
    """
    从给定的模型输出文本中提取 <think> 标签内的思考内容
    以及标签后的 JSON 答案，返回包含 'think' 和 'answer' 的字典。

    Args:
        output_text (str): 包含 <think> 标签和 JSON 的完整输出文本。

    Returns:
        dict: 包含 'think' (str) 和 'answer' (dict) 的字典。
    """
    # 提取 <think> 标签内的内容
    think_match = re.search(r'<think>(.*?)</think>', output_text, re.DOTALL)
    if think_match:
        think_str = think_match.group(1).strip()
    else:
        think_str = ""

    # 移除 <think> 标签部分，剩余部分应为 <answer>{JSON}</answer>
    remaining = re.sub(r'<think>.*?</think>', '', output_text, flags=re.DOTALL).strip()
    # 剥掉 <answer> 标签
    remaining = re.sub(r'</?answer>', '', remaining).strip()

    # 解析 JSON
    try:
        answer_dict = json.loads(remaining)
    except json.JSONDecodeError:
        # 兜底：在最内层花括号范围内尝试
        s, e = remaining.find('{'), remaining.rfind('}')
        if 0 <= s < e:
            try:
                answer_dict = json.loads(remaining[s:e + 1])
            except json.JSONDecodeError:
                answer_dict = {}
        else:
            answer_dict = {}

    if not isinstance(answer_dict, dict):
        answer_dict = {}

    return {
        "think": think_str,
        "answer": answer_dict
    }

def weighted_value_similarity_reward(target_scores: dict, predicted_scores: dict, weights: list) -> float:
    """
    评估预测分数与目标分数接近程度的奖励函数。
    总分 2.0 分：
    - 1.0 分来自于 5 个单项分数的接近程度（平均绝对误差）。
    - 1.0 分来自于 5 个分数的加权总分的接近程度。
    """
    expected_keys = [
        "correctness_of_code_answer",
        "relevance_and_sufficiency",
        "clarity_of_question",
        "quality_of_code_answer",
        "quality_of_context"
    ]

    if len(weights) != len(expected_keys):
        raise ValueError("权重数组的长度必须为 5，与评分项一一对应。")

    individual_similarity_sum = 0.0
    target_weighted_sum = 0.0
    pred_weighted_sum = 0.0
    total_weight = sum(weights)

    for i, key in enumerate(expected_keys):
        target_val = target_scores.get(key)
        pred_val = predicted_scores.get(key)

        # 验证并限制 target 值为 0.0 - 10.0
        if isinstance(target_val, bool) or not isinstance(target_val, (int, float)):
            target_val = 0.0
        target_val = max(0.0, min(10.0, float(target_val)))

        # 验证并限制 predicted 值为 0.0 - 10.0
        if isinstance(pred_val, bool) or not isinstance(pred_val, (int, float)):
            pred_val = 0.0
        else:
            pred_val = max(0.0, min(10.0, float(pred_val)))

        # 1. 计算单项相似度
        absolute_error = abs(target_val - pred_val)
        individual_similarity_sum += 1.0 - (absolute_error / 10.0)

        # 2. 累加加权总分
        target_weighted_sum += target_val * weights[i]
        pred_weighted_sum += pred_val * weights[i]

    # 指标一：单项平均相似度 (0.0 - 1.0 分)
    score_component_1 = individual_similarity_sum / len(expected_keys)

    # 指标二：加权总分相似度 (0.0 - 1.0 分)
    if total_weight > 0:
        max_possible_weighted_error = 10.0 * total_weight
        weighted_absolute_error = abs(target_weighted_sum - pred_weighted_sum)
        score_component_2 = 1.0 - (weighted_absolute_error / max_possible_weighted_error)
    else:
        score_component_2 = 1.0  # 如果权重全为0，认为总分完美匹配

    # 合并得分 (0.0 - 2.0)
    final_score = score_component_1 + score_component_2

    return max(0.0, min(2.0, final_score))

def format_reward_function(output_text: str) -> float:
    """论文设定：R_format = R_think + R_answer_fmt，各 ±0.5。

    R_think: <think>...</think> 块存在且顺序正确则 +0.5，否则 -0.5。
    R_answer_fmt: think 之后的 answer 块能解析出合法 JSON（5 个数值键，0-10）则 +0.5，否则 -0.5。
    """
    score = 0.0

    # R_think
    think_start = output_text.find("<think>")
    think_end = output_text.find("</think>")
    think_ok = (think_start != -1 and think_end != -1 and think_start < think_end)
    score += 0.5 if think_ok else -0.5

    # R_answer_fmt
    parsed_data = extract_think_and_answer(output_text)["answer"]
    answer_ok = isinstance(parsed_data, dict) and bool(parsed_data)
    if answer_ok:
        expected_keys = {
            "correctness_of_code_answer",
            "relevance_and_sufficiency",
            "clarity_of_question",
            "quality_of_code_answer",
            "quality_of_context",
        }
        for key in expected_keys:
            val = parsed_data.get(key)
            if isinstance(val, bool) or not isinstance(val, (int, float)) or not (0.0 <= val <= 10.0):
                answer_ok = False
                break
    score += 0.5 if answer_ok else -0.5

    return score

def judge_reward(completions, response_think, response_answer, weights, **kwargs):
    """GRPO 奖励函数（对齐论文设定）：

    R(Y) = R_format + R_score
    - R_format: think/answer 格式各 ±0.5（见 format_reward_function）
    - R_score = R_total + Σ_k R_sub^(k)，仅当 answer JSON 成功解析时计入：
        R_total = max(0, 1 - |Δ_total|/10)，total 为 5 个子分的均值
        R_sub^(k) = 0.2 · max(0, 1 - |Δ_k|/10)
    """
    scores = []

    # 调试：每次调用采样前 2 条原始输出落盘，供诊断
    try:
        with open("grpo_completions_debug.jsonl", "a", encoding="utf-8") as f:
            for c in list(completions)[:2]:
                f.write(json.dumps({"raw": str(c)[:3000]}, ensure_ascii=False) + "\n")
    except Exception:
        pass

    expected_keys = [
        "correctness_of_code_answer",
        "relevance_and_sufficiency",
        "clarity_of_question",
        "quality_of_code_answer",
        "quality_of_context",
    ]

    for i, completion in enumerate(completions):
        score = format_reward_function(completion)
        response = extract_think_and_answer(completion)
        pred = response["answer"]
        if isinstance(pred, dict) and pred:
            try:
                target = json.loads(response_answer[i])
            except (json.JSONDecodeError, TypeError):
                target = None
            if isinstance(target, dict) and target:
                def clamp(v):
                    if isinstance(v, bool) or not isinstance(v, (int, float)):
                        return 0.0
                    return max(0.0, min(10.0, float(v)))
                # R_sub：5 个子维度
                for key in expected_keys:
                    delta = abs(clamp(pred.get(key)) - clamp(target.get(key)))
                    score += 0.2 * max(0.0, 1.0 - delta / 10.0)
                # R_total：5 子分均值的总分相似度
                pred_total = sum(clamp(pred.get(k)) for k in expected_keys) / 5.0
                target_total = sum(clamp(target.get(k)) for k in expected_keys) / 5.0
                score += max(0.0, 1.0 - abs(pred_total - target_total) / 10.0)
        scores.append(score)
    print("scores", scores)
    return scores
