import os
import sys

import fire
import torch
import json
import transformers
from peft import (
    PeftModel,
    LoraConfig,
    get_peft_model,
    get_peft_model_state_dict,
    prepare_model_for_kbit_training,
    set_peft_model_state_dict,
)
from transformers import GenerationConfig, AutoModelForCausalLM, AutoTokenizer
from typing import Dict
import json
from tqdm import tqdm
from tool import *
from datetime import datetime
import random
from collections import Counter
prompt_4shot = """Read the following text and table, and then write code to answer a question:
( in millions ) | dec 282013 | dec 292012
available-for-sale investments | $ 18086 | $ 14001
cash | 854 | 593
equity method investments | 1038 | 992
loans receivable | 1072 | 979
non-marketable cost method investments | 1270 | 1202
reverse repurchase agreements | 800 | 2850
trading assets | 8441 | 5685
total cash and investments | $ 31561 | $ 26302
Question: what percentage of total cash and investments as of dec . 29 2012 was comprised of available-for-sale investments?
```python
available_for_sale_investments_dec_29_2012 = 14001
total_cash_and_investments_dec_29_2012 = 26302
percent_available_for_sale_investments_dec_29_2012 = available_for_sale_investments_dec_29_2012 / total_cash_and_investments_dec_29_2012
ans = percent_available_for_sale_investments_dec_29_2012
```

Read the following text and table, and then write code to answer a question:
the chart shows that the firm posted market risk 2013related gains on 248 out of 261 days in this period , with 12 days exceeding $ 210 million .
december 31 ( in millions ) | 1 basis point increase in jpmorgan chase 2019s credit spread
2010 | $ 35
2009 | $ 39
Question: on what percent of trading days were there market gains above $ 210 million?
```python
days_with_market_gains_above_210_million = 12
total_trading_days = 261
percent_days_with_market_gains_above_210_million = days_with_market_gains_above_210_million / total_trading_days
ans = percent_days_with_market_gains_above_210_million
```

Read the following text and table, and then write code to answer a question:
american tower corporation and subsidiaries notes to consolidated financial statements ( 3 ) consists of customer-related intangibles of approximately $ 75.0 million and network location intangibles of approximately $ 72.7 million . the customer-related intangibles and network location intangibles are being amortized on a straight-line basis over periods of up to 20 years .
- | preliminary purchase price allocation
current assets | $ 8763
non-current assets | 2332
property and equipment | 26711
intangible assets ( 1 ) | 21079
other non-current liabilities | -1349 ( 1349 )
fair value of net assets acquired | $ 57536
goodwill ( 2 ) | 5998
Question: for acquired customer-related and network location intangibles , what is the expected annual amortization expenses , in millions?
```python
customer_related_intangibles = 75
network_location_intangibles = 72.7
straight_line_basis = 20
amortization_expenses = ( customer_related_intangibles + network_location_intangibles ) / straight_line_basis
ans = amortization_expenses
```

Read the following text and table, and then write code to answer a question:
the aggregate commitment under the liquidity asset purchase agreements was approximately $ 23.59 billion and $ 28.37 billion at december 31 , 2008 and 2007 , respectively .
( dollars in billions ) | 2008 amount | 2008 percent of total conduit assets | 2008 amount | percent of total conduit assets
united states | $ 11.09 | 46% ( 46 % ) | $ 12.14 | 42% ( 42 % )
australia | 4.30 | 17 | 6.10 | 21
great britain | 1.97 | 8 | 2.93 | 10
spain | 1.71 | 7 | 1.90 | 7
italy | 1.66 | 7 | 1.86 | 7
portugal | 0.62 | 3 | 0.70 | 2
germany | 0.57 | 3 | 0.70 | 2
netherlands | 0.40 | 2 | 0.55 | 2
belgium | 0.29 | 1 | 0.31 | 1
greece | 0.27 | 1 | 0.31 | 1
other | 1.01 | 5 | 1.26 | 5
total conduit assets | $ 23.89 | 100% ( 100 % ) | $ 28.76 | 100% ( 100 % )
Question: what is percentage change in total conduit asset from 2007 to 2008?
```python
total_conduit_assets_2007 = 28.76
total_conduit_assets_2008 = 23.89
net_change_in_total_conduit_assets = total_conduit_assets_2008 - total_conduit_assets_2007
percent_change_in_total_conduit_assets = net_change_in_total_conduit_assets / total_conduit_assets_2007
ans = percent_change_in_total_conduit_assets
```
"""
# def create_reader_request_processed(example: Dict[str, Any]):
#     prompt = 'Read the following text and table, and then write code to answer a question:\n'
#     if example['text']:
#         prompt += example['text'] + '\n'
#     prompt += example['table'].strip() + '\n'
#     prompt += 'Note: The result of the finance Problem should be stored in the \'ans\' variable.\n'
#     prompt += 'Question: {}\n'.format(example['question'])
#     #prompt += '#Python\n\n#Python:\n'
#     prompt += '#Python\n'
#     return prompt
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
    


