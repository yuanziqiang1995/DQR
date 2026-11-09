import random
from typing import Any, Callable, Dict, List


def select_top_percent(
    items: List[Dict[str, Any]],
    score_getter: Callable[[Dict[str, Any]], float],
    percent: float,
    seed: int = 42,
) -> List[Dict[str, Any]]:
    """按分数从高到低选取前 percent% 的数据。

    选取数量为 floor(len(items) * percent / 100)。
    若临界分数处出现同分（同分人数超过剩余名额），在同分候选中随机选取，
    保证最终结果恰好为目标数量。分数为 None 的样本视为最低分。
    """
    if not 0 < percent <= 100:
        raise ValueError("percent 必须在 (0, 100] 之间")

    n = len(items)
    k = int(n * percent / 100)
    if k >= n:
        return list(items)
    if k <= 0:
        return []

    def key(item):
        s = score_getter(item)
        return float("-inf") if s is None else s

    sorted_items = sorted(items, key=key, reverse=True)
    threshold = key(sorted_items[k - 1])

    selected = [it for it in sorted_items if key(it) > threshold]
    tied = [it for it in sorted_items if key(it) == threshold]
    need = k - len(selected)

    rng = random.Random(seed)
    selected.extend(rng.sample(tied, need))
    return selected
