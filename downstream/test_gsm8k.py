import os
import sys
import re
import math

import fire
import torch
import json
import transformers
from transformers import GenerationConfig, AutoModelForCausalLM, AutoTokenizer
from typing import Dict, Any
from tqdm import tqdm
from tool import safe_execute, floatify_ans, save_dict_list_to_json  # 保留 tool 中部分工具函数
from datetime import datetime
from collections import Counter
from peft import (
    PeftModel,
    LoraConfig,
    get_peft_model,
    get_peft_model_state_dict,
    prepare_model_for_kbit_training,
    set_peft_model_state_dict,
)
# GSM8K 的 few-shot prompt（4个示例，要求模型生成 Python 代码）
prompt_4shot = """Solve the following math problem with Python code. Store the final answer in the `ans` variable. Only output the code block.

Question: A robe takes 2 bolts of blue fiber and half that much white fiber. How many bolts in total does it take?
```python
blue = 2
white = blue / 2
ans = blue + white
```

Question: Josh decides to try flipping a house. He buys a house for $80,000 and then puts in $50,000 in repairs. This increased the value of the house by 150%. How much profit did he make?
```python
cost = 80000 + 50000
new_value = cost * (1 + 150/100)
ans = new_value - cost
```

Question: James spends 40 years teaching. His partner has been teaching for 5 years less. How many years of experience do they have combined?
```python
james = 40
partner = james - 5
ans = james + partner
```

Question: A store sells apples in bags of 6 for $4. If Anna wants to buy 24 apples, how much will she pay?
```python
apples_per_bag = 6
cost_per_bag = 4
bags_needed = 24 / apples_per_bag
ans = bags_needed * cost_per_bag
```
"""

def create_reader_request_processed(example: Dict[str, Any], few_shot: bool = False) -> str:
    """
    构建 GSM8K 问题的 prompt，要求模型生成 Python 代码解决。
    如果 few_shot 为 True，则在前面添加 few-shot 示例。
    """
    prompt = ""
    if few_shot:
        prompt += prompt_4shot
    prompt += "Write Python code to solve it. Store the answer in `ans` variable.\n"
    prompt += "Question: " + example['question'] + "\n"
    prompt += "```python\n"
    return prompt


def extract_gsm8k_answer(answer_str: str):
    """
    从 GSM8K 的 answer 文本中提取最终数值答案（位于 '#### ' 之后）。
    返回 float 类型的数值，若提取失败则返回 None。
    """
    if not answer_str:
        return None
    # 按 '####' 分割，取最后一部分
    parts = answer_str.rsplit('####', 1)
    if len(parts) < 2:
        return None
    final = parts[1].strip()
    # 去除逗号，提取数字（可能是小数、整数）
    final = final.replace(",", "")
    # 使用正则找出第一个有效数字（支持负数、小数）
    match = re.search(r'-?\d+(?:\.\d+)?', final)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def gsm8k_equal(prediction, answer_str: str, tolerance: float = 1e-6) -> bool:
    """
    判断模型预测的数值答案与标准答案是否相等（容差范围内）。
    prediction: 模型输出的数值 (float/int) 或 None
    answer_str: GSM8K 中完整的 answer 字符串
    """
    if prediction is None:
        return False
    target = extract_gsm8k_answer(answer_str)
    if target is None:
        return False
    try:
        pred_num = float(prediction)
        return math.isclose(pred_num, target, rel_tol=0, abs_tol=tolerance)
    except (ValueError, TypeError):
        return False


