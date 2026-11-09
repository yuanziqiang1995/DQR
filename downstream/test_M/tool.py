question = """
Please read the following text and table, and write code to answer the questions based on the calculation process:
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
#Python
available_for_sale_investments_dec_29_2012 = 14001
total_cash_and_investments_dec_29_2012 = 26302
percent_available_for_sale_investments_dec_29_2012 = available_for_sale_investments_dec_29_2012 / total_cash_and_investments_dec_29_2012
ans = percent_available_for_sale_investments_dec_29_2012


Please read the following text and table, and write code to answer the questions based on the calculation process:
the chart shows that the firm posted market risk 2013related gains on 248 out of 261 days in this period , with 12 days exceeding $ 210 million .
december 31 ( in millions ) | 1 basis point increase in jpmorgan chase 2019s credit spread
2010 | $ 35
2009 | $ 39
Question: on what percent of trading days were there market gains above $ 210 million?
#Python
days_with_market_gains_above_210_million = 12
total_trading_days = 261
percent_days_with_market_gains_above_210_million = days_with_market_gains_above_210_million / total_trading_days
ans = percent_days_with_market_gains_above_210_million


Please read the following text and table, and write code to answer the questions based on the calculation process:
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
#Python
customer_related_intangibles = 75
network_location_intangibles = 72.7
straight_line_basis = 20
amortization_expenses = ( customer_related_intangibles + network_location_intangibles ) / straight_line_basis
ans = amortization_expenses


Please read the following text and table, and write code to answer the questions based on the calculation process:
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
#Python
total_conduit_assets_2007 = 28.76
total_conduit_assets_2008 = 23.89
net_change_in_total_conduit_assets = total_conduit_assets_2008 - total_conduit_assets_2007
percent_change_in_total_conduit_assets = net_change_in_total_conduit_assets / total_conduit_assets_2007
ans = percent_change_in_total_conduit_assets


Read the following text and table, and then write code to answer a question:
entergy corporation and subsidiaries management 2019s financial discussion and analysis a result of the entergy louisiana and entergy gulf states louisiana business combination , results of operations for 2015 also include two items that occurred in october 2015 : 1 ) a deferred tax asset and resulting net increase in tax basis of approximately $ 334 million and 2 ) a regulatory liability of $ 107 million ( $ 66 million net-of-tax ) as a result of customer credits to be realized by electric customers of entergy louisiana , consistent with the terms of the stipulated settlement in the business combination proceeding . see note 2 to the financial statements for further discussion of the business combination and customer credits . results of operations for 2015 also include the sale in december 2015 of the 583 mw rhode island state energy center for a realized gain of $ 154 million ( $ 100 million net-of-tax ) on the sale and the $ 77 million ( $ 47 million net-of-tax ) write-off and regulatory charges to recognize that a portion of the assets associated with the waterford 3 replacement steam generator project is no longer probable of recovery . see note 14 to the financial statements for further discussion of the rhode island state energy center sale . see note 2 to the financial statements for further discussion of the waterford 3 write-off . results of operations for 2014 include $ 154 million ( $ 100 million net-of-tax ) of charges related to vermont yankee primarily resulting from the effects of an updated decommissioning cost study completed in the third quarter 2014 along with reassessment of the assumptions regarding the timing of decommissioning cash flows and severance and employee retention costs . see note 14 to the financial statements for further discussion of the charges . results of operations for 2014 also include the $ 56.2 million ( $ 36.7 million net-of-tax ) write-off in 2014 of entergy mississippi 2019s regulatory asset associated with new nuclear generation development costs as a result of a joint stipulation entered into with the mississippi public utilities staff , subsequently approved by the mpsc , in which entergy mississippi agreed not to pursue recovery of the costs deferred by an mpsc order in the new nuclear generation docket . see note 2 to the financial statements for further discussion of the new nuclear generation development costs and the joint stipulation . net revenue utility following is an analysis of the change in net revenue comparing 2015 to 2014 . amount ( in millions ) . the retail electric price variance is primarily due to : 2022 formula rate plan increases at entergy louisiana , as approved by the lpsc , effective december 2014 and january 2015 ; 2022 an increase in energy efficiency rider revenue primarily due to increases in the energy efficiency rider at entergy arkansas , as approved by the apsc , effective july 2015 and july 2014 , and new energy efficiency riders at entergy louisiana and entergy mississippi that began in the fourth quarter 2014 ; and 2022 an annual net rate increase at entergy mississippi of $ 16 million , effective february 2015 , as a result of the mpsc order in the june 2014 rate case . see note 2 to the financial statements for a discussion of rate and regulatory proceedings. .
- | amount ( in millions )
2014 net revenue | $ 5735
retail electric price | 187
volume/weather | 95
waterford 3 replacement steam generator provision | -32 ( 32 )
miso deferral | -35 ( 35 )
louisiana business combination customer credits | -107 ( 107 )
other | -14 ( 14 )
2015 net revenue | $ 5829
Question: what is the net change in net revenue during 2015 for entergy corporation?
#Python
"""

