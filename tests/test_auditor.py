
import pytest

from src.auditor import audit_recommendations


def make_song(title, genre):
    return {"title": title, "genre": genre}


def make_recommendation(title, genre, score):
    return (make_song(title, genre), score, "Test explanation")


def test_auditor_calculates_average_score():
    songs = [make_song(str(i), "pop") for i in range(10)]
    recommendations = [
        make_recommendation("A", "pop", 0.9),
        make_recommendation("B", "rock", 0.7),
    ]

    report = audit_recommendations(
        recommendations, songs, {"genre": "pop"}
    )

    assert report["average_match_score"] == 0.8
    assert report["recommendation_count"] == 2


def test_auditor_identifies_weak_matches():
    songs = [make_song(str(i), "pop") for i in range(10)]
    recommendations = [
        make_recommendation("Strong", "pop", 0.9),
        make_recommendation("Weak", "rock", 0.3),
    ]

    report = audit_recommendations(
        recommendations, songs, {"genre": "pop"}
    )

    assert report["weak_matches"] == ["Weak"]
    assert report["status"] == "warning"


def test_score_at_threshold_is_not_weak():
    songs = [make_song(str(i), "pop") for i in range(10)]
    recommendations = [
        make_recommendation("Boundary", "pop", 0.5),
    ]

    report = audit_recommendations(
        recommendations, songs, {"genre": "pop"}
    )

    assert report["weak_matches"] == []


def test_missing_preferred_genre_is_flagged():
    songs = [make_song(str(i), "rock") for i in range(10)]
    recommendations = [
        make_recommendation("Rock Song", "rock", 0.9),
    ]

    report = audit_recommendations(
        recommendations, songs, {"genre": "pop"}
    )

    assert report["genre_coverage"] == 0.0
    assert report["status"] == "warning"


def test_genre_diversity_calculation():
    songs = [make_song(str(i), "pop") for i in range(10)]
    recommendations = [
        make_recommendation("A", "pop", 0.9),
        make_recommendation("B", "rock", 0.8),
    ]

    report = audit_recommendations(
        recommendations, songs, {"genre": "pop"}
    )

    assert report["genre_diversity"] == 1.0


def test_empty_recommendations_are_not_reported_as_passed():
    songs = [make_song(str(i), "pop") for i in range(10)]

    report = audit_recommendations([], songs, {"genre": "pop"})

    assert report["status"] == "warning"
    assert report["warnings"]


def test_invalid_recommendation_score_is_rejected():
    songs = [make_song(str(i), "pop") for i in range(10)]
    recommendations = [
        make_recommendation("Invalid", "pop", 1.5),
    ]

    with pytest.raises(ValueError):
        audit_recommendations(
            recommendations, songs, {"genre": "pop"}
        )


def test_limited_coverage_info_does_not_cause_warning():
    songs = [
        make_song("Pop Song", "pop")
    ] + [
        make_song(str(i), "rock") for i in range(9)
    ]

    recommendations = [
        make_recommendation(str(i), "rock", 0.8)
        for i in range(5)
    ]

    report = audit_recommendations(
        recommendations, songs, {"genre": "pop"}
    )

    assert report["genre_coverage"] == 0.1
    assert report["status"] == "passed"
    assert report["warnings"] == []

    assert any(
        finding["category"] == "catalogue_coverage"
        and finding["severity"] == "info"
        for finding in report["findings"]
    )


def test_low_diversity_info_does_not_cause_warning():
    songs = [make_song(str(i), "pop") for i in range(10)]

    recommendations = [
        make_recommendation("A", "pop", 0.9),
        make_recommendation("B", "pop", 0.8),
    ]

    report = audit_recommendations(
        recommendations, songs, {"genre": "pop"}
    )

    assert report["genre_diversity"] == 0.5
    assert report["status"] == "passed"
    assert report["warnings"] == []

    assert any(
        finding["category"] == "diversity"
        and finding["severity"] == "info"
        for finding in report["findings"]
    )
