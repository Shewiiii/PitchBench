from dataclasses import dataclass, field
from typing import Dict, Union, List, Tuple
import logging
from pathlib import Path
import json
import statistics
import math

from consts import SOLUTION, RESULTS_FILE


@dataclass
class Model:
    name: str
    scores: list[float] = field(default_factory=list)
    completions_tokens: list[int] = field(default_factory=list)
    propositions: list[Dict[str, str]] = field(
        default_factory=list
    )  # Added logging variable
    avg_score: float = field(init=False)
    ci_score: float = field(init=False)
    avg_token_usage: float = field(init=False)
    run_count: int = field(init=False)

    def __post_init__(self) -> None:
        models.add_model(self)
        self.update_variables()

    def __repr__(self) -> str:
        return f"Model class of {self.name}: ({self.avg_score},{self.avg_token_usage})"

    def to_dict(
        self,
    ) -> Dict[str, Union[int, str, List[float], List[int], List[Dict[str, str]]]]:
        return {
            "scores": self.scores,
            "completions_tokens": self.completions_tokens,
            "propositions": self.propositions,
            "run_count": self.run_count,
        }

    def update_variables(self) -> None:
        self.run_count = len(self.scores)
        if self.scores:
            self.avg_score = round(sum(self.scores) / len(self.scores), 2)
            if self.run_count > 1:
                stdev = statistics.stdev(self.scores)
                self.ci_score = 1.96 * stdev / math.sqrt(self.run_count)
            else:
                self.ci_score = 0.0
        else:
            self.avg_score = 0.0
            self.ci_score = 0.0

        if self.completions_tokens:
            self.avg_token_usage = round(
                sum(self.completions_tokens) / len(self.completions_tokens), 2
            )
        else:
            self.avg_token_usage = 0.0

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
            if expected.startswith("[") and expected.endswith("]"):  # Example: [A;N]
                options = expected[1:-1].split(";")
                if answer in options:  # Guess a pitch accent within multiple choices
                    s += 1

        self.scores.append(s * 100 / len(SOLUTION))  # Convert to percentage
        self.completions_tokens.append(completion_tokens)
        self.propositions.append(proposition)  # Log the proposition
        self.update_variables()


@dataclass
class Models:
    dico: Dict[str, Model] = field(default_factory=dict)
    parsed_file: bool = False

    def to_dict(self) -> Dict[str, Dict[str, Union[List[float], List[int], int]]]:
        return {model.name: model.to_dict() for model in models.dico.values()}

    def add_model(self, model: Model) -> None:
        self.dico[model.name] = model

    def get_models_avg_score(self) -> List[Tuple[str, float, float, int]]:
        scores = [
            (name, model.avg_score, model.ci_score, model.run_count)
            for name, model in self.dico.items()
        ]
        return sorted(scores, key=lambda x: x[1], reverse=True)

    def get_models_avg_tokens(self) -> List[Tuple[str, float, int]]:
        tokens = [
            (name, model.avg_token_usage, model.run_count)
            for name, model in self.dico.items()
        ]
        return sorted(tokens, key=lambda x: x[1], reverse=False)

    def get_run_counts(self) -> List[Tuple[str, int]]:
        return [(name, model.run_count) for name, model in self.dico.items()]

    def parse_results_file(
        self, path: Path = RESULTS_FILE
    ) -> Dict[str, Model]:
        if not path.exists():
            logging.info("No results file has been found.")
            return

        self.parsed_file = True
        with open(path, "r", encoding="utf-8") as f:
            raw_results: Dict[str, Dict[Union[int, str, Dict[str, str]]]] = json.load(f)
            for name, values in raw_results.items():
                completions_tokens = values.get("completions_tokens")
                scores = values.get("scores")
                run_count = values.get("run_count")
                propositions = values.get("propositions", [])

                if not (scores or completions_tokens or run_count):
                    continue

                Model(name, scores, completions_tokens, propositions)

        return models

    def save_to_file(self, path: Path = RESULTS_FILE) -> None:
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps(self.to_dict(), indent=4))


models = Models()