example = """
Please read the following text and table, and write code to answer the questions based on the calculation process:
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
#Python
available_for_sale_investments_dec_29_2012 = 14001
total_cash_and_investments_dec_29_2012 = 26302
percent_available_for_sale_investments_dec_29_2012 = available_for_sale_investments_dec_29_2012 / total_cash_and_investments_dec_29_2012
ans = percent_available_for_sale_investments_dec_29_2012


Please read the following text and table, and write code to answer the questions based on the calculation process:
the chart shows that the firm posted market risk 2013related gains on 248 out of 261 days in this period , with 12 days exceeding $ 210 million .
december 31 ( in millions ) | 1 basis point increase in jpmorgan chase 2019s credit spread
2010 | $ 35
2009 | $ 39
Question: on what percent of trading days were there market gains above $ 210 million?
#Python
days_with_market_gains_above_210_million = 12
total_trading_days = 261
percent_days_with_market_gains_above_210_million = days_with_market_gains_above_210_million / total_trading_days
ans = percent_days_with_market_gains_above_210_million


Please read the following text and table, and write code to answer the questions based on the calculation process:
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
#Python
customer_related_intangibles = 75
network_location_intangibles = 72.7
straight_line_basis = 20
amortization_expenses = ( customer_related_intangibles + network_location_intangibles ) / straight_line_basis
ans = amortization_expenses


Please read the following text and table, and write code to answer the questions based on the calculation process:
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
#Python
total_conduit_assets_2007 = 28.76
total_conduit_assets_2008 = 23.89
net_change_in_total_conduit_assets = total_conduit_assets_2008 - total_conduit_assets_2007
percent_change_in_total_conduit_assets = net_change_in_total_conduit_assets / total_conduit_assets_2007
ans = percent_change_in_total_conduit_assets


Read the following text and table, and then write code to answer a question:
entergy corporation and subsidiaries management 2019s financial discussion and analysis a result of the entergy louisiana and entergy gulf states louisiana business combination , results of operations for 2015 also include two items that occurred in october 2015 : 1 ) a deferred tax asset and resulting net increase in tax basis of approximately $ 334 million and 2 ) a regulatory liability of $ 107 million ( $ 66 million net-of-tax ) as a result of customer credits to be realized by electric customers of entergy louisiana , consistent with the terms of the stipulated settlement in the business combination proceeding . see note 2 to the financial statements for further discussion of the business combination and customer credits . results of operations for 2015 also include the sale in december 2015 of the 583 mw rhode island state energy center for a realized gain of $ 154 million ( $ 100 million net-of-tax ) on the sale and the $ 77 million ( $ 47 million net-of-tax ) write-off and regulatory charges to recognize that a portion of the assets associated with the waterford 3 replacement steam generator project is no longer probable of recovery . see note 14 to the financial statements for further discussion of the rhode island state energy center sale . see note 2 to the financial statements for further discussion of the waterford 3 write-off . results of operations for 2014 include $ 154 million ( $ 100 million net-of-tax ) of charges related to vermont yankee primarily resulting from the effects of an updated decommissioning cost study completed in the third quarter 2014 along with reassessment of the assumptions regarding the timing of decommissioning cash flows and severance and employee retention costs . see note 14 to the financial statements for further discussion of the charges . results of operations for 2014 also include the $ 56.2 million ( $ 36.7 million net-of-tax ) write-off in 2014 of entergy mississippi 2019s regulatory asset associated with new nuclear generation development costs as a result of a joint stipulation entered into with the mississippi public utilities staff , subsequently approved by the mpsc , in which entergy mississippi agreed not to pursue recovery of the costs deferred by an mpsc order in the new nuclear generation docket . see note 2 to the financial statements for further discussion of the new nuclear generation development costs and the joint stipulation . net revenue utility following is an analysis of the change in net revenue comparing 2015 to 2014 . amount ( in millions ) . the retail electric price variance is primarily due to : 2022 formula rate plan increases at entergy louisiana , as approved by the lpsc , effective december 2014 and january 2015 ; 2022 an increase in energy efficiency rider revenue primarily due to increases in the energy efficiency rider at entergy arkansas , as approved by the apsc , effective july 2015 and july 2014 , and new energy efficiency riders at entergy louisiana and entergy mississippi that began in the fourth quarter 2014 ; and 2022 an annual net rate increase at entergy mississippi of $ 16 million , effective february 2015 , as a result of the mpsc order in the june 2014 rate case . see note 2 to the financial statements for a discussion of rate and regulatory proceedings. .
- | amount ( in millions )
2014 net revenue | $ 5735
retail electric price | 187
volume/weather | 95
waterford 3 replacement steam generator provision | -32 ( 32 )
miso deferral | -35 ( 35 )
louisiana business combination customer credits | -107 ( 107 )
other | -14 ( 14 )
2015 net revenue | $ 5829
Question: what is the net change in net revenue during 2015 for entergy corporation?
#Python
net_revenue_2014 = 5735
net_revenue_2015 = 5829
net_change_in_net_revenue = net_revenue_2015 - net_revenue_2014
ans = net_change_in_net_revenue


Please read the following text and table, and write code to answer the questions based on the calculation process:
the following table presents the components of the change in net revenue for the years ended december 31, 2014 and 2015 ( in millions ) :
2014 | 2015
retail electric price variance | $ 187 | $ 95
volume/weather | ( 95 ) | ( 105 )
waterford 3 replacement steam generator provision | -32 | -35
miso deferral | -35 | -35
louisiana business combination customer credits | -107 | -107
other | -14 | -14
total net revenue change | $ 5735 | $ 5829
Question: what is the total net revenue change for entergy corporation from 2014 to 2015?
#Python
net_revenue_2014 = 5735
net_revenue_2015 = 5829
total_net_revenue_change = net_revenue_2015 - net_revenue_2014
ans = total_net_revenue_change


Please read the following text and table, and write code to answer the questions based on the calculation process:
the following table presents the components of the change in net revenue for the years ended december 31, 2014 and 2015 ( in millions ) :
2014 | 2015
retail electric price variance | $ 187 | $ 95
volume/weather | ( 95 ) | ( 105 )
waterford 3 replacement steam generator provision | -32 | -35
miso deferral | -35 | -35
louisiana
"""

    
from typing import Union, Any
from math import isclose
import func_timeout
from sympy.solvers import solve
from sympy import Symbol, Eq
import math
from sympy import simplify
import numpy as np
import cvxpy as cp
import statistics
import json
import re
from pathlib import Path
import os
import datetime

