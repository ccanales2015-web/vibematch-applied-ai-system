
"""
Experiment 2: Catalogue Coverage Threshold

Tests how the auditor responds to different proportions
of preferred-genre songs in synthetic catalogues.

Run from repository root:
    python -m experiments.experiment_2
"""

import json
from pathlib import Path

from src.auditor import audit_recommendations


PREFERRED_GENRE = "pop"

COVERAGE_TESTS = {
    "A": 0,
    "B": 1,
    "C": 2,
    "D": 3,
}

CATALOGUE_SIZE = 10


def create_catalogue(matching_count):
    """Create a synthetic catalogue with controlled genre coverage."""

    songs = []

    for i in range(CATALOGUE_SIZE):
        if i < matching_count:
            genre = PREFERRED_GENRE
        else:
            genre = "rock" if i % 2 == 0 else "jazz"

        songs.append({
            "title": f"Song {i + 1}",
            "genre": genre,
            "mood": "happy",
            "energy": 0.8,
        })

    return songs


def run_experiment():
    results = []

    preferences = {"genre": PREFERRED_GENRE}

    print("\nEXPERIMENT 2: CATALOGUE COVERAGE")
    print("=" * 55)

    for test_name, matching_count in COVERAGE_TESTS.items():

        songs = create_catalogue(matching_count)

        recommendations = [
            (song, 0.8, "Synthetic test recommendation")
            for song in songs[:5]
        ]

        report = audit_recommendations(
            recommendations,
            songs,
            preferences,
        )

        coverage = matching_count / CATALOGUE_SIZE

        coverage_findings = [
            finding
            for finding in report["findings"]
            if finding["category"] == "catalogue_coverage"
        ]

        result = {
            "test": test_name,
            "matching_songs": matching_count,
            "catalogue_size": CATALOGUE_SIZE,
            "coverage": round(coverage, 3),
            "coverage_findings": coverage_findings,
            "warnings": report["warnings"],
            "status": report["status"],
        }

        results.append(result)

        print(f"\nTest {test_name}")
        print(f"Matching songs: {matching_count}/10")
        print(f"Coverage: {coverage:.0%}")
        print(f"Coverage findings: {coverage_findings}")
        print(f"Overall status: {report['status']}")

    output_path = Path("experiments/experiment_2_results.json")

    output_path.write_text(
        json.dumps(results, indent=4),
        encoding="utf-8",
    )

    print("\nResults saved to:", output_path)


if __name__ == "__main__":
    run_experiment()
