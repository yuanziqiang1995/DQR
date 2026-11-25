import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
from functools import partial

import torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import GRPOTrainer, GRPOConfig

from src.config import load_config
from src.prompts import system_prompt_ori, create_reader_request_processed
from src.rewards import judge_reward


def main():
    parser = argparse.ArgumentParser(description="GRPO RL 训练 judge 模型")
    parser.add_argument("--config", default=None, help="config.yaml 路径，默认 judge_pipeline/config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    rl = cfg["rl"]
    paths = cfg.get("paths", {})

    tokenizer = AutoTokenizer.from_pretrained(
        rl["tokenizer_path"],
        trust_remote_code=True,
        padding_side="left"
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    try:
        import flash_attn  # noqa: F401
        attn_impl = "flash_attention_2"
    except ImportError:
        attn_impl = "sdpa"
    model = AutoModelForCausalLM.from_pretrained(
        rl["model_path"],
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        attn_implementation=attn_impl,
    )
    model.gradient_checkpointing_enable()
    print(f"Model loaded on {model.device}")

    dataset = load_dataset(
        "parquet",
        data_files={"train": rl["data_path"]},
    )

    def preprocess_data(example):
        prompt_messages = [
            {"role": "system", "content": system_prompt_ori},
            {"role": "user", "content": create_reader_request_processed(example)}
        ]
        prompt = tokenizer.apply_chat_template(
            prompt_messages,
            tokenize=False,
            add_generation_prompt=True
        )
        return {"prompt": prompt}

    dataset = dataset.map(preprocess_data)

    reward_func = partial(judge_reward, weights=rl.get("reward_weights", [0.2] * 5))
    reward_func.__name__ = "judge_reward"

    grpo_config = GRPOConfig(
        optim=rl.get("optim", "adamw_bnb_8bit"),
        learning_rate=rl.get("learning_rate", 5e-7),
        num_generations=rl.get("num_generations", 8),
        max_prompt_length=rl.get("max_prompt_length", 6144),
        max_completion_length=rl.get("max_completion_length", 2048),
        beta=rl.get("beta", 0.2),
        epsilon=rl.get("epsilon", 0.05),
        per_device_train_batch_size=rl.get("per_device_train_batch_size", 8),
        gradient_accumulation_steps=rl.get("gradient_accumulation_steps", 4),
        num_train_epochs=rl.get("num_train_epochs", 3),
        save_strategy="epoch",  # 每个 epoch 保存一次 checkpoint
        save_total_limit=None,
        warmup_steps=rl.get("warmup_steps", 100),
        logging_steps=1,
        eval_steps=rl.get("eval_steps", 500),
        adam_beta1=rl.get("adam_beta1", 0.9),
        adam_beta2=rl.get("adam_beta2", 0.999),
        weight_decay=rl.get("weight_decay", 0.01),
        deepspeed=rl.get("deepspeed"),
        remove_unused_columns=False,
        gradient_checkpointing=True,
        output_dir=rl["output_dir"],
        report_to="tensorboard",
        logging_dir=rl.get("logging_dir", paths.get("logging_dir", "outputs/logs")),
    )

    trainer_kwargs = {}
    lora_cfg = rl.get("lora", None)
    if lora_cfg:
        from peft import LoraConfig
        trainer_kwargs["peft_config"] = LoraConfig(
            r=lora_cfg.get("r", 160),
            lora_alpha=lora_cfg.get("lora_alpha", 160),
            lora_dropout=lora_cfg.get("lora_dropout", 0.05),
            target_modules=lora_cfg.get("target_modules",
                                        ["q_proj", "k_proj", "v_proj", "o_proj"]),
            bias="none",
            task_type="CAUSAL_LM",
        )
        print(f"使用 LoRA-GRPO: r={lora_cfg.get('r', 160)}, alpha={lora_cfg.get('lora_alpha', 160)}")

    trainer = GRPOTrainer(
        model=model,
        args=grpo_config,
        reward_funcs=reward_func,
        train_dataset=dataset["train"],
        processing_class=tokenizer,
        **trainer_kwargs,
    )

    print("Starting GRPO training...")
    resume_from_checkpoint = rl.get("resume_from_checkpoint", None)
    if resume_from_checkpoint:
        trainer.train(resume_from_checkpoint)
    else:
        trainer.train()

    final_save_dir = rl["final_save_dir"]
    trainer.save_model(final_save_dir)
    tokenizer.save_pretrained(final_save_dir)

    print("Training completed!")


if __name__ == "__main__":
    main()
