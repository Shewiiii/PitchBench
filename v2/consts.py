from pathlib import Path
from typing import Dict

PROMPT = """
Give the Tokyo-standard pitch accent (高低アクセント) of all the following japanese words, in order, in the following format.
With the letters: H: heiban, A: atamadaka, N: nakadaka, O: odaka, build a dictionary whose keys are the word indices (starting at 1) and whose values are the corresponding pitch accent labels.
If multiple accents are possible, indicate only one of them.
For example, ちょっと can be H, or A, or O.

You can think and detail your answer in the "details" field, then put your propositions in the "proposition" array.
Example of proposition: [{"word_num": "1", "answer": "A"}, {"word_num": "2", "answer": "H"}, ...]
Even if you have low confidence, give a best-effort answer from memory/knowledge now.

1. 相次ぐ
2. 問う
3. 下さる
4. 警察
5. 行ける
6. 変わる
7. 資産
8. 明治
9. 勤める
10. 唯
11. 走る
12. 姿
13. 試み
14. 玄関
15. 作る
16. 脅威
17. 腹
18. たり
19. 行く
20. 作家
21. 強い
22. 大阪
23. 部分
24. 自分
25. 項
26. 見る
27. 戦争
28. 君
29. する
30. 三十
31. 的
32. とする
33. そして
34. 英語
35. 生まれる
36. 塵
37. 一般的
38. 輸送
39. 於て
40. 電機
41. システム
42. どうしても
43. 状態
44. 居る
45. 連携
46. 限定
47. 目指す
48. 条件
49. 去る
50. 違い
"""

SOLUTION_STRING = "A,[A;H],N,H,H,H,[H;A],A,N,A,N,A,[H;O],A,N,A,O,H,H,[A;H],N,H,A,H,A,A,H,[A;H],H,A,H,N,H,H,H,O,H,H,[H;A],A,A,[N;A],H,H,H,H,N,[N;H],A,H"  # No space


def _build_solution_map(solution_text: str) -> Dict[int, str]:
    entries = solution_text.split(",")
    return {str(index + 1): entry for index, entry in enumerate(entries)}


SOLUTION = _build_solution_map(SOLUTION_STRING)
MODELS = [
    "google/gemini-3-pro-preview",
    "google/gemini-3-flash-preview",
    "google/gemini-2.5-pro",
    "google/gemini-2.5-flash",
    "anthropic/claude-sonnet-4.5",
    "anthropic/claude-opus-4.5",
    "moonshotai/kimi-k2-thinking",
    "moonshotai/kimi-k2-0905",
    "deepseek/deepseek-chat-v3-0324",
    "deepseek/deepseek-r1-0528",
    "openai/gpt-5.2",
    "openai/gpt-5.2-chat",
    "openai/gpt-5.1",
    "openai/gpt-5.1-chat",
    "openai/gpt-5",
    "openai/gpt-5-chat",
    "openai/gpt-5-mini",
    "openai/gpt-4o",
    "mistralai/mistral-nemo",
    "x-ai/grok-4.1-fast",
    "x-ai/grok-4",
    "x-ai/grok-4-fast",
]
RESULTS_FILE = Path("./results.json")
