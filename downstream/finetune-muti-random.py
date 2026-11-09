import os
import sys
from typing import List
import re

import torch
import transformers
from datasets import load_dataset
import json
from tqdm import tqdm
import math
import random
from tool import *
os.environ["WANDB_DISABLED"] = "true"
"""
Unused imports:
import torch.nn as nn
import bitsandbytes as bnb
"""
from typing import Union, Dict, Any
def is_valid_json(json_input):
    try:
        json_input = json_input["response"]["answer"]
    except:
        return False
    if isinstance(json_input, str):
        try:
            data = json.loads(json_input)
        except json.JSONDecodeError:
            return False
    elif isinstance(json_input, dict):
        data = json_input
    else:
        return False

    counts = {
        "correctness": 0,
        "relevance": 0,
        "clarity": 0,
        "quality": 0
    }

    for key, value in data.items():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if 0.0 <= float(value) <= 10.0:
                key_lower = key.lower()
                if "correctness" in key_lower:
                    counts["correctness"] += 1
                elif "relevance" in key_lower:
                    counts["relevance"] += 1
                elif "clarity" in key_lower:
                    counts["clarity"] += 1
                elif "quality" in key_lower:
                    counts["quality"] += 1

    return (counts["correctness"] >= 1 and 
            counts["relevance"] >= 1 and 
            counts["clarity"] >= 1 and 
            counts["quality"] >= 2)
def compute_final_score(
    item,
    default_score = -1.0,
    weights = None
) -> float:
    """
    从 JSON 字符串中提取五个评分字段，计算加权总分。

    参数:
        json_str: JSON 字符串，应包含五个字段，字段名需分别包含关键词
                  'correctness', 'relevance', 'clarity', 以及两个 'quality'。
        default_score: 当某个关键词对应的字段缺失时使用的默认分数，取值范围 [0,10]。
        weights: 五个分数对应的权重列表，顺序为 [correctness, relevance, clarity, quality1, quality2]，
                 默认均为 0.2。

    返回:
        加权总分（浮点数）。如果 JSON 解析失败或值不合法，抛出异常。
    """
    try:
        data = item["response"]["answer"]
    except:
        return default_score
    print(data)
    if not isinstance(data, dict):
        return default_score

    # 初始化权重
    if weights is None:
        weights = [0.2, 0.2, 0.2, 0.2, 0.2]
    if len(weights) != 5:
        return default_score

    # 准备存放分数的变量
    correctness = None
    relevance = None
    clarity = None
    quality_scores = []  # 收集所有包含 quality 的字段值

    # 遍历所有键值对
    for key, value in data.items():
        key_lower = key.lower()

        # 检查值是否为数字且在 [0,10] 内
        if not isinstance(value, (int, float)):
            value = default_score
        if value < 0.0 or value > 10.0:
            value = default_score

        # 根据关键词匹配
        if "correctness" in key_lower and correctness is None:
            correctness = value
        if "relevance" in key_lower and relevance is None:
            relevance = value
        if "clarity" in key_lower and clarity is None:
            clarity = value
        if "quality" in key_lower:
            quality_scores.append(value)

    # 如果某个关键词未匹配到，使用默认值
    if correctness is None:
        correctness = default_score
    if relevance is None:
        relevance = default_score
    if clarity is None:
        clarity = default_score

    # 处理 quality 字段：至少取前两个，不足则用默认值补齐
    # 如果多于两个，只取前两个（按遍历顺序）
    quality1 = quality_scores[0] if len(quality_scores) > 0 else default_score
    quality2 = quality_scores[1] if len(quality_scores) > 1 else default_score

    # 收集五个分数
    scores = [correctness, relevance, clarity, quality1, quality2]

    # 计算加权和
    total = sum(s * w for s, w in zip(scores, weights))
    print(total)
    print("_________________________")
    return total

#def safe_get_score(item, default_value=float('-inf')):
def safe_get_score(item, default_value=float(10)):
    """安全地获取分数，如果键不存在或值不是数字，则返回一个默认值。"""
    if not isinstance(item, dict):
        return default_value
    response = item.get('response')
    score = response.get('answer')
    if isinstance(score, (int, float)):
        return score
    else:
        try:
            return float(score)
        except:
            return default_value
    return default_value

import math
import random

