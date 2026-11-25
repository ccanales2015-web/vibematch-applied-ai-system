
"""
Experiment 1: Match Strength and Catalogue Coverage

Evaluates VibeMatch across three different preference profiles.
Records recommendation scores and auditor findings.

Run from the repository root:
    python -m experiments.experiment_1
"""

import json
from pathlib import Path

from src.recommender import load_songs, recommend_songs
from src.auditor import audit_recommendations


PROFILES = {
    "Baseline": {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.8,
    },
    "Represented genre": {
        "genre": "lofi",
        "mood": "chill",
        "energy": 0.4,
    },
    "Unsupported genre": {
        "genre": "classical",
        "mood": "sad",
        "energy": 0.1,
    },
}


def run_experiment():
    songs = load_songs("data/songs.csv")
    results = []

    for profile_name, preferences in PROFILES.items():

        recommendations = recommend_songs(
            preferences, songs, k=5
        )

        report = audit_recommendations(
            recommendations, songs, preferences
        )

        result = {
            "profile": profile_name,
            "preferences": preferences,
            "recommendations": [
                {
                    "title": song["title"],
                    "genre": song["genre"],
                    "score": round(score, 3),
                    "explanation": explanation,
                }
                for song, score, explanation in recommendations
            ],
            "audit": report,
        }

        results.append(result)

        print("\n" + "=" * 55)
        print(f"PROFILE: {profile_name}")
        print("=" * 55)

        print("Preferences:", preferences)

        for item in result["recommendations"]:
            print(
                f"{item['title']}: "
                f"{item['score']:.3f}"
            )

        print("\nAudit results:")
        print("Average score:", report["average_match_score"])
        print("Weak matches:", report["weak_matches"])
        print("Genre coverage:", report["genre_coverage"])
        print("Genre diversity:", report["genre_diversity"])
        print("Warnings:", report["warnings"])
        print("Status:", report["status"])

    output_path = Path("experiments/experiment_1_results.json")

    output_path.write_text(
        json.dumps(results, indent=4),
        encoding="utf-8",
    )

    print("\nResults saved to:", output_path)


if __name__ == "__main__":
    run_experiment()