def append_with_time(info: str, file_path: str) -> None:
    """
    在指定文件末尾追加写入内容，并标注当前时间。

    参数:
        info: 要写入的文本信息。
        file_path: 目标文件的路径（若文件不存在会自动创建）。
    """
    # 获取当前时间，格式可自定义，例如 "2026-05-05 14:30:00"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 组合带时间标记的写入内容
    content = f"[{timestamp}] {info}\n"

    # 以追加模式打开文件，编码使用utf-8保证中文正常写入
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(content)
def get_precision(gt_ans: float) -> int:
    precision = 5
    if '.' in str(gt_ans):
        precision = len(str(gt_ans).split('.')[-1])
    return precision


def finqa_equal(prediction: Union[bool, float, str],
                reference: Union[float, str],
                include_percentage: bool = False,
                is_close: float = False) -> bool:
    if prediction is None:
        return False
    elif type(prediction) == bool:
        # bool questions
        if prediction:
            return reference == 'yes'
        else:
            return reference == 'no'
    elif type(reference) == str or type(prediction) == str:
        # string questions
        return prediction == reference
    else:
        # number questions
        if include_percentage:
            gt_result = [reference / 100, reference, reference * 100]
        else:
            gt_result = [reference]
        for item in gt_result:
            try:
                if is_close:
                    if isclose(item, prediction, rel_tol=0.001):
                        return True
                precision = min(get_precision(prediction), get_precision(item))
                if round(prediction, precision) == round(item, precision):
                    return True
            except Exception:
                continue
        return False