def robust_filter_lowest_by_proportion(data_list: list, proportion_to_remove: float) -> list:
    """
    按比例过滤 'avg_score' 最低的数据（鲁棒版）。
    - 严格保证移除的数量符合百分比要求。
    - 当遇到临界分数有大量重复数据时，随机移除其中的一部分。
    - 缺少 'avg_score' 或非数值的项被视为最低分，优先被移除。
    """
    if not data_list or proportion_to_remove <= 0:
        return data_list[:]
    if proportion_to_remove >= 1.0:
        return []

    total_items = len(data_list)
    
    # 计算严格需要移除的数量 (向上取整，保证至少移除这么多)
    num_to_remove = math.ceil(total_items * proportion_to_remove)
    
    if num_to_remove >= total_items:
        return []

    # --- 核心修改开始 ---
    
    # 构建一个临时列表，包含 (分数, 随机数, 原始数据)
    # 引入 random.random() 作为第二排序键：
    # 当分数不同时，按分数排序；当分数相同时，按随机数排序（相当于随机打乱）
    decorated_data = []
    w_num1 = 0
    w_num2 = 0
    for item in data_list:
        score = compute_final_score(item)
        if score < 0:
            w_num1 += 1
        if is_valid_json(item) == False:
            w_num2 += 1
        decorated_data.append((score, random.random(), item))
    print("错误数量1",w_num1)
    print("错误数量2",w_num2)
    
    # 执行排序
    # Python 的 sort 是稳定的，但这里我们显式加入了随机键，保证了同分数的随机性
    decorated_data.sort(key=lambda x: (x[0], x[1]))
    
    # 直接根据数量进行切片：保留从 num_to_remove 开始到最后的所有数据
    # 这种方法严格控制了保留的数量，不受分数重复的影响
    kept_decorated = decorated_data[num_to_remove:]
    
    # 还原回原始数据列表
    filtered_list = [x[2] for x in kept_decorated]
    
    # --- 核心修改结束 ---

    # 获取分界处的调试信息
    # 最后一个被移除的数据（在排序后的列表中索引为 num_to_remove - 1）
    cutoff_item = decorated_data[num_to_remove - 1]
    threshold_score = cutoff_item[0]

    print(f"总数据量: {total_items}, 计划移除比例: {proportion_to_remove:.2%}")
    print(f"计划移除数量: {num_to_remove}, 临界分数: {threshold_score}")
    print(f"实际移除数量: {total_items - len(filtered_list)}, 最终保留数量: {len(filtered_list)}")
    
    return filtered_list
def calculate_average_answer(data_point: dict) -> float:
    """
    计算 JSON 对象中 'response' 列表下所有 'answer' 值的平均值。

    该函数会稳健地处理以下情况：
    - 'answer' 的值为 None 时会跳过。
    - 'answer' 的值为字符串时，会尝试将其转换为浮点数，转换失败则跳过。
    - 'answer' 的值为整数或浮点数时，直接使用。
    - 'response' 列表中的元素如果不是字典或没有 'answer' 键，则会安全地跳过。
    - 如果没有找到任何有效的数值，则返回 0.0。

    :param data_point: 包含 'response' 列表的字典。
    :return: 所有有效 'answer' 值的平均值，类型为 float。
    """
    # 检查 'response' 键是否存在且其值是否为列表
    if not isinstance(data_point.get("scores"), list):
        print("警告: 'data_point' 中没有找到 'scores' 列表，或其不是一个列表。返回 0.0")
        return 0.0

    valid_numbers = []
    
    # 遍历 response 列表中的每一个元素
    for item in data_point["scores"]:
        
            
        answer = item # 使用 .get() 避免 KeyError

        # 1. 跳过 None 值
        if answer is None:
            continue

        # 2. 尝试将值转换为 float
        try:
            # float() 函数可以智能地处理 int, float, 和数字字符串
            numeric_value = float(answer)
            valid_numbers.append(numeric_value)
        except (ValueError, TypeError):
            # ValueError: 字符串无法转换为数字 (例如 "hello")
            # TypeError: answer 是不支持转换的类型 (例如列表或字典)
            print(f"信息: 值 '{answer}' (类型: {type(answer).__name__}) 无法转换为数字，已跳过。")
            continue

    # 3. 计算平均值
    if not valid_numbers:
        print("信息: 没有找到任何有效的数值来计算平均值。返回 0.0")
        return 0.0
    else:
        average = sum(valid_numbers) / len(valid_numbers)
        return average
        
class Prompter(object):
    
    def generate_prompt(
        self,
        instruction: str,
        label: Union[None, str] = None,
    ) -> str:     

        res = f"{instruction}"
               
        if label:
            res = f"{res}{label}"
         
        return res


    def get_response(self, output: str) -> str:
        return output.split("#Python:\n")[1].strip().replace("/", "\u00F7").replace("*", "\u00D7")
        # return output
