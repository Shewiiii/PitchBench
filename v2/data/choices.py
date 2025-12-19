import numpy as np
import json
from pathlib import Path

## This is the draft script that was used to choose the words of the benchmark ##


def draw_frequencies(draws: int, max_val: int) -> list[int]:
    numbers = np.arange(1, max_val + 1)
    weights = 1.0 / numbers
    normalized_weights = weights / weights.sum()
    choices = np.random.choice(numbers, size=draws, replace=False, p=normalized_weights)
    return choices.tolist()


def extract_words_by_frequencies(file_path, frequency_list):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Creating the dictionary {frequency: first_word_found}
    freq_map = {}
    for entry in data:
        # entry[0] is the word, entry[2] is the dictionary containing the frequency
        word = entry[0]
        freq_value = entry[2]["frequency"]

        if freq_value not in freq_map:
            freq_map[freq_value] = word

    results = []
    for f in frequency_list:
        # Remove words without a frequency
        word = freq_map.get(f, None)
        if word:
            results.append(word)
    return results


frequencies = draw_frequencies(50, 10000)
found_words = extract_words_by_frequencies(
    Path("v2/data/term_meta_bank_1.json"), frequencies
)

# Display random words
for f, w in zip(frequencies, found_words):
    print(f"Frequency {f}: {w}")

print("Final choice")
words = [
    "相次ぐ",
    "問う",
    "下さる",
    "警察",
    "行ける",
    "変わる",
    "資産",
    "明治",
    "於く",
    "唯",
    "走る",
    "姿",
    "試み",
    "玄関",
    "作る",
    "脅威",
    "腹",
    "たり",
    "行く",
    "作家",
    "強い",
    "大阪",
    "部分",
    "自分",
    "項",
    "見る",
    "戦争",
    "君",
    "する",
    "三十",
    "的",
    "として",
    "そして",
    "英語",
    "生まれる",
    "塵",
    "一般的",
    "輸送",
    "於て",
    "電機",
    "システム",
    "どうしても",
    "状態",
    "居る",
    "連携",
    "限定",
    "目指す",
    "条件",
    "去る",
    "違い"
]

for i, w in enumerate(words, 1):
    print(f"{i}. {w}")