def parse_api_result(result, question):
    lq = len(question)
    result = result[lq:]
    #print(result)
    result_list = result.split('\n\n')
    code = result_list[0]
    return code

def simplify_ans(ans, convert_to_str: bool = True):
    if 'relational' in str(type(ans)):
        return str(ans)
    elif 'numpy' in str(type(ans)):
        if ans.shape == ():
            # scalar value
            ans = round(float(ans), 2)
        else:
            # array value
            ans = round(float(ans[0]), 2)
        if convert_to_str:
            return str(ans)
        else:
            return ans
    elif not ans:
        return None
    else:
        if type(ans) in [list, tuple]:
            if 'sympy' in str(type(ans[0])):
                try:
                    ans = [round(float(x), 2) for x in ans]
                except Exception:
                    ans = [str(x) for x in ans]
            if len(ans) == 1:
                ans = ans[0]
        else:
            if 'sympy' in str(type(ans)):
                try:
                    ans = round(float(ans), 2)
                except Exception:
                    ans = str(ans)
        if convert_to_str:
            return str(ans)
        else:
            return ans


def floatify_ans(ans):
    if ans is None:
        return None
    elif type(ans) == dict:
        ans = list(ans.values())[0]
    elif type(ans) == bool:
        ans = ans
    elif type(ans) in [list, tuple]:
        if not ans:
            return None
        else:
            try:
                ans = float(ans[0])
            except Exception:
                ans = str(ans[0])
    else:
        try:
            ans = float(ans)
        except Exception:
            ans = str(ans)
    return ans



def solve_it(equation, variable):
    solution = solve(equation, variable, dict=True)
    if not solution:
        if isinstance(variable, list):
            solution = {v: None for v in variable}
        else:
            solution = {variable: None}
        return solution
    else:
        solution = solution[0]
        return solution


def safe_execute(code_string: str, keys=None):
    def execute(x):
        try:
            exec(x)
            locals_ = locals()
            if keys is None:
                return locals_.get('ans', None)
            else:
                return [locals_.get(k, None) for k in keys]
        except Exception:
            return None
    try:
        ans = func_timeout.func_timeout(5, execute, args=(code_string,))
    except func_timeout.FunctionTimedOut:
        ans = None

    return ans


