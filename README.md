# DQR Main Experiments

本目录整理 DQR 论文主试验所需的核心代码与数据：DQR 评分器的 SFT/GRPO 训练、数据评分与筛选、Qwen3-8B 下游训练，以及 FinQA、ConvFinQA、MultiHiertt、GSM8K 评测。

不包含 Qwen2.5-7B 消融、其他消融试验、FinQA 统一过滤测试集的构建代码与数据、模型权重、优化器状态、训练日志或历史检查点。`FinQA (Sel.)` 不在本仓库复现范围内。

## 目录

```text
scorer/                 DQR 评分器：数据准备、SFT、GRPO、评分与筛选
downstream/             Qwen3-8B 下游训练与四个数据集的评测
baselines/ds2/          DS² 主对比方法的评分、校正和子集生成代码
data/scorer/            评分器蒸馏 SFT 数据与 GRPO 数据
data/finqa_convfinqa/   主试验各方法的 FinQA+ConvFinQA 评分/筛选数据
data/multihiertt/       主试验各方法的 MultiHiertt 评分/筛选数据
data/test/              四个主试验测试集
results/main_results.csv 论文主结果（不含 FinQA Sel.）
DATA_MANIFEST.tsv        数据文件与方法对应关系
```

大型 JSON/JSONL 使用 gzip 压缩，所有文件均小于 GitHub 的 100MB 单文件限制。先解压：

```bash
bash scripts/decompress_data.sh
```

该命令保留 `.gz` 文件，并在同目录生成原始文件；原始大文件已被 `.gitignore` 排除，避免误上传。

## 环境

建议在独立 Python 环境中安装。主实验使用过 PyTorch 2.7.0、Transformers 4.51.3；请根据 CUDA 版本安装合适的 PyTorch wheel，再安装其余依赖：

```bash
pip install -r requirements.txt
```

基座模型默认为 `Qwen/Qwen3-8B`，由 Transformers 下载。也可以把配置中的模型路径改成本地路径。模型权重不在本目录中。

## 1. 训练 DQR 评分器

以下命令从 `scorer/` 目录运行。数据从随仓库提供的蒸馏样本开始，无需重新调用教师模型。

```bash
cd scorer
python scripts/prepare_data.py --config config.yaml

# 论文主配置使用 4 卡 DeepSpeed；单卡可去掉 deepspeed 启动器并将配置中的 deepspeed 设为 null。
deepspeed --num_gpus=4 scripts/train_sft.py --config config.yaml
deepspeed --num_gpus=4 scripts/train_grpo.py --config config.yaml
```

SFT 输出为 `scorer/outputs/scorer_sft`，GRPO 输出为 `scorer/outputs/scorer_rl`。核心配置见 `scorer/config.yaml`：SFT 最大长度 5120、3 epochs、lr 1e-6；GRPO 8 candidates、3 epochs、lr 5e-7、beta 0.2、epsilon 0.05。

## 2. 评分并保留 90% 数据

以 FinQA+ConvFinQA 为例：

```bash
cd scorer
python scripts/score_data.py \
  --config config.yaml \
  --input ../data/finqa_convfinqa/unselected.json \
  --output ../data/finqa_convfinqa/dqr_sft_rl_rescored.json \
  --selected-output ../data/finqa_convfinqa/dqr_sft_rl_selected.json \
  --percent 90
```

仓库已经提供主试验实际使用的评分文件，复现下游训练时不必重新评分。API 基线可使用 `scripts/score_data_api.py`，密钥只能通过 `JUDGE_API_KEY` 环境变量或命令行参数提供，仓库中不保存密钥。

DS² 的适配代码位于 `baselines/ds2/`；模型路径、数据路径和输出路径集中在 `run_finqa_pipeline.sh`。其原始项目为 https://github.com/UCSC-REAL/DS2 。

## 3. 训练下游 Qwen3-8B

从 `downstream/` 目录运行：

```bash
cd downstream
mkdir -p ../outputs
python finetune-0313.py          # FinQA+ConvFinQA，默认 DQR SFT+RL
python finetune-random.py        # FinQA+ConvFinQA，随机保留 90%
python finetune-muti.py          # MultiHiertt，默认 DQR SFT+RL
python finetune-muti-random.py   # MultiHiertt，随机保留 90%
```

其他方法通过修改脚本顶部的 `data_path` 和 `output_dir` 复现，数据对应关系见 `DATA_MANIFEST.tsv`：

- `unselected`：原始未筛选数据，`use_judge=0`。
- `dqr_sft`、`dqr_sft_rl`、`deepseek`、`gemini`、`qwen3_8b`：包含五维评分，训练时剔除最低 10%，即 `use_judge=0.10`。
- `ds2`：已经由 DS² 保留 90% 的文件，`use_judge=0`。
- `random`：使用对应 random 脚本，从完整数据随机保留 90%。

FinQA+ConvFinQA 主配置为 batch 48、micro batch 1、3 epochs、lr 3e-4、最大长度 4096。MultiHiertt 的 DQR 脚本最大长度为 8192。LoRA 参数保留在主试验原始脚本中。

## 4. 评测

从 `downstream/` 目录运行，默认评测 DQR SFT+RL 输出；更换 `lora_weights` 可评测其他方法：

```bash
cd downstream
python test_finqa.py
python generate_convfinqa_test.py
cd test_M && python test_M1.py && cd ..

# GSM8K 原始脚本使用合并后的模型：
python ../scorer/scripts/merge_lora.py \
  --base Qwen/Qwen3-8B \
  --adapter ../outputs/finqa_convfinqa/dqr_sft_rl \
  --output ../outputs/finqa_convfinqa/dqr_sft_rl_merged
python test_gsm8k.py
```

测试集路径分别为 `data/test/finqa.json`、`convfinqa.json`、`multihiertt.json`、`gsm8k.jsonl`。评测采用代码生成与 Exact Match，具体提示词、执行和数值比较逻辑保留在各评测脚本及 `tool.py` 中。

## 上传说明

直接上传本目录内容即可。`.gitignore` 会排除解压后的大型原始 JSON、模型输出、日志和缓存。上传前可运行：

```bash
bash scripts/check_package.sh
```

该脚本检查 Python 语法、压缩文件完整性、密钥模式、排除内容和 GitHub 单文件大小限制，不会重新训练模型。
