# DQR Main Experiments

This repository contains the core implementation and datasets for the main DQR experiments: scorer training with SFT and GRPO, data scoring and selection, Qwen3-8B downstream fine-tuning, and evaluation on FinQA, ConvFinQA, MultiHiertt, and GSM8K.

## Repository Layout

```text
scorer/                  Scorer data preparation, SFT, GRPO, scoring, and selection
downstream/              Qwen3-8B fine-tuning and benchmark evaluation
baselines/ds2/           DS2 scoring, score curation, and subset generation
data/scorer/             Distilled samples for scorer SFT
data/finqa_convfinqa/    FinQA+ConvFinQA training and scoring data by method
data/multihiertt/        MultiHiertt training and scoring data by method
data/test/               Benchmark evaluation sets
results/main_results.csv Main-table Exact Match scores
DATA_MANIFEST.tsv         Dataset descriptions and method mapping
```

## Data Preparation

The JSON and JSONL datasets are distributed as gzip archives. Extract them before training or evaluation:

```bash
bash scripts/decompress_data.sh
```

The script preserves the `.gz` archives and writes the extracted files beside them. Extracted datasets, generated models, logs, and caches are ignored by Git.

## Environment

Use a dedicated Python environment. The main experiments used PyTorch 2.7.0 and Transformers 4.51.3. Install the PyTorch build appropriate for your CUDA version, followed by the remaining dependencies:

```bash
pip install -r requirements.txt
```

The default base model is `Qwen/Qwen3-8B`. Transformers downloads it automatically; a local model path can also be used in the configuration files.

## 1. Train the DQR Scorer

Run the following commands from `scorer/`:

```bash
cd scorer
python scripts/prepare_data.py --config config.yaml

deepspeed --num_gpus=4 scripts/train_sft.py --config config.yaml
deepspeed --num_gpus=4 scripts/train_grpo.py --config config.yaml
```

For a single-GPU run, launch the scripts with Python and set the corresponding `deepspeed` entry to `null` in `config.yaml`.

SFT writes to `scorer/outputs/scorer_sft`, and GRPO writes to `scorer/outputs/scorer_rl`. The main settings are in `scorer/config.yaml`: SFT uses a maximum length of 5120, 3 epochs, and learning rate 1e-6. GRPO uses 8 candidates, 3 epochs, learning rate 5e-7, beta 0.2, and epsilon 0.05.

Before running GRPO, place a parquet dataset at `../data/scorer/rl_data.parquet`. It should contain the sample fields used by `src/prompts.py`, together with `response_think` and `response_answer` for the reward function in `src/rewards.py`.

## 2. Score and Select Data

The following example retains 90% of the FinQA+ConvFinQA data:

```bash
cd scorer
python scripts/score_data.py \
  --config config.yaml \
  --input ../data/finqa_convfinqa/unselected.json \
  --output ../data/finqa_convfinqa/dqr_sft_rl_rescored.json \
  --selected-output ../data/finqa_convfinqa/dqr_sft_rl_selected.json \
  --percent 90
```

The scored datasets used in the main experiments are provided under `data/finqa_convfinqa/` and `data/multihiertt/`.

For API-based scoring, set `JUDGE_API_KEY` in the environment or pass `--api-key` to `scripts/score_data_api.py`.

The DS2 implementation is under `baselines/ds2/`. Its model, input, and output paths are configured in `run_finqa_pipeline.sh`. The original DS2 project is available at https://github.com/UCSC-REAL/DS2.

## 3. Fine-tune Qwen3-8B

Run from `downstream/`:

```bash
cd downstream
mkdir -p ../outputs
python finetune-0313.py          # FinQA+ConvFinQA, DQR SFT+RL
python finetune-random.py        # FinQA+ConvFinQA, random 90% subset
python finetune-muti.py          # MultiHiertt, DQR SFT+RL
python finetune-muti-random.py   # MultiHiertt, random 90% subset
```

To run another method, change `data_path` and `output_dir` near the training function signature. See `DATA_MANIFEST.tsv` for the dataset mapping:

- `unselected`: use the original dataset with `use_judge=0`.
- `dqr_sft`, `dqr_sft_rl`, `deepseek`, `gemini`, and `qwen3_8b`: use five-dimensional scores and remove the lowest-scoring 10% with `use_judge=0.10`.
- `ds2`: use the provided 90% subset with `use_judge=0`.
- `random`: use the corresponding random-training script to retain 90% of the complete dataset.

FinQA+ConvFinQA training uses batch size 48, micro batch size 1, 3 epochs, learning rate 3e-4, and maximum length 4096. The MultiHiertt DQR script uses maximum length 8192. LoRA settings are defined in the training scripts.

## 4. Evaluate

The evaluation scripts default to the DQR SFT+RL adapter. Change `lora_weights` to evaluate another method:

```bash
cd downstream
python test_finqa.py
python generate_convfinqa_test.py
cd test_M && python test_M1.py && cd ..
```

GSM8K evaluation uses a merged model:

```bash
cd downstream
python ../scorer/scripts/merge_lora.py \
  --base Qwen/Qwen3-8B \
  --adapter ../outputs/finqa_convfinqa/dqr_sft_rl \
  --output ../outputs/finqa_convfinqa/dqr_sft_rl_merged
python test_gsm8k.py
```

The evaluation sets are `data/test/finqa.json`, `convfinqa.json`, `multihiertt.json`, and `gsm8k.jsonl`. Evaluation uses executable code generation and Exact Match. Prompt construction, execution, and numerical comparison are implemented in the evaluation scripts and `tool.py`.

## Package Validation

Run the package checks with:

```bash
bash scripts/check_package.sh
```

The checks cover Python syntax, gzip integrity, benchmark sizes, credential patterns, file-size limits, and SHA-256 checksums.
