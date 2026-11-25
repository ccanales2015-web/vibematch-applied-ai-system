
"""
Reliability auditing for the VibeMatch recommendation system.

The auditor evaluates recommendation outputs and catalogue coverage.
It does not modify the underlying recommendation algorithm.
"""

from collections import Counter
from typing import Any, Dict, List, Tuple


# Transparent thresholds; these are design choices, not learned values.
WEAK_MATCH_THRESHOLD = 0.50
LOW_COVERAGE_THRESHOLD = 0.20


def audit_recommendations(
    recommendations: List[Tuple[Dict[str, Any], float, str]],
    songs: List[Dict[str, Any]],
    preferences: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluate recommendation strength, catalogue coverage, and diversity.

    Returns a structured report containing findings and warnings.
    """

    if not isinstance(recommendations, list):
        raise ValueError("recommendations must be a list")

    if not isinstance(songs, list) or not songs:
        raise ValueError("songs must be a non-empty list")

    if not isinstance(preferences, dict):
        raise ValueError("preferences must be a dictionary")

    scores = []

    for item in recommendations:
        if not isinstance(item, tuple) or len(item) != 3:
            raise ValueError(
                "Each recommendation must be a (song, score, explanation) tuple"
            )

        song, score, explanation = item

        if not isinstance(song, dict):
            raise ValueError("Recommendation song must be a dictionary")

        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise ValueError("Recommendation score must be numeric")

        if not 0.0 <= score <= 1.0:
            raise ValueError("Recommendation score must be between 0 and 1")

        if not isinstance(explanation, str):
            raise ValueError("Recommendation explanation must be a string")

        scores.append(float(score))

    warnings = []
    findings = []

    if not recommendations:
        warnings.append(
            "No recommendations were generated; recommendation quality "
            "cannot be assessed."
        )
        findings.append({
            "category": "recommendation_availability",
            "severity": "warning",
            "details": "The recommendation list is empty.",
        })

    # 1. Match-strength analysis
    weak_matches = [
        item[0].get("title", "Unknown song")
        for item in recommendations
        if item[1] < WEAK_MATCH_THRESHOLD
    ]

    if weak_matches:
        warnings.append("One or more recommendations have weak match scores.")
        findings.append({
            "category": "match_strength",
            "severity": "warning",
            "details": weak_matches,
        })

    # 2. Catalogue coverage
    genre_counts = Counter(
        song.get("genre", "").strip().lower()
        for song in songs
        if isinstance(song.get("genre"), str)
    )

    preferred_genre = preferences.get("genre")

    genre_coverage = None

    if preferred_genre:
        normalized_genre = preferred_genre.strip().lower()
        matching_count = genre_counts.get(normalized_genre, 0)

        genre_coverage = matching_count / len(songs)

        if matching_count == 0:
            warnings.append(
                f"The catalogue contains no songs in the preferred genre: "
                f"{preferred_genre}."
            )
            findings.append({
                "category": "catalogue_coverage",
                "severity": "warning",
                "details": f"No catalogue representation for {preferred_genre}.",
            })
        elif genre_coverage < LOW_COVERAGE_THRESHOLD:
            warnings.append(
                f"The preferred genre '{preferred_genre}' has limited "
                "catalogue representation."
            )
            findings.append({
                "category": "catalogue_coverage",
                "severity": "info",
                "details": f"{matching_count} of {len(songs)} songs match.",
            })

    # 3. Recommendation diversity
    recommended_genres = {
        item[0].get("genre", "").strip().lower()
        for item in recommendations
        if isinstance(item[0].get("genre"), str)
    }

    diversity = (
        len(recommended_genres) / len(recommendations)
        if recommendations else 0.0
    )

    if len(recommended_genres) <= 1 and len(recommendations) > 1:
        warnings.append(
            "Recommendations contain only one represented genre."
        )
        findings.append({
            "category": "diversity",
            "severity": "info",
            "details": list(recommended_genres),
        })

    # 4. Summary statistics
    average_score = (
        sum(scores) / len(scores)
        if scores else 0.0
    )

    return {
        "recommendation_count": len(recommendations),
        "average_match_score": round(average_score, 3),
        "weak_matches": weak_matches,
        "genre_coverage": (
            round(genre_coverage, 3)
            if genre_coverage is not None else None
        ),
        "genre_diversity": round(diversity, 3),
        "findings": findings,
        "warnings": warnings,
        "status": "warning" if warnings else "passed",
    }
