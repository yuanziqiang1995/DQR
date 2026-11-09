import argparse

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


def main():
    parser = argparse.ArgumentParser(description="合并 LoRA adapter 到基座模型")
    parser.add_argument("--base", required=True, help="基座模型路径")
    parser.add_argument("--adapter", required=True, help="LoRA adapter 路径")
    parser.add_argument("--output", required=True, help="合并后模型输出路径")
    args = parser.parse_args()

    model = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.bfloat16, device_map="cpu"
    )
    model = PeftModel.from_pretrained(model, args.adapter)
    model = model.merge_and_unload()
    model.save_pretrained(args.output)
    tokenizer = AutoTokenizer.from_pretrained(args.base)
    tokenizer.save_pretrained(args.output)
    print(f"已合并保存到 {args.output}")


if __name__ == "__main__":
    main()