def convert_html_tables_to_markdown(data_instance):
    """
    输入数据字典，提取其中的 HTML 表格并将其转化为 Markdown 格式。
    返回包含 Markdown 表格字符串的列表。
    """
    html_tables = data_instance.get("tables", [])
    markdown_tables = []

    for html_table in html_tables:
        # 匹配所有的 <tr> 行
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html_table, re.IGNORECASE | re.DOTALL)

        parsed_rows = []
        max_cols = 0

        for row in rows:
            # 匹配 <td> 或 <th> 单元格，提取属性和内容
            cells = re.findall(r'<t[dh]([^>]*)>(.*?)</t[dh]>', row, re.IGNORECASE | re.DOTALL)

            row_data = []
            for attr, content in cells:
                # 移除单元格内部的 HTML 标签 (例如 <i>, <b>)
                clean_content = re.sub(r'<[^>]+>', '', content).strip()
                # 替换换行符，防止破坏 Markdown 表格结构
                clean_content = clean_content.replace('\n', ' ').replace('\r', '')

                row_data.append(clean_content)

                # 处理 colspan 属性 (Markdown 不原生支持 colspan，通过补充空单元格对齐)
                colspan_match = re.search(r'colspan=["\']?(\d+)["\']?', attr, re.IGNORECASE)
                if colspan_match:
                    colspan = int(colspan_match.group(1))
                    # 为合并的列填充空字符串
                    row_data.extend([''] * (colspan - 1))

            parsed_rows.append(row_data)
            max_cols = max(max_cols, len(row_data))

        # 构建 Markdown 字符串
        if not parsed_rows:
            markdown_tables.append("")
            continue

        md_lines = []
        for i, row_data in enumerate(parsed_rows):
            # 补齐长度不足的行，确保表格列数一致
            padded_row = row_data + [''] * (max_cols - len(row_data))
            md_line = "| " + " | ".join(padded_row) + " |"
            md_lines.append(md_line)

            # 在第一行之后插入 Markdown 表格的分隔线
            if i == 0:
                separator = "|" + "|".join(["---"] * max_cols) + "|"
                md_lines.append(separator)

        markdown_tables.append("\n".join(md_lines))

    return markdown_tables

        
class Prompter(object):
    
    def generate_prompt(
        self,
        instruction: str,
        label: Union[None, str] = None,
    ) -> str:     

        res = f"{instruction}"
               
        if label:
            res = f"{res}{label}"
         
        return res


    def get_response(self, output: str) -> str:
        return output.split("#Python:\n")[1].strip().replace("/", "\u00F7").replace("*", "\u00D7")
        # return output
        
from peft import (
    LoraConfig,
    get_peft_model,
    get_peft_model_state_dict,
    prepare_model_for_kbit_training,
    set_peft_model_state_dict,
    load_peft_weights,
    PeftModel,
)
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

def create_reader_request_processed_mult(example: Dict[str, Any]):
    qa = example.get('qa', 'N/A')
    question = qa.get('question', 'N/A')
    paragraphs = "\n".join(example.get("paragraphs", []))
    tables = convert_html_tables_to_markdown(example)
    table = "\n".join(tables)
    
    prompt = 'Read the following text and tables, and then write code to answer a question:\n'
    prompt += 'Please store the result of the question in the \'ans\' variable.\n'
    prompt += paragraphs + '\n\n'
    prompt += table + '\n\n'
    prompt += 'Question: {}\n'.format(question)
    prompt += '```python\n'
    return prompt



