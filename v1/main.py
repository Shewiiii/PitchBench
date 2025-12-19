import os
import sys
import logging

from typing import List
from dotenv import load_dotenv
import httpx
import json
import matplotlib.pyplot as plt

from consts import PROMPT, SOLUTION, MODELS
from data_structure import Model, models
import asyncio

load_dotenv()
OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def dict_of_proposition_array(
    proposition_array: list[dict[str, str]],
) -> dict[str, str]:
    proposition = {}
    for a in proposition_array:
        proposition[a["word_num"]] = a["answer"]

    return proposition


async def query_openrouter(
    model_names: List[str] = MODELS,
    prompt: str = PROMPT,
) -> None:
    if not models.parsed_file:
        models.parse_results_file()

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

    async with httpx.AsyncClient(timeout=60) as client:

        async def fetch_model(model_name: str) -> None:
            if model_name in models.dico:
                logging.info(f"Existing proposition for {model_name} in json file.")
            logging.info(f"Requesting a solution to {model_name}.")
            payload = {
                "model": model_name,
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
                logging.error(f"Could not call OpenRouter for {model_name}: {exc}")
                return

            payload_json = response.json()
            data = payload_json["choices"][0]["message"]
            usage = payload_json.get("usage") or {}
            completion_tokens = int(usage.get("completion_tokens") or 0)
            try:
                parsed = json.loads(data.get("content", "{}"))
                # Convert proposition to the right format
                # Array is supported by Sonnet 4.5 and GPT 5.1, but not object (dict) directly
                proposition = dict_of_proposition_array(parsed["proposition"])
            except (json.JSONDecodeError, TypeError) as e:
                logging.error(f"{model_name}: {e}")
                proposition = {}

            if len(proposition) == 0:
                logging.warning(f"The model did not answer: {model_name}.")
                return

            if model_name not in models.dico:
                Model(model_name)

            logging.info(f"Proposition from {model_name} got.")
            models.dico[model_name].add_score(proposition, completion_tokens)

        await asyncio.gather(*(fetch_model(name) for name in model_names))

    logging.info("Saving the results in results.json.")
    models.save_to_file()


def plot_results() -> None:
    score_data = models.get_models_avg_score()
    token_data = models.get_models_avg_tokens()

    names_score = [f"{d[0]} (n={d[3]})" for d in score_data]
    values_score = [d[1] for d in score_data]
    cis_score = [d[2] for d in score_data]

    names_token = [f"{d[0]} (n={d[2]})" for d in token_data]
    values_token = [d[1] for d in token_data]

    def plot_metric(
        labels: List[str],
        values: List[float],
        title: str,
        color: str,
        xerr: List[float] = None,
    ) -> None:
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
            xerr=xerr,
            color=color,
            edgecolor="#1f2933",
            capsize=5 if xerr else 0,
            error_kw={"ecolor": "white"},
        )

        ax.invert_yaxis()
        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels, color="white")
        ax.spines[:].set_color("white")
        ax.tick_params(colors="white")
        ax.set_xlabel("Value", color="white")
        ax.set_title(title, color="white", pad=15)

        max_val = max(values)
        if xerr:
            max_val += max(xerr)

        margin = max(1, int(0.05 * max_val))
        ax.set_xlim(0, max_val + margin)

        for i, bar in enumerate(bars):
            width = bar.get_width()
            label_text = f"{width:.2f}"

            # Calculate position: if xerr exists, place text after the error bar
            text_x = width + margin * 0.02 + (xerr[i] + 0.3 if xerr else 0)

            ax.text(
                text_x,
                bar.get_y() + bar.get_height() / 2,
                label_text,
                va="center",
                ha="left",
                color="white",
            )

        plt.tight_layout()
        plt.show()

    plot_metric(
        names_score,
        values_score,
        f"Scores (out of {len(SOLUTION)})",
        "#4ade80",
        xerr=cis_score,
    )
    plot_metric(names_token, values_token, "Token usage", "#60a5fa")


async def main() -> None:
    c = int(input("Number of runs: "))
    for _ in range(c):
        await query_openrouter()
    if c == 0:
        models.parse_results_file()
    plot_results()


if __name__ == "__main__":
    asyncio.run(main())
