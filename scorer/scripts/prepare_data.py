import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse

from src.config import load_config
from src.data_utils import read_jsonl_as_dict_list, save_dict_list_to_json
from src.prompts import system_prompt_ori, create_reader_request_processed, create_reader_response


def main():
    parser = argparse.ArgumentParser(description="准备 judge SFT 数据（jsonl -> 含 prompt/response 的 JSON）")
    parser.add_argument("--config", default=None, help="config.yaml 路径，默认 judge_pipeline/config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)["prepare"]

    data_jsonl = read_jsonl_as_dict_list(cfg["input_file"])

    raw_data = []
    for d in data_jsonl:
        raw_data.append({
            "system_prompt": system_prompt_ori,
            "context": create_reader_request_processed(d),
            "response": create_reader_response(d),
        })

    save_dict_list_to_json(raw_data, cfg["output_file"])
    print(f"处理完成，共处理 {len(raw_data)} 条数据，已保存到 {cfg['output_file']}")


if __name__ == "__main__":
    main()