def train(
    # model/data params
    base_model: str = "Qwen/Qwen3-8B",
    data_path: str = "../data/multihiertt/gemini.json",
    output_dir: str = "../outputs/multihiertt/random",
    
    # training hyperparams
    batch_size: int = 48,
    micro_batch_size: int = 1,
    num_epochs: int = 3,
    learning_rate: float = 3e-4,
    cutoff_len: int = 4096,
    val_set_size: int = 0, # we don't need val in our case.

    use_g2: bool = False,

    use_judge: float = 0.00,

    
    # lora hyperparams
    lora_r: int = 64,
    lora_alpha: int = 128,
    lora_dropout: float = 0.05,
    lora_target_modules: List[str] = [
        "q_proj",
        "v_proj",
        "k_proj",
        "o_proj",
    ],
    
    # llm hyperparams
    train_on_inputs: bool = False,  # if False, masks out inputs in loss
    group_by_length: bool = False,  # faster, but produces an odd training loss curve

    
    resume_from_checkpoint = None
    
):
    if int(os.environ.get("LOCAL_RANK", 0)) == 0:
        print(
            f"Training Alpaca-LoRA model with params:\n"
            f"base_model: {base_model}\n"
            f"data_path: {data_path}\n"
            f"output_dir: {output_dir}\n"
            f"batch_size: {batch_size}\n"
            f"micro_batch_size: {micro_batch_size}\n"
            f"num_epochs: {num_epochs}\n"
            f"learning_rate: {learning_rate}\n"
            f"cutoff_len: {cutoff_len}\n"
            f"val_set_size: {val_set_size}\n"
            f"lora_r: {lora_r}\n"
            f"lora_alpha: {lora_alpha}\n"
            f"lora_dropout: {lora_dropout}\n"
            f"lora_target_modules: {lora_target_modules}\n"
            f"train_on_inputs: {train_on_inputs}\n"
            f"group_by_length: {group_by_length}\n"
            f"resume_from_checkpoint: {resume_from_checkpoint or False}\n"
        )
    assert (
        base_model
    ), "Please specify a --base_model, e.g. --base_model='decapoda-research/llama-7b-hf'"
    gradient_accumulation_steps = batch_size // micro_batch_size

    prompter = Prompter()


    world_size = int(os.environ.get("WORLD_SIZE", 1))
    ddp = world_size != 1


    device_map = {"": int(os.environ.get("LOCAL_RANK", 0))}
    gradient_accumulation_steps = gradient_accumulation_steps // world_size
    print(device_map)
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        load_in_8bit=True,
        torch_dtype=torch.float16,
        device_map=device_map,
    )

    tokenizer = AutoTokenizer.from_pretrained(base_model)

    tokenizer.pad_token_id = 0
    
    tokenizer.padding_side = "left"  # Allow batched inference

    def tokenize(prompt, add_eos_token=True):
        result = tokenizer(
            prompt,
            truncation=True,
            max_length=cutoff_len,
            padding=False,
            return_tensors=None,
        )
        if (
            result["input_ids"][-1] != tokenizer.eos_token_id
            and len(result["input_ids"]) < cutoff_len
            and add_eos_token
        ):
            result["input_ids"].append(tokenizer.eos_token_id)
            result["attention_mask"].append(1)

        result["labels"] = result["input_ids"].copy()

        return result

    def generate_and_tokenize_prompt(data_point):

        ins = create_reader_request_processed_mult(data_point)
        code = data_point["code"]
        if '\nunits = ' in code:
            code = code.replace('\nunits = ', '\nscale = ')
            print(code)
        full_prompt = prompter.generate_prompt(
            ins,
            code,
        )
        tokenized_full_prompt = tokenize(full_prompt)
        if not train_on_inputs:
            user_prompt = prompter.generate_prompt(
                ins
            )
            tokenized_user_prompt = tokenize(user_prompt, add_eos_token=False)
            user_prompt_len = len(tokenized_user_prompt["input_ids"])

            tokenized_full_prompt["labels"] = [
                -100
            ] * user_prompt_len + tokenized_full_prompt["labels"][
                user_prompt_len:
            ]  # could be sped up, probably
        return tokenized_full_prompt

    model = prepare_model_for_kbit_training(model)
    if resume_from_checkpoint:
        model.enable_input_require_grads()
        model = PeftModel.from_pretrained(model, resume_from_checkpoint, is_trainable=True)
        #model._mark_only_adapters_as_trainable()
    else:
        config = LoraConfig(
            r=lora_r,
            lora_alpha=lora_alpha,
            target_modules=lora_target_modules,
            lora_dropout=lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, config)

    
    model.print_trainable_parameters()  # Be more transparent about the % of trainable params.
    

    with open(data_path) as f:
        finqa_train = json.load(f)
    train_data_tmp = []
    train_data = []
    for data_point in tqdm(finqa_train):
        example = generate_and_tokenize_prompt(data_point)
        train_data.append(example) 
    random.shuffle(train_data)
    number = (1.0 - use_judge) * len(train_data)
    train_data = train_data[0:int(number)]
    
    val_data = None
    
    #random.shuffle(train_data)
    
    val_data = None

    if not ddp and torch.cuda.device_count() > 1:
        # keeps Trainer from trying its own DataParallelism when more than 1 gpu is available
        model.is_parallelizable = True
        model.model_parallel = True

    trainer = transformers.Trainer(
        model=model,
        train_dataset=train_data,
        eval_dataset=val_data,
        args=transformers.TrainingArguments(
            per_device_train_batch_size=micro_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            warmup_steps=100,
            num_train_epochs=num_epochs,
            learning_rate=learning_rate,
            fp16=True,
            logging_steps=10,
            optim="adamw_torch",
            save_strategy="steps",
            eval_steps=200 if val_set_size > 0 else None,
            save_steps=1000,
            output_dir=output_dir,
            save_total_limit=1,
            load_best_model_at_end=False if val_set_size > 0 else False,
            ddp_find_unused_parameters=False,
            #group_by_length=group_by_length,
        ),
        data_collator=transformers.DataCollatorForSeq2Seq(
            tokenizer, pad_to_multiple_of=8, return_tensors="pt", padding=True
        ),
    )
    model.config.use_cache = False

    old_state_dict = model.state_dict


    trainer.train(resume_from_checkpoint=resume_from_checkpoint)
    #trainer.train()
    model.save_pretrained(output_dir)

    print(
        "\n If there's a warning about missing keys above, please disregard :)"
    )


if __name__ == "__main__":
    train()