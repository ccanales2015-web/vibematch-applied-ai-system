
"""
Command line runner for the VibeMatch recommendation system.

Generates music recommendations and evaluates their reliability.
"""

from src.recommender import load_songs, recommend_songs
from src.auditor import audit_recommendations


def print_audit_report(report: dict) -> None:
    """Display the recommendation reliability audit."""

    print("\n" + "-" * 40)
    print("VIBEMATCH RELIABILITY AUDIT")
    print("-" * 40)

    print(f"Recommendations evaluated: {report['recommendation_count']}")
    print(f"Average match score: {report['average_match_score']:.3f}")

    print(f"Weak matches: {len(report['weak_matches'])}")

    if report["genre_coverage"] is not None:
        print(
            "Preferred-genre catalogue share: "
            f"{report['genre_coverage']:.0%}"
        )

    print(
        "Distinct-genre ratio: "
        f"{report['genre_diversity']:.0%}"
    )

    if report["weak_matches"]:
        print("\nWeak recommendations:")
        for title in report["weak_matches"]:
            print(f"  - {title}")

    if report["warnings"]:
        print("\nWARNINGS:")
        for warning in report["warnings"]:
            print(f"  - {warning}")
    else:
        print("\nNo reliability warnings detected.")

    print(f"\nOverall status: {report['status'].upper()}")
    print("-" * 40)


def main() -> None:
    songs = load_songs("data/songs.csv")

    # Starter example profile
    user_prefs = {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.8,
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print("\nTop recommendations:\n")

    for song, score, explanation in recommendations:
        print(f"{song['title']} - Score: {score:.2f}")
        print(f"Because: {explanation}")
        print()

    # Evaluate recommendation reliability
    report = audit_recommendations(
        recommendations,
        songs,
        user_prefs,
    )

    print_audit_report(report)


if __name__ == "__main__":
    main()