def test_convfinqa(base_model,
                   lora_weights,
                   temperature,
                   few_shot,
                   num_return_sequences,
                   max_new_tokens,
                   dataset_path,
                   do_sample,
                   save_path
                  ):
    
    
    now = datetime.now()
    dt_string = now.strftime("%m_%d_%H_%M")
    correct, wrong = 0, 0
    filename = f'outputs/finqa_{dt_string}.json'
    use_peft = True
    load_in_8bit=False
    tokenizer = AutoTokenizer.from_pretrained(base_model)

    
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
    
    
    #if not load_in_8bit:
    #    model.half() 
    
    
    
    generation_config = GenerationConfig(
        temperature=temperature,
        top_p=0.95,
        top_k=40,
        do_sample=do_sample,
        pad_token_id = 0,
        num_return_sequences = num_return_sequences,
        #stop_strings = '\n\n'
    )
    
    with open(dataset_path) as f:
        finqa_dev = json.load(f)
    #random.shuffle(finqa_dev)    
    #jiequ
    #finqa_dev = finqa_dev[0:3]
    result = []
    for example in tqdm(finqa_dev):
        if few_shot:
            full_prompt = prompt_4shot + "\n\n"
        else:
            full_prompt = ""
        full_prompt += create_reader_request_processed_mult(example)
        print("example\n"+example['uid'])
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
        result_counter = Counter()
        codes=[]
        s = generation_output.sequences
        for si in s:
            output = tokenizer.decode(si, skip_special_tokens=True).strip()
            lq = len(full_prompt)
            print(output)
            output = output.split('```python')[1]
            output = output.split('```')[0]
            # output = output.split('#Python:\n')[-1]
            # output = output.split('\n\n')[0]
            if num_return_sequences > 1:
                output = output.replace('!','')
            codes.append(output)
        print(codes)
        #code = output.split('\n\n')[0]
        
        for r in codes:
            ans = safe_execute(r)
            ans = floatify_ans(ans)
            if ans is not None:
                result_counter.update([ans])
        
        if len(result_counter) > 0:
            prediction = result_counter.most_common(1)[0][0]
        else:
            prediction = None

        if prediction is not None:
            if type(prediction) == bool:
                if prediction:
                    prediction = 'yes'
                else:
                    prediction = 'no'
            # elif type(prediction) == list:
            #     prediction = prediction[0]
            #     if type(prediction) == bool:
            #         if prediction:
            #             prediction = 'yes'
            #         else:
            #             prediction = 'no'
            else:
                if type(prediction) not in [float, int, list]:
                    prediction = None
                    
        print("prediction")
        print(prediction)
        try:
            prediction = float(prediction)
        except:
            prediction = prediction
                # print("answer")
        # print(example["qa"]["answer"])
        res_dict = {}
        res_dict['uid'] = example['uid']
        res_dict['predicted_ans'] = prediction
        if type(prediction) == str:
            res_dict['predicted_program'] = []
        else:
            res_dict['predicted_program'] = ['add(', str(prediction), '0', ')', 'EOF']
        result.append(res_dict)
    save_dict_list_to_json(result, save_path)
    return ""
        
    
if __name__ == "__main__":
    base_model = ["Qwen/Qwen3-8B"]
    lora_weights = ["../../outputs/multihiertt/dqr_sft_rl"]
    dataset_path = ["../../data/test/multihiertt.json"]
    save_path = ["../../outputs/multihiertt_predictions.json"]
    errror_path = ['finqa_error.json']
    temperature = [0.01]
    few_shot = [False]
    do_sample = [False]
    num_return_sequences = [1]
    max_new_tokens = [1024]
    res_list = []
    for i in range(len(base_model)):
        append_with_time("开始测试", "../../outputs/multihiertt_eval.log")
        res = test_convfinqa(base_model[i],
                             lora_weights[i],
                             temperature[i],
                             few_shot[i],
                             num_return_sequences[i],
                             max_new_tokens[i],
                             dataset_path[i],
                             do_sample[i],
                             save_path[i]
                            )
        res_list.append(res)
        msg = base_model[i] + "\n"
        msg += lora_weights[i] + '\n'
        msg += dataset_path[i] + '\n'
        append_with_time(msg, "../../outputs/multihiertt_eval.log")
    print(res_list)
    print(base_model)
    print(lora_weights)
    print(dataset_path)