def test_gsm8k(base_model,
               lora_weights,
               temperature,
               few_shot,
               num_return_sequences,
               max_new_tokens,
               dataset_path,
               do_sample,
               error_path):
    
    now = datetime.now()
    dt_string = now.strftime("%m_%d_%H_%M")
    correct, wrong = 0, 0
    
    use_peft = False
    load_in_8bit = False
    
    tokenizer = AutoTokenizer.from_pretrained(base_model, padding_side="left")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token  # 确保有 pad_token
    
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        load_in_8bit=load_in_8bit,
        torch_dtype=torch.float16,
        device_map="auto",
        do_sample=do_sample
    )
    
    if use_peft:
        model = PeftModel.from_pretrained(
            model,
            lora_weights,
            torch_dtype=torch.float16,
            device_map={'': 0},
            do_sample=do_sample
        )
    
    generation_config = GenerationConfig(
        temperature=temperature,
        top_p=0.95,
        top_k=40,
        do_sample=do_sample,
        pad_token_id=tokenizer.pad_token_id,
        num_return_sequences=num_return_sequences,
    )
    
    # 加载 GSM8K 数据集（jsonl 格式）
    with open(dataset_path, 'r', encoding='utf-8') as f:
        gsm8k_data = [json.loads(line) for line in f if line.strip()]
    
    error = []
    
    for example in tqdm(gsm8k_data):
        full_prompt = create_reader_request_processed(example, few_shot=few_shot)
        
        inputs = tokenizer(full_prompt, return_tensors="pt")
        input_ids = inputs["input_ids"].to("cuda")
        
        with torch.no_grad():
            generation_output = model.generate(
                input_ids=input_ids,
                generation_config=generation_config,
                return_dict_in_generate=True,
                output_scores=True,
                max_new_tokens=max_new_tokens,
                do_sample=do_sample
            )
        
        codes = []
        s = generation_output.sequences
        for si in s:
            output = tokenizer.decode(si, skip_special_tokens=True).strip()
            # 提取代码块：从 '```python' 后到 '```' 之前
            try:
                code = output.split('```python')[1].split('```')[0]
                codes.append(code)
            except IndexError:
                # 如果没有代码块，尝试用整段作为代码（极少情况）
                codes.append(output[len(full_prompt):].strip())
        
        # 执行代码提取答案
        result_counter = Counter()
        for code in codes:
            ans = safe_execute(code)
            ans = floatify_ans(ans)
            if ans is not None:
                result_counter.update([ans])
        print(codes)
        if len(result_counter) > 0:
            prediction = result_counter.most_common(1)[0][0]
        else:
            prediction = None
        
        # 处理 prediction 类型（与原始代码一致）
        if prediction is not None:
            if isinstance(prediction, bool):
                prediction = 'yes' if prediction else 'no'
            elif isinstance(prediction, list):
                prediction = prediction[0] if prediction else None
                if isinstance(prediction, bool):
                    prediction = 'yes' if prediction else 'no'
        
        # 使用 GSM8K 答案验证
        if prediction is None:
            wrong += 1
            error.append(example)
        elif gsm8k_equal(prediction, example['answer']):
            correct += 1
        else:
            wrong += 1
            error.append(example)
        
        print(f"Prediction: {prediction}")
        print(f"Answer: {example['answer']}")
        print(f"Current accuracy: {correct / (correct + wrong):.4f}")
        
        example['generated'] = codes
    
    save_dict_list_to_json(error, error_path)
    accuracy = correct / (correct + wrong)
    return accuracy


if __name__ == "__main__":
    base_model = ["../outputs/finqa_convfinqa/dqr_sft_rl_merged"]
    lora_weights = [None]
    dataset_path = ["../data/test/gsm8k.jsonl"]
    error_path = ['gsm8k_error.json']
    temperature = [0.0]
    few_shot = [False]          # 是否使用 few-shot 示例
    do_sample = [False]
    num_return_sequences = [1]
    max_new_tokens = [512]

    res_list = []
    for i in range(len(base_model)):
        res = test_gsm8k(base_model[i],
                         lora_weights[i],
                         temperature[i],
                         few_shot[i],
                         num_return_sequences[i],
                         max_new_tokens[i],
                         dataset_path[i],
                         do_sample[i],
                         error_path[i])
        res_list.append(res)
        print(f"Final accuracy: {res}")
        print(f"Model: {base_model[i]}")
        print(f"LoRA weights: {lora_weights[i]}")