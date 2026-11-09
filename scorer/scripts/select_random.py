import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_utils import load_json


def main():
    parser = argparse.ArgumentParser(description="随机保留前 n%% 的数据（Random Selection 基线）")
    parser.add_argument("--input", required=True, help="输入数据（JSON 列表）")
    parser.add_argument("--output", default=None,
                        help="输出路径，默认为 <input去掉.json>_selected_random.json")
    parser.add_argument("--percent", type=float, default=90.0, help="保留比例（默认 90）")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not args.output:
        base = args.input[:-5] if args.input.endswith(".json") else args.input
        args.output = base + "_selected_random.json"

    data = load_json(args.input)
    k = int(len(data) * args.percent / 100)
    rng = random.Random(args.seed)
    selected = rng.sample(data, k)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)
    print(f"共 {len(data)} 条，随机保留 {k} 条（seed={args.seed}）: {args.output}")


if __name__ == "__main__":
    main()
