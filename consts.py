from pathlib import Path
from typing import Dict

PROMPT = """
Give the Tokyo-standard pitch accent (高低アクセント) of all the following japanese words, in order, in the following format.
With the letters: H: heiban, A: atamadaka, N: nakadaka, O: odaka, build a dictionary whose keys are the word indices (starting at 1) and whose values are the corresponding pitch accent labels.
For nakadaka, indicate after which mora the accent drops. For example, 青い is N2.
If multiple accents are possible, indicate them in square brackets (in this order: H then A then N then O) separating the letters with semicolons.
For example, 博物館 is [N3;N4], and ちょっと is [H;A;O].

Detail your answer in the "details" field, then put your propositions in the "proposition" array.
Example of proposition: [{"word_num": "1", "answer": "A"}, {"word_num": "2", "answer": "H"}, ...]
Even if you have low confidence, give a best-effort answer from memory/knowledge now.

1. 筋萎縮性側索硬化症 
2. 上位
3. 運動ニューロン
4. 下位
5. 両者
6. 細胞
7. 体 (たい)
8. 散発
9. 性
10. 賭け
11. 進行性
12. 神経
13. 神経変性疾患
14. 磁気共鳴映像法
15. 間質
16. 詳らか
17. 乏精子症
18. 旧遊
19. 最低血圧
20. 母趾
21. 萎縮腎
22. 事典
23. この世
24.  飼い主
25. 雄
26. 気分転換
27. 煮る
28. 八月
29. 寝そべる
30. 運ぶ
"""

SOLUTION_STRING = "[H;N6],A,N5,A,A,H,A,H,A,O,H,A,H,N9,H,N3,A,H,N5,A,N3,H,[H;O],[A;N2],O,N4,H,[H;O],N3,H"  # No space


def _build_solution_map(solution_text: str) -> Dict[int, str]:
    entries = solution_text.split(",")
    return {str(index + 1): entry for index, entry in enumerate(entries)}


SOLUTION = _build_solution_map(SOLUTION_STRING)
MODELS = [
    "google/gemini-3-pro-preview",
    "google/gemini-2.5-pro",
    "google/gemini-2.5-flash",
    "anthropic/claude-sonnet-4.5",
    "moonshotai/kimi-k2-thinking",
    "moonshotai/kimi-k2-0905",
    "deepseek/deepseek-chat-v3-0324",
    "deepseek/deepseek-r1-0528",
    "openai/gpt-5.1",
    "openai/gpt-5.1-chat",
    "openai/gpt-5",
    "openai/gpt-5-chat",
    "openai/gpt-5-mini",
    "openai/gpt-4o",
    "x-ai/grok-4",
    "x-ai/grok-4-fast",
]
RESULTS_FILE = Path("./results.json")
