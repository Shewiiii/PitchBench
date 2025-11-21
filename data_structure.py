from dataclasses import dataclass, field
from typing import Dict, Union, List, Tuple
import logging
from pathlib import Path
import json

from consts import SOLUTION


@dataclass
class Model:
    name: str
    scores: list[float] = field(default_factory=list)
    completions_tokens: list[int] = field(default_factory=list)
    run_count: int = 0
    avg_score: float = 0
    avg_token_usage: float = 0

    def __post_init__(self) -> None:
        models.add_model(self)
        self.calculate_avgerages()

    def __repr__(self) -> str:
        return f"Model class of {self.name}: ({self.avg_score},{self.avg_token_usage})"

    def to_dict(self) -> Dict[str, Union[int, str, Dict[str, str]]]:
        return {
            "scores": self.scores,
            "completions_tokens": self.completions_tokens,
            "run_count": self.run_count,
        }

    def calculate_avgerages(self) -> None:
        if self.scores:
            self.avg_score = round(sum(self.scores) / len(self.scores), 2)
        if self.completions_tokens:
            self.avg_token_usage = (
                f"{sum(self.completions_tokens) // len(self.completions_tokens):.2f}"
            )

    def add_score(
        self,
        proposition: Dict[str, str],
        completion_tokens: int,
        solution: Dict[str, str] = SOLUTION,
    ) -> None:
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

        self.scores.append(s)
        self.completions_tokens.append(completion_tokens)
        self.calculate_avgerages()
        self.run_count += 1


@dataclass
class Models:
    dico: Dict[str, Model] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Dict[str, Union[List[float], List[int], int]]]:
        return {model.name: model.to_dict() for model in models.dico.values()}

    def add_model(self, model: Model) -> None:
        self.dico[model.name] = model

    def get_models_avg_score(self) -> List[Tuple[str, int]]:
        scores = [(name, model.avg_score) for name, model in self.dico.items()]
        return sorted(scores, key=lambda x: x[1], reverse=True)

    def get_models_avg_tokens(self) -> List[Tuple[str, int]]:
        tokens = [(name, model.avg_token_usage) for name, model in self.dico.items()]
        return sorted(tokens, key=lambda x: x[1], reverse=False)

    def parse_results_file(path: Path = Path("./results.json")) -> Dict[str, Model]:
        if not path.exists():
            logging.info("No results file has been found.")
            return

        with open(path, "r", encoding="utf-8") as f:
            raw_results: Dict[str, Dict[Union[int, str, Dict[str, str]]]] = json.load(f)
            for name, values in raw_results.items():
                completions_tokens = values.get("completions_tokens")
                scores = values.get("scores")
                run_count = values.get("run_count")

                if not (scores or completions_tokens or run_count):
                    continue

                Model(name, scores, completions_tokens, run_count)

        return models

    def save_to_file(self, path: Path = Path("./results.json")) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.to_dict()))


models = Models()
