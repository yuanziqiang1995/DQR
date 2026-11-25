#!/bin/bash
# DS2 pipeline for the local finqa+convfinqa dataset (single RTX 4090, 24GB)
# Data: data/finqa-convfinqa-g1-g2-1102.json (18853 samples)
set -e
cd "$(dirname "$0")"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

DATA_PATH="data/finqa-convfinqa-g1-g2-1102.json"
MODEL_PATH="models/Meta-Llama-3.1-8B-Instruct"
RATING_MODEL="meta-llama/Meta-Llama-3.1-8B-Instruct"  # logical name for output paths
DATASET_NAME="finqa"
SUBSET_SIZE=0.9   # keep 90% of the processed data for training

########## Step 1: LLM-prompt-based rating ##########
echo "===== Step 1: scoring with local Llama-3.1-8B-Instruct (single GPU) ====="
cd LLM_scoring
python scoring.py \
    --model_name ../${MODEL_PATH} \
    --dataset_name ${DATASET_NAME} \
    --data_path ../${DATA_PATH} \
    --output_dir ../scoring_output/
cd ..

########## Step 2: Score curation ##########
echo "===== Step 2: score curation ====="
cd score_curation
CUDA_VISIBLE_DEVICES=0 python diagnose.py \
    --config finqa_template.py \
    --dataset_name ${DATASET_NAME} \
    --score_root_path ../scoring_output/ \
    --output_dir ../score_curation_results/ \
    --rating_model ${RATING_MODEL}
cd ..

########## Step 3: Data selection ##########
echo "===== Step 3: subset generation ====="
python subset_generation.py \
    --dataset_name ${DATASET_NAME} \
    --model_name ${RATING_MODEL} \
    --selected_subset_size ${SUBSET_SIZE} \
    --root_score_path scoring_output \
    --score_curation_path score_curation_results \
    --output_dir selected_data

echo "===== Done. Selected subset: selected_data/${RATING_MODEL}/${DATASET_NAME}/ds2_10k_dataset.json ====="
