import argparse
import json
import os
import re
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config
from src.data_utils import load_json
from src.prompts import system_prompt_ori, create_reader_request_processed
from src.rewards import extract_think_and_answer
from src.selection import select_top_percent

SCORE_KEYS = [
    "correctness_of_code_answer",
    "relevance_and_sufficiency",
    "clarity_of_question",
    "quality_of_code_answer",
    "quality_of_context",
]


def adapt_sample(sample):
    """字段适配：finqa 数据中的 program 对应 prompt 模板中的 code。"""
    adapted = dict(sample)
    if "code" not in adapted and "program" in adapted:
        adapted["code"] = adapted["program"]
    return adapted


def build_prompt(tokenizer, sample):
    messages = [
        {"role": "system", "content": system_prompt_ori},
        {"role": "user", "content": create_reader_request_processed(sample)},
    ]
    return tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )


def parse_scores(text):
    """从模型输出中解析五项分数；解析失败返回 None。"""
    answer = extract_think_and_answer(text)["answer"]
    if not answer:  # 输出含 <answer> 标签时兜底
        t = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        t = re.sub(r'</?answer>', '', t).strip()
        s, e = t.find('{'), t.rfind('}')
        if 0 <= s < e:
            try:
                answer = json.loads(t[s:e + 1])
            except json.JSONDecodeError:
                answer = None
    if not isinstance(answer, dict) or not answer:
        return None
    scores = {}
    for key in SCORE_KEYS:
        val = answer.get(key)
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            return None
        scores[key] = max(0.0, min(10.0, float(val)))
    return scores


def main():
    parser = argparse.ArgumentParser(description="用评分器模型给数据打分并提取前 n%%")
    parser.add_argument("--config", default=None, help="config.yaml 路径")
    parser.add_argument("--input", required=True, help="待评分数据（JSON 列表）")
    parser.add_argument("--output", required=True, help="评分结果输出路径")
    parser.add_argument("--selected-output", default=None,
                        help="前 n%% 筛选结果输出路径，默认为 <output>.selected.json")
    parser.add_argument("--percent", type=float, default=None, help="覆盖 config 中的 percent")
    args = parser.parse_args()

    cfg = load_config(args.config)
    score_cfg = cfg.get("score", {})
    model_path = score_cfg.get("model_path", "../rl-main-2")
    max_new_tokens = score_cfg.get("max_new_tokens", 2048)
    batch_size = score_cfg.get("batch_size", 4)
    percent = args.percent if args.percent is not None else score_cfg.get("percent", 10)
    seed = score_cfg.get("seed", 42)

    selected_output = args.selected_output or args.output + ".selected.json"

    data = load_json(args.input)
    print(f"共加载 {len(data)} 条数据，模型: {model_path}")

    # 断点续跑：若输出文件已存在，跳过已成功解析的样本
    done_by_id = {}
    if os.path.exists(args.output):
        try:
            for r in load_json(args.output):
                if r.get("judge_raw_output") and r.get("judge_scores") is not None:
                    done_by_id[r.get("id")] = r
        except Exception as e:
            print(f"警告: 读取已有输出失败（{e}），从头开始")
            done_by_id = {}
    if done_by_id:
        print(f"断点续跑: 已有 {len(done_by_id)} 条有效评分，跳过")
        todo_idx = [i for i, s in enumerate(data) if s.get("id") not in done_by_id]
    else:
        todo_idx = list(range(len(data)))
    results = [None] * len(data)

    def save_results():
        merged = []
        for i, s in enumerate(data):
            if results[i] is not None:
                merged.append(results[i])
            elif s.get("id") in done_by_id:
                merged.append(done_by_id[s.get("id")])
            else:
                merged.append({**s, "judge_scores": None,
                               "judge_avg_score": None, "judge_raw_output": ""})
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    try:
        import flash_attn  # noqa: F401
        attn_impl = "flash_attention_2"
    except ImportError:
        attn_impl = "sdpa"
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        device_map="auto",
        attn_implementation=attn_impl,
    )
    model.eval()

    prompts = [build_prompt(tokenizer, adapt_sample(data[i])) for i in todo_idx]

    n_done = 0
    for b, start in enumerate(range(0, len(todo_idx), batch_size)):
        batch_prompts = prompts[start:start + batch_size]
        inputs = tokenizer(batch_prompts, return_tensors="pt", padding=True,
                           add_special_tokens=False).to(model.device)
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
            )
        generated = output_ids[:, inputs["input_ids"].shape[1]:]
        texts = tokenizer.batch_decode(generated, skip_special_tokens=True)

        for i, text in zip(todo_idx[start:start + batch_size], texts):
            scores = parse_scores(text)
            avg_score = sum(scores.values()) / len(SCORE_KEYS) if scores else None
            results[i] = {
                **data[i],
                "judge_scores": scores,
                "judge_avg_score": avg_score,
                "judge_raw_output": text,
            }
        n_done += len(batch_prompts)
        print(f"已评分 {n_done}/{len(todo_idx)}（跳过已完成 {len(done_by_id)} 条）", flush=True)
        save_results()  # 每批落盘，支持断点续跑

    save_results()
    print(f"评分结果已保存: {args.output}")

    results = load_json(args.output)
    failed = sum(1 for r in results if r["judge_scores"] is None)
    if failed:
        print(f"警告: {failed} 条输出解析失败（judge_scores 为 null，按最低分处理）")

    selected = select_top_percent(
        results, lambda r: r["judge_avg_score"], percent, seed
    )
    with open(selected_output, "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)
    print(f"前 {percent}% 共 {len(selected)} 条已保存: {selected_output}")


if __name__ == "__main__":
    main()
