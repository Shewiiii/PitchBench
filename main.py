import os
import sys
import logging
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
import httpx
import json
import matplotlib.pyplot as plt

from consts import PROMPT, SOLUTION, MODELS, RESULTS_FILE
import asyncio

load_dotenv()
OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def score(
    proposition: Dict[str, str], model: str, solution: Dict[str, str] = SOLUTION
) -> int:
    if len(proposition) != len(solution):
        logging.warning(
            f"{model}: Length of proposition and solution are different: {len(proposition)} vs {len(solution)}"
        )

    s = 0
    for index, expected in solution.items():
        answer = proposition.get(index)
        if answer == expected:
            s += 1
            continue
        if expected.startswith("[") and expected.endswith("]"):  # Example: [A;N4]
            options = expected[1:-1].split(";")
            if answer in options: # Guess a pitch accent within multiple choices
                s += 0.5
    return s


def dict_of_proposition_array(
    proposition_array: list[dict[str, str]],
) -> dict[str, str]:
    proposition = {}
    for a in proposition_array:
        proposition[a["word_num"]] = a["answer"]

    return proposition


async def query_openrouter(
    models: List[str] = MODELS,
    prompt: str = PROMPT,
    overwrite_past_results: bool = False,
) -> Dict[str, Dict[str, Any]]:
    headers = {
        "Authorization": f"Bearer {OPEN_ROUTER_API_KEY}",
        "HTTP-Referer": "https://openrouter.ai",
    }
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "pitchbench_response",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "details": {"type": "string"},
                    "proposition": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "word_num": {"type": "string"},
                                "answer": {"type": "string"},
                            },
                            "required": ["word_num", "answer"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["details", "proposition"],
                "additionalProperties": False,
            },
        },
    }
    if RESULTS_FILE.exists() and not overwrite_past_results:
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            results = json.load(f)
    else:
        results = {}

    async with httpx.AsyncClient(timeout=60) as client:

        async def fetch_model(model: str) -> None:
            if model in results:
                proposition: dict[str, str] = results[model].get("proposition")
                if proposition:
                    logging.info(
                        f"Proposition from {model} got from json file: {results[model]['proposition']}"
                    )
                    return
                logging.info(
                    f"Existing proposition for {model} empty in json file, requerying."
                )
            logging.info(f"Requesting a solution to {model}.")
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": response_format,
            }
            try:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                logging.error(f"Could not call OpenRouter for {model}: {exc}")
                return

            payload_json = response.json()
            data = payload_json["choices"][0]["message"]
            usage = payload_json.get("usage") or {}
            completion_tokens = int(usage.get("completion_tokens") or 0)
            try:
                parsed = json.loads(data.get("content", "{}"))
                # Convert proposition to the right format
                # Array is supported by Sonnet 4.5 and GPT 5.1, but not object (dict) directly
                parsed["proposition"] = dict_of_proposition_array(parsed["proposition"])
            except (json.JSONDecodeError, TypeError):
                parsed = {
                    "details": data.get("content", ""),
                    "proposition": {},
                }

            results[model] = {
                "details": parsed.get("details", ""),
                "proposition": parsed["proposition"],
                "completion_tokens": completion_tokens,
            }
            logging.info(
                f"Proposition from {model} got: {results[model]['proposition']}"
            )

        await asyncio.gather(*(fetch_model(model) for model in models))

    logging.info("Saving the results in results.json.")
    json_results = json.dumps(results, ensure_ascii=False, indent=2)
    with open("results.json", "w", encoding="utf-8") as f:
        f.write(json_results)

    return results


def plot_results(results: Optional[Dict[str, Dict[str, str]]] = None) -> None:
    if not results:
        if not RESULTS_FILE.exists():
            logging.warning("No results to plot.")
            return
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            results = json.load(f)

    score_data = [
        (
            model,
            score(values.get("proposition", {}), model),
        )
        for model, values in results.items()
    ]
    token_data = [
        (model, values.get("completion_tokens")) for model, values in results.items()
    ]
    scores_sorted = sorted(score_data, key=lambda x: x[1], reverse=True)
    tokens_sorted = sorted(token_data, key=lambda x: x[1], reverse=False)

    def plot_metric(sorted_data: List[tuple], title: str, color: str) -> None:
        labels = [item[0] for item in sorted_data]
        values = [item[1] for item in sorted_data]
        if not any(values):
            logging.warning(f"No non-zero {title.lower()}.")
            return

        y_positions = list(range(len(labels)))
        fig, ax = plt.subplots(
            figsize=(10, max(2, 0.6 * len(labels))), facecolor="black"
        )
        ax.set_facecolor("black")
        bars = ax.barh(
            y_positions,
            values,
            color=color,
            edgecolor="#1f2933",
        )
        ax.invert_yaxis()
        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels, color="white")
        ax.spines[:].set_color("white")
        ax.tick_params(colors="white")
        ax.set_xlabel("Value", color="white")
        ax.set_title(title, color="white", pad=15)

        max_val = max(values)
        margin = max(1, int(0.05 * max_val))
        ax.set_xlim(0, max_val + margin)

        for bar in bars:
            width = bar.get_width()
            ax.text(
                width + margin * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{width}",
                va="center",
                ha="left",
                color="white",
            )

        plt.tight_layout()
        plt.show()

    plot_metric(scores_sorted, f"Scores (out of {len(SOLUTION)})", "#4ade80")
    plot_metric(tokens_sorted, "Token usage", "#60a5fa")


async def main() -> None:
    results = await query_openrouter()
    plot_results(results)


if __name__ == "__main__":
    asyncio.run(main())
