
"""
Experiment 3: Recommendation Consistency

Runs identical inputs ten times and compares
recommendation outputs and audit reports.
"""

import json
from pathlib import Path

from src.recommender import load_songs, recommend_songs
from src.auditor import audit_recommendations


RUNS = 10

PREFERENCES = {
    "genre": "pop",
    "mood": "happy",
    "energy": 0.8,
}


def run_experiment():
    songs = load_songs("data/songs.csv")

    results = []

    for run_number in range(RUNS):

        recommendations = recommend_songs(
            PREFERENCES, songs, k=5
        )

        report = audit_recommendations(
            recommendations, songs, PREFERENCES
        )

        result = {
            "titles": [
                song["title"]
                for song, score, explanation in recommendations
            ],
            "scores": [
                round(score, 6)
                for song, score, explanation in recommendations
            ],
            "average_score": report["average_match_score"],
            "weak_matches": report["weak_matches"],
            "warnings": report["warnings"],
            "status": report["status"],
        }

        results.append(result)

        print(f"Run {run_number + 1}: {result['titles']}")

    baseline = results[0]

    consistent = all(
        result == baseline for result in results
    )

    summary = {
        "runs": RUNS,
        "identical_outputs": consistent,
        "baseline": baseline,
        "all_results": results,
    }

    output_path = Path("experiments/experiment_3_results.json")

    output_path.write_text(
        json.dumps(summary, indent=4),
        encoding="utf-8",
    )

    print("\nEXPERIMENT 3 SUMMARY")
    print("--------------------")
    print("Runs:", RUNS)
    print("Identical outputs:", consistent)
    print("Result:", "PASS" if consistent else "FAIL")
    print("Saved:", output_path)


if __name__ == "__main__":
    run_experiment()
