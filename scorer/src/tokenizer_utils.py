from typing import List, Dict, Any

import torch
from torch.utils.data import Dataset


class SFTDataset(Dataset):
    """训练时动态 tokenize 的 SFT 数据集。

    每个样本需包含 system_prompt / context / response 三个字段。
    只做 max_length 截断，不预 padding（交给 DataCollatorForSeq2Seq）。
    labels 中 prompt 部分为 -100，只对 assistant 回复计算 loss。
    """

    def __init__(self, data: List[Dict[str, Any]], tokenizer, max_length: int = 2048):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

        if not hasattr(self.tokenizer, 'chat_template') or self.tokenizer.chat_template is None:
            print("警告: tokenizer没有chat_template，将使用默认格式")

    @staticmethod
    def format_conversation(system_prompt: str, context: str, response: str) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context},
            {"role": "assistant", "content": response}
        ]

    def tokenize_and_create_labels(self, messages: List[Dict[str, str]]) -> Dict[str, torch.Tensor]:
        full_text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False
        )

        messages_without_response = messages[:-1]
        text_without_response = self.tokenizer.apply_chat_template(
            messages_without_response,
            tokenize=False,
            add_generation_prompt=True
        )

        full_tokens = self.tokenizer.encode(full_text, add_special_tokens=False)
        prompt_tokens = self.tokenizer.encode(text_without_response, add_special_tokens=False)

        labels = [-100] * len(full_tokens)

        assistant_start_pos = len(prompt_tokens)
        if assistant_start_pos < len(full_tokens):
            labels[assistant_start_pos:] = full_tokens[assistant_start_pos:]

        if len(full_tokens) > self.max_length:
            full_tokens = full_tokens[:self.max_length]
            labels = labels[:self.max_length]

        attention_mask = [1] * len(full_tokens)

        return {
            'input_ids': torch.tensor(full_tokens, dtype=torch.long),
            'attention_mask': torch.tensor(attention_mask, dtype=torch.long),
            'labels': torch.tensor(labels, dtype=torch.long)
        }

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        messages = self.format_conversation(
            item.get('system_prompt', ''),
            item['context'],
            item['response']
        )
        return self.tokenize_and_create_labels(messages)