def synthesize_program(result: str, prefix: str) -> str:
    program = prefix
    for i, line in enumerate(result.split('\n')):
        if i == 0:
            program += line + '\n'
        else:
            if line.startswith('    '):
                program += line + '\n'
            else:
                break
    program += 'ans = solver()'    
    return program

def save_dict_list_to_json(dict_list, file_name):
    """
    将字典列表保存为JSON文件

    参数:
    dict_list (list): 字典列表
    file_name (str): 要保存的文件名

    返回:
    bool: True表示保存成功，False表示保存失败
    """
    try:
        # 将字典列表转换为JSON格式的字符串
        json_string = json.dumps(dict_list, indent=4)
        # 将JSON字符串写入文件
        with open(file_name, 'w') as file:
            file.write(json_string)
        return True
    except Exception as e:
        print(f"保存JSON文件时出错: {e}")
        return False

def list_to_markdown(data):
    """
    将二维列表转换为 Markdown 表格格式。
    假设第一行为表头。
    """
    if not data:
        return ""

    # 1. 将所有数据转换为字符串，并处理单元格内可能存在的 '|' 符号
    formatted_data = [
        [str(cell).replace("|", "\\|") for cell in row]
        for row in data
    ]

    # 2. 提取表头和数据行
    headers = formatted_data[0]
    rows = formatted_data[1:]

    # 3. 构建分隔行 (例如: |---|---|)
    # 使用 :--- 表示左对齐，这是最通用的格式
    separator = ["---"] * len(headers)

    # 4. 格式化每一行
    def format_row(row_items):
        return "| " + " | ".join(row_items) + " |"

    markdown_lines = []

    # 添加表头
    markdown_lines.append(format_row(headers))
    # 添加分隔线
    markdown_lines.append(format_row(separator))
    # 添加数据行
    for row in rows:
        markdown_lines.append(format_row(row))

    return "\n".join(markdown_lines)
#parse_api_result(example,question)

def extract_numbers_dsl(text):
    """
    从字符串中提取所有数字。
    1. 支持正数、负数、浮点数。
    2. 排除前一个字符是下划线 '_' 的数字。
    """

    # 正则表达式解释：
    # (?<!_)       : 否定回顾 (Negative Lookbehind) - 确保匹配项的前一个字符不是 '_'
    # (?<!#)       : 否定回顾 (Negative Lookbehind) - 确保匹配项的前一个字符不是 '#'
    # (?<!m)       : 否定回顾 (Negative Lookbehind) - 确保匹配项的前一个字符不是 'm'
    # (?<!\d)      : 否定回顾 - 确保匹配项的前一个字符不是数字 (防止匹配到 "_123" 中的 "23")
    # (?<!\d\.)    : 否定回顾 - 确保前一个字符不是 "数字." (防止匹配小数的后半部分)
    # [-+]?        : 可选的正号或负号
    # \d+          : 一个或多个数字
    # (?:\.\d+)?   : 非捕获组，可选的小数部分 (例如 .123)

    pattern = r'(?<!m)(?<!#)(?<!_)(?<!\d)(?<!\d\.)[-+]?\d+(?:\.\d+)?'

    # 使用 findall 查找所有匹配项
    numbers = re.findall(pattern, text)

    # 将结果转换为数字类型 (float 或 int) 以便后续使用，如果只需要字符串可省略此步
    result = []
    for num_str in numbers:
        if '.' in num_str:
            result.append(float(num_str))
        else:
            result.append(int(num_str))

    return result
