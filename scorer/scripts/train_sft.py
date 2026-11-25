import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import os

os.environ["WANDB_DISABLED"] = "true"

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.config import load_config
from src.data_utils import load_json, split_train_val
from src.tokenizer_utils import SFTDataset


def train(cfg):
    sft = cfg["sft"]
    paths = cfg.get("paths", {})

    base_model = sft["base_model"]
    data_path = sft["data_path"]
    output_dir = sft["output_dir"]
    batch_size = sft["batch_size"]
    micro_batch_size = sft["micro_batch_size"]
    num_epochs = sft["num_epochs"]
    learning_rate = sft["learning_rate"]
    cutoff_len = sft["cutoff_len"]
    val_ratio = sft.get("val_ratio", 0.05)
    seed = sft.get("seed", 42)
    deepspeed_config_path = sft.get("deepspeed", None)
    resume_from_checkpoint = sft.get("resume_from_checkpoint", None)
    warmup_steps = sft.get("warmup_steps", 100)
    save_steps = sft.get("save_steps", 1000)
    eval_steps = sft.get("eval_steps", 500)
    logging_dir = sft.get("logging_dir", paths.get("logging_dir", "outputs/logs"))

    if int(os.environ.get("LOCAL_RANK", 0)) == 0:
        print(
            f"Training model with params:\n"
            f"base_model: {base_model}\n"
            f"data_path: {data_path}\n"
            f"output_dir: {output_dir}\n"
            f"batch_size: {batch_size}\n"
            f"micro_batch_size: {micro_batch_size}\n"
            f"num_epochs: {num_epochs}\n"
            f"learning_rate: {learning_rate}\n"
            f"cutoff_len: {cutoff_len}\n"
            f"val_ratio: {val_ratio}\n"
            f"resume_from_checkpoint: {resume_from_checkpoint or False}\n"
        )
    assert base_model, "Please specify a base_model"

    gradient_accumulation_steps = batch_size // micro_batch_size

    world_size = int(os.environ.get("WORLD_SIZE", 1))
    ddp = world_size != 1
    if ddp:
        gradient_accumulation_steps = gradient_accumulation_steps // world_size

    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        device_map=None,
    )

    lora_cfg = sft.get("lora", None)
    if lora_cfg:
        from peft import LoraConfig, get_peft_model
        model = get_peft_model(model, LoraConfig(
            r=lora_cfg.get("r", 160),
            lora_alpha=lora_cfg.get("lora_alpha", 160),
            lora_dropout=lora_cfg.get("lora_dropout", 0.05),
            target_modules=lora_cfg.get("target_modules",
                                        ["q_proj", "k_proj", "v_proj", "o_proj"]),
            bias="none",
            task_type="CAUSAL_LM",
        ))
        model.print_trainable_parameters()

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    tokenizer.pad_token_id = 0
    tokenizer.padding_side = "left"  # Allow batched inference

    if resume_from_checkpoint:
        model.enable_input_require_grads()

    train_data = load_json(data_path)
    new_train_data, val_data = split_train_val(train_data, val_ratio=val_ratio, seed=seed)
    val_size = len(val_data)
    print("验证集数量：", val_size)

    if new_train_data and "input_ids" in new_train_data[0]:
        # 数据已预 tokenize（含 input_ids/attention_mask/labels），直接使用
        class PreTokenizedDataset(torch.utils.data.Dataset):
            def __init__(self, data):
                self.data = data

            def __len__(self):
                return len(self.data)

            def __getitem__(self, idx):
                item = self.data[idx]
                return {k: torch.tensor(item[k], dtype=torch.long)
                        for k in ("input_ids", "attention_mask", "labels")}

        train_dataset = PreTokenizedDataset(new_train_data)
        eval_dataset = PreTokenizedDataset(val_data) if val_size > 0 else None
    else:
        train_dataset = SFTDataset(new_train_data, tokenizer, max_length=cutoff_len)
        eval_dataset = SFTDataset(val_data, tokenizer, max_length=cutoff_len) if val_size > 0 else None

    if not ddp and torch.cuda.device_count() > 1:
        # keeps Trainer from trying its own DataParallelism when more than 1 gpu is available
        model.is_parallelizable = True
        model.model_parallel = True

    trainer = transformers.Trainer(
        model=model,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        args=transformers.TrainingArguments(
            per_device_train_batch_size=micro_batch_size,
            per_device_eval_batch_size=sft.get("eval_batch_size", 1),
            gradient_accumulation_steps=gradient_accumulation_steps,
            warmup_steps=warmup_steps,
            num_train_epochs=num_epochs,
            learning_rate=learning_rate,
            bf16=True,
            tf32=True,
            logging_steps=sft.get("logging_steps", 10),
            optim="adamw_torch",
            save_strategy="steps",
            eval_strategy="steps" if val_size > 0 else "no",
            eval_steps=eval_steps if val_size > 0 else None,
            save_steps=save_steps,
            output_dir=output_dir,
            save_total_limit=1,
            load_best_model_at_end=False,
            ddp_find_unused_parameters=False if ddp else None,
            deepspeed=deepspeed_config_path,
            report_to="tensorboard",
            logging_dir=logging_dir,
        ),
        data_collator=transformers.DataCollatorForSeq2Seq(
            tokenizer, pad_to_multiple_of=8, return_tensors="pt", padding=True
        ),
    )
    model.config.use_cache = False

    trainer.train(resume_from_checkpoint=resume_from_checkpoint)
    model.save_pretrained(output_dir)

    print(
        "\n If there's a warning about missing keys above, please disregard :)"
    )


def main():
    parser = argparse.ArgumentParser(description="SFT 训练 judge 模型")
    parser.add_argument("--config", default=None, help="config.yaml 路径，默认 judge_pipeline/config.yaml")
    args = parser.parse_args()
    train(load_config(args.config))


if __name__ == "__main__":
    main()
