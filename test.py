import json
from typing import Dict
from consts import SOLUTION
import logging


def get_scores(
    results: Dict[str, Dict[str, str]], solution: Dict[str, str] = SOLUTION
) -> Dict[str, int]:
    scores: Dict[str, int] = {}  # {model: score}

    for model, proposition in results.items():
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
                if answer in options:  # Guess a pitch accent within multiple choices
                    s += 0.5
        scores[model] = s
        
    return scores
