import json
import random


def read_jsonl_as_dict_list(file_path):
    result = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
                result.append(obj)
            except json.JSONDecodeError as e:
                print(f"[警告] 第 {line_number} 行格式错误: {e}")
                continue
    return result


def save_dict_list_to_json(dict_list, file_name):
    """将字典列表保存为 JSON 文件，成功返回 True，失败返回 False。"""
    try:
        json_string = json.dumps(dict_list, indent=4)
        with open(file_name, 'w') as file:
            file.write(json_string)
        return True
    except Exception as e:
        print(f"保存文件 {file_name} 时出错: {e}")
        return False


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def split_train_val(data, val_ratio=0.05, seed=42):
    """shuffle 后按比例切分训练/验证集，返回 (train_data, val_data)。"""
    data_copy = list(data)
    random.Random(seed).shuffle(data_copy)

    val_size = int(len(data_copy) * val_ratio)
    if val_size == 0 and val_ratio > 0 and len(data_copy) > 0:
        val_size = 1

    return data_copy[val_size:], data_copy[:val_size]
