import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_utils import load_json
from src.prompts import system_prompt_ori, create_reader_request_processed
from src.selection import select_top_percent

DEFAULT_API_KEY = None
DEFAULT_BASE_URL = "https://api.gpt.ge/v1/"
DEFAULT_MODEL = "gemini-3.1-flash-lite-preview"

SCORE_KEYS = [
    "correctness_of_code_answer",
    "relevance_and_sufficiency",
    "clarity_of_question",
    "quality_of_code_answer",
    "quality_of_context",
]


def adapt_sample(sample):
    """字段适配：finqa 数据中的 program 对应 prompt 模板中的 code。"""
    adapted = dict(sample)
    if "code" not in adapted and "program" in adapted:
        adapted["code"] = adapted["program"]
    return adapted


def extract_answer_json(text):
    """从输出中提取 JSON 对象：优先取 </think> 之后的内容，再找最外层 {}。"""
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def parse_scores(text):
    """从模型输出中解析五项分数；解析失败返回 None。"""
    answer = extract_answer_json(text)
    if not isinstance(answer, dict):
        return None
    scores = {}
    for key in SCORE_KEYS:
        val = answer.get(key)
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            return None
        scores[key] = max(0.0, min(10.0, float(val)))
    return scores


def score_one(client, model, sample, max_tokens, retries):
    """调用 API 给单条样本评分，失败重试 retries 次；返回 (scores, raw_output)。"""
    adapted = adapt_sample(sample)
    messages = [
        {"role": "system", "content": system_prompt_ori},
        {"role": "user", "content": create_reader_request_processed(adapted)},
    ]
    last_err = None
    for attempt in range(retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.0,
            )
            text = resp.choices[0].message.content or ""
            return parse_scores(text), text
        except Exception as e:  # 网络/限流/服务端错误
            last_err = e
            if attempt < retries:
                time.sleep(2 ** attempt * 5)
    print(f"  请求失败（已重试 {retries} 次）: {last_err}", file=sys.stderr)
    return None, f"<API error: {last_err}>"


def main():
    parser = argparse.ArgumentParser(description="用在线 API 模型给数据打分并提取前 n%%")
    parser.add_argument("--input", required=True, help="待评分数据（JSON 列表）")
    parser.add_argument("--output", default=None,
                        help="评分结果输出路径，默认为 <input去掉.json>_scored_api.json")
    parser.add_argument("--selected-output", default=None,
                        help="前 n%% 筛选结果输出路径，默认为 <input去掉.json>_selected_api.json")
    parser.add_argument("--percent", type=float, default=90.0, help="保留比例（默认 90）")
    parser.add_argument("--seed", type=int, default=42, help="同分随机选取的种子")
    parser.add_argument("--model", default=os.environ.get("JUDGE_MODEL", DEFAULT_MODEL),
                        help=f"模型名，默认 {DEFAULT_MODEL}，也可用环境变量 JUDGE_MODEL")
    parser.add_argument("--base-url", default=os.environ.get("JUDGE_BASE_URL", DEFAULT_BASE_URL),
                        help=f"API base_url，默认 {DEFAULT_BASE_URL}，也可用环境变量 JUDGE_BASE_URL")
    parser.add_argument("--api-key", default=os.environ.get("JUDGE_API_KEY", DEFAULT_API_KEY),
                        help="API key，通过 --api-key 或环境变量 JUDGE_API_KEY 指定")
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--workers", type=int, default=8, help="并发请求数")
    parser.add_argument("--retries", type=int, default=3, help="单条失败重试次数")
    parser.add_argument("--save-every", type=int, default=50, help="每完成多少条增量保存一次")
    args = parser.parse_args()

    if not args.model or not args.api_key:
        sys.exit("请通过 --model/--api-key 或环境变量 JUDGE_MODEL/JUDGE_API_KEY 指定模型和密钥"
                 + ("；还需 --base-url 或 JUDGE_BASE_URL" if not args.base_url else ""))

    input_base = args.input[:-5] if args.input.endswith(".json") else args.input
    if not args.output:
        args.output = input_base + "_scored_api.json"
    if not args.selected_output:
        args.selected_output = input_base + "_selected_api.json"
    selected_output = args.selected_output

    data = load_json(args.input)
    print(f"共加载 {len(data)} 条数据，模型: {args.model}")

    client = OpenAI(api_key=args.api_key, base_url=args.base_url)
    results = [None] * len(data)

    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(score_one, client, args.model, s, args.max_tokens, args.retries): i
            for i, s in enumerate(data)
        }
        for fut in as_completed(futures):
            i = futures[fut]
            scores, raw = fut.result()
            avg = sum(scores.values()) / len(SCORE_KEYS) if scores else None
            results[i] = {
                **data[i],
                "judge_scores": scores,
                "judge_avg_score": avg,
                "judge_raw_output": raw,
                "judge_model": args.model,
            }
            done += 1
            if done % 10 == 0 or done == len(data):
                print(f"已评分 {done}/{len(data)}")
            if done % args.save_every == 0:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"评分结果已保存: {args.output}")

    failed = sum(1 for r in results if r["judge_scores"] is None)
    if failed:
        print(f"警告: {failed} 条输出解析失败（judge_scores 为 null，按最低分处理）")

    selected = select_top_percent(
        results, lambda r: r["judge_avg_score"], args.percent, args.seed
    )
    with open(selected_output, "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)
    print(f"前 {args.percent}% 共 {len(selected)} 条已保存: {selected_output}")


if __name__ == "__main__":
    main()