def extract_numbers_code(text):
    """
    从字符串中提取所有数字。
    1. 支持正数、负数、浮点数。
    2. 排除前一个字符是下划线 '_' 的数字。
    """

    # 正则表达式解释：
    # (?<!_)       : 否定回顾 (Negative Lookbehind) - 确保匹配项的前一个字符不是 '_'
    # (?<!#)       : 否定回顾 (Negative Lookbehind) - 确保匹配项的前一个字符不是 '#'
    # (?<!\d)      : 否定回顾 - 确保匹配项的前一个字符不是数字 (防止匹配到 "_123" 中的 "23")
    # (?<!\d\.)    : 否定回顾 - 确保前一个字符不是 "数字." (防止匹配小数的后半部分)
    # [-+]?        : 可选的正号或负号
    # \d+          : 一个或多个数字
    # (?:\.\d+)?   : 非捕获组，可选的小数部分 (例如 .123)

    pattern = r'(?<!\d)(?<!\d\.)[-+]?\d+(?:\.\d+)?'

    # 使用 findall 查找所有匹配项
    numbers = re.findall(pattern, text)

    # 将结果转换为数字类型 (float 或 int) 以便后续使用，如果只需要字符串可省略此步
    result = []
    for num_str in numbers:
        if '.' in num_str:
            result.append(float(num_str))
        else:
            result.append(int(num_str))

    return result

def verify_dsl_numbers(dsl_numbers, code_numbers):
    """
    验证 DSL 中的所有非常数数字是否都能在代码定义中找到匹配项。

    参数:
    dsl_numbers (list): DSL 中提取的非常数数字列表 (S_DSL / na)
    code_numbers (list): 代码定义中的数字列表 (S_Code / nb)

    返回:
    bool: 如果验证通过返回 True，否则返回 False
    """

    # n 的范围是 -9 到 9 (注意 range 的结束值是不包含的，所以是 10)
    exponent_range = range(-9, 10)

    # 遍历 DSL 中的每一个数字 na
    for na in dsl_numbers:
        found_match = False

        # 尝试在代码数字列表 nb 中寻找匹配
        for nb in code_numbers:
            # 预先计算 nb 的绝对值并保留两位小数
            nb_abs_rounded = round(abs(nb), 2)

            # 遍历所有可能的指数 n
            for n in exponent_range:
                # 计算 |na| * 10^n
                scaled_na = abs(na) * (10 ** n)
                # 保留两位小数
                scaled_na_rounded = round(scaled_na, 2)

                # 比较
                if nb_abs_rounded == scaled_na_rounded:
                    found_match = True
                    # 找到匹配的 n 后，跳出指数循环
                    break

            if found_match:
                # 找到匹配的 nb 后，跳出 nb 循环，处理下一个 na
                break

        # 如果遍历完所有 nb 和所有 n，仍然没有为当前的 na 找到匹配
        if not found_match:
            print(f"验证失败: DSL数字 {na} 未在代码中找到匹配项。")
            return False

    # 如果循环正常结束，说明所有 na 都找到了匹配
    print("验证通过: 所有DSL数字均符合规则。")
    return True

def safe_append_jsonl(data, file_path):
    """安全追加数据到JSONL文件"""
    temp_path = str(file_path) + '.tmp'
    try:
        # 将新数据写入临时文件
        with open(temp_path, 'w', encoding='utf-8') as f:
            for item in data:
                json.dump(item, f, ensure_ascii=False)
                f.write('\n')  # 添加换行符

        # 将临时文件内容追加到目标文件
        with open(temp_path, 'rb') as src, open(file_path, 'ab') as dst:
            content = src.read()
            dst.write(content)

        os.remove(temp_path)
    except Exception as e:
        if Path(temp_path).exists():
            os.remove(temp_path)
        raise e
def read_jsonl_file(file_path):
    """
    读取指定文件夹中的所有JSONL文件，提取每个JSON对象的id字段，并返回包含所有id的列表。

    参数:
        folder_path (str): 要读取的文件夹路径

    返回:
        list: 包含所有id字段的列表
    """
    res = []
    # 获取所有JSONL文件的路径
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            try:
                data = json.loads(line.strip())
                    # 检查是否存在id字段
                res.append(data)
            except json.JSONDecodeError:
                print(f"警告：文件 {file_path} 中存在格式错误的行，已跳过。")
    return res
def write_json_file(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, sort_keys=True)