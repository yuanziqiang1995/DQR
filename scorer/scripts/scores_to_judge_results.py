"""把 score_data.py 的评分输出转换为 finqa-judge-results 格式（供 train_qwen8b_*.py 使用）。

用法: python scripts/scores_to_judge_results.py --scored <scored.json> --output <judge-results.json>
输出 response 字段: {"think": <思考文本>, "answer": {五维分数字典}}
"""
import argparse
import json
import re
import sys


def split_think(raw):
    m = re.search(r'<think>(.*?)</think>', raw or '', re.DOTALL)
    return m.group(1).strip() if m else ''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scored", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    data = json.load(open(args.scored))
    out = []
    bad = 0
    for x in data:
        scores = x.get("judge_scores")
        if not scores:
            bad += 1
        r = dict(x)
        r.pop("judge_scores", None)
        r.pop("judge_avg_score", None)
        r["response"] = {"think": split_think(x.get("judge_raw_output", "")),
                         "answer": scores}
        out.append(r)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"共 {len(out)} 条（无分数 {bad} 条，训练脚本会按最低分处理）→ {args.output}")


if __name__ == "__main__":
    main()
