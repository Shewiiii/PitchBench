from dataclasses import dataclass, field
from typing import Dict, Union, List, Tuple
import logging
from pathlib import Path
import json

from consts import SOLUTION


@dataclass
class Model:
    name: str
    details: str
    proposition: Dict[str, str]
    completion_tokens: int
    score: float = field(init=False)

    def __post_init__(self) -> None:
        self.set_score()
        models.add_model(self)

    def __repr__(self) -> str:
        return f"Model class of {self.name}, score: {self.score}, completion tokens: {self.completion_tokens}"

    def to_dict(self) -> Dict[str, Union[int, str, Dict[str, str]]]:
        return {
            "details": self.details,
            "proposition": self.proposition,
            "completion_tokens": self.completion_tokens,
        }

    def set_score(self, solution: Dict[str, str] = SOLUTION) -> None:
        proposition = self.proposition
        if len(proposition) != len(solution):
            logging.warning(
                f"{self.name}: Length of proposition and solution are different: {len(proposition)} vs {len(solution)}"
            )

        s = 0
        for index, expected in solution.items():
            answer = proposition.get(index)
            if answer == expected:
                s += 1
                continue
            if expected.startswith("[") and expected.endswith("]"):  # Example: [A;N4]
                options = expected[1:-1].split(";")
                if answer in options:  # Guess a pitch accent within multiple choices
                    s += 0.5

        self.score = s


@dataclass
class Models:
    dico: Dict[str, Model] = field(default_factory=dict)

    def add_model(self, model: Model) -> None:
        self.dico[model.name] = model

    def get_models_score(self) -> List[Tuple[str, int]]:
        scores: list[Tuple[str, int]] = []  # [("model", score)]

        for name, model in self.dico.items():
            proposition: Dict[str, str] = model.proposition
            if len(proposition) != len(SOLUTION):
                logging.warning(
                    f"{name}: Length of proposition and solution are different: {len(proposition)} vs {len(SOLUTION)}"
                )

            s = 0
            for index, expected in SOLUTION.items():
                answer = proposition.get(index)
                if answer == expected:
                    s += 1
                    continue
                if expected.startswith("[") and expected.endswith(
                    "]"
                ):  # Example: [A;N4]
                    options = expected[1:-1].split(";")
                    if (
                        answer in options
                    ):  # Guess a pitch accent within multiple choices
                        s += 0.5
            scores.append((name, s))

        return sorted(scores, key=lambda x: x[1], reverse=True)

    def get_models_completion_tokens(self) -> List[Tuple[str, int]]:
        models_completion_tokens = []
        for name, model in self.dico.items():
            models_completion_tokens.append((name, model.completion_tokens))

        return sorted(models_completion_tokens, key=lambda x: x[1], reverse=False)


models = Models()


def parse_results_file(path: Path = Path("./results.json")) -> Dict[str, Model]:
    if not path.exists():
        logging.info("No results file has been found.")
        return

    with open(path, "r", encoding="utf-8") as f:
        raw_results: Dict[str, Dict[Union[int, str, Dict[str, str]]]] = json.load(f)
        for name, values in raw_results.items():
            details = values.get("details")
            completion_tokens = values.get("completion_tokens")
            proposition = values.get("proposition")

            if not (details or completion_tokens or proposition):
                continue

            Model(name, details, proposition, completion_tokens)

    return models
