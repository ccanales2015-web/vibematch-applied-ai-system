from src.recommender import Song, UserProfile, Recommender

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ---------------------------------------------------------------------------
# Extended tests
# ---------------------------------------------------------------------------

import math
from dataclasses import asdict
from pathlib import Path

import pytest

from src.recommender import load_songs, score_song, recommend_songs

DATA_PATH = str(Path(__file__).resolve().parent.parent / "data" / "songs.csv")


def song_dict(**overrides) -> dict:
    base = {
        "id": 1,
        "title": "Base",
        "artist": "Artist",
        "genre": "pop",
        "mood": "happy",
        "energy": 0.5,
        "tempo_bpm": 120.0,
        "valence": 0.5,
        "danceability": 0.5,
        "acousticness": 0.5,
    }
    base.update(overrides)
    return base


# --- UserProfile compatibility ---------------------------------------------

def test_user_profile_accepts_original_four_positional_args():
    user = UserProfile("pop", "happy", 0.8, False)
    assert user.favorite_genre == "pop"
    assert user.target_tempo_bpm is None
    assert user.target_valence is None
    assert user.target_danceability is None
    assert user.target_acousticness is None


def test_user_profile_rejects_invalid_values():
    with pytest.raises(ValueError):
        UserProfile("pop", "happy", 1.5, False)
    with pytest.raises(ValueError):
        UserProfile("pop", "happy", 0.5, False, target_tempo_bpm=-10)
    with pytest.raises(ValueError):
        UserProfile("pop", "happy", 0.5, "yes")


# --- load_songs ------------------------------------------------------------

def test_load_songs_parses_csv_types():
    songs = load_songs(DATA_PATH)
    assert len(songs) == 10
    first = songs[0]
    assert first["id"] == 1 and isinstance(first["id"], int)
    assert first["title"] == "Sunrise City"
    for key in ("energy", "tempo_bpm", "valence", "danceability", "acousticness"):
        assert isinstance(first[key], float)
    assert first["tempo_bpm"] == 118.0


# --- Similarity formulas ---------------------------------------------------

def test_numeric_similarity_formula():
    score, _ = score_song({"energy": 0.8}, song_dict(energy=0.5))
    assert score == pytest.approx(0.7)


def test_tempo_similarity_formula():
    score, _ = score_song({"tempo_bpm": 100}, song_dict(tempo_bpm=150))
    assert score == pytest.approx(0.75)


def test_tempo_similarity_floors_at_zero():
    score, _ = score_song({"tempo_bpm": 0}, song_dict(tempo_bpm=250))
    assert score == 0.0


def test_categorical_match_normalizes_case_and_whitespace():
    score, _ = score_song({"genre": "  POP ", "mood": "Happy"}, song_dict(genre="Pop", mood="happy "))
    assert score == 1.0


def test_categorical_match_is_exact_not_partial():
    score, _ = score_song({"genre": "pop"}, song_dict(genre="indie pop"))
    assert score == 0.0


# --- Normalization and unspecified features --------------------------------

def test_perfect_match_scores_one():
    song = song_dict()
    prefs = {k: song[k] for k in ("genre", "mood", "energy", "tempo_bpm", "valence", "danceability", "acousticness")}
    score, reasons = score_song(prefs, song)
    assert score == pytest.approx(1.0)
    assert len(reasons) == 7


def test_unspecified_features_excluded_from_score():
    # Only genre supplied: a genre match is a perfect score regardless of other features.
    score, reasons = score_song({"genre": "pop"}, song_dict(energy=0.0, tempo_bpm=300))
    assert score == 1.0
    assert len(reasons) == 1


def test_none_values_treated_as_unspecified():
    score, reasons = score_song({"genre": "pop", "energy": None, "tempo_bpm": None}, song_dict())
    assert score == 1.0
    assert len(reasons) == 1


def test_weighted_average_over_supplied_features():
    # genre match (1.0) + mood mismatch (0.0) + energy 0.8 vs 0.5 (0.7) => 1.7 / 3
    score, _ = score_song({"genre": "pop", "mood": "sad", "energy": 0.8}, song_dict(energy=0.5))
    assert score == pytest.approx(1.7 / 3)


def test_scores_bounded_between_zero_and_one():
    songs = load_songs(DATA_PATH)
    profiles = [
        {"genre": "pop", "mood": "happy", "energy": 0.8},
        {"genre": "metal", "mood": "angry", "energy": 0.0, "tempo_bpm": 0, "valence": 0.0,
         "danceability": 0.0, "acousticness": 1.0},
        {"tempo_bpm": 1000},
        {"energy": 1.0, "valence": 1.0, "danceability": 1.0, "acousticness": 0.0},
    ]
    for prefs in profiles:
        for song in songs:
            score, _ = score_song(prefs, song)
            assert 0.0 <= score <= 1.0


# --- No preferences --------------------------------------------------------

def test_no_preferences_returns_zero_with_explanation():
    score, reasons = score_song({}, song_dict())
    assert score == 0.0
    assert len(reasons) == 1 and "No preferences" in reasons[0]


def test_no_preferences_recommend_songs_does_not_crash():
    results = recommend_songs({}, [song_dict(id=2), song_dict(id=1)], k=2)
    assert [s["id"] for s, _, _ in results] == [1, 2]
    assert all(score == 0.0 for _, score, _ in results)


# --- Acousticness handling -------------------------------------------------

def test_likes_acoustic_true_targets_full_acousticness():
    score, reasons = score_song({"likes_acoustic": True}, song_dict(acousticness=0.2))
    assert score == pytest.approx(0.2)
    assert "acousticness" in reasons[0]


def test_likes_acoustic_false_leaves_acousticness_unspecified():
    score, reasons = score_song({"likes_acoustic": False}, song_dict(acousticness=0.9))
    assert score == 0.0
    assert "No preferences" in reasons[0]


def test_target_acousticness_overrides_boolean():
    score, _ = score_song({"likes_acoustic": True, "acousticness": 0.0}, song_dict(acousticness=0.2))
    assert score == pytest.approx(0.8)


def test_user_profile_acousticness_resolution():
    song = Song(**song_dict(acousticness=0.9))
    rec = Recommender([song])
    explanation = rec.explain_recommendation(UserProfile("pop", "happy", 0.5, False), song)
    assert "acousticness" not in explanation

    explanation = rec.explain_recommendation(
        UserProfile("pop", "happy", 0.5, True, target_acousticness=0.0), song
    )
    assert "acousticness 0.90 vs target 0.00" in explanation


# --- Validation ------------------------------------------------------------

@pytest.mark.parametrize("prefs", [
    {"energy": 1.5},
    {"valence": -0.1},
    {"danceability": 2},
    {"acousticness": 1.01},
    {"tempo_bpm": -1},
    {"energy": "high"},
    {"energy": True},
    {"energy": math.nan},
    {"tempo_bpm": math.inf},
    {"genre": ""},
    {"mood": 5},
    {"likes_acoustic": "yes"},
])
def test_invalid_preferences_raise_value_error(prefs):
    with pytest.raises(ValueError):
        score_song(prefs, song_dict())


def test_recommend_songs_validates_even_with_empty_catalog():
    with pytest.raises(ValueError):
        recommend_songs({"energy": 2.0}, [], k=5)


def test_negative_k_raises():
    with pytest.raises(ValueError):
        recommend_songs({"genre": "pop"}, [song_dict()], k=-1)


# --- Ranking ---------------------------------------------------------------

def test_recommend_songs_sorted_descending():
    songs = load_songs(DATA_PATH)
    results = recommend_songs({"genre": "pop", "mood": "happy", "energy": 0.8}, songs, k=10)
    scores = [score for _, score, _ in results]
    assert scores == sorted(scores, reverse=True)
    assert results[0][0]["title"] == "Sunrise City"


def test_ties_broken_by_song_id():
    songs = [song_dict(id=3), song_dict(id=1), song_dict(id=2)]
    results = recommend_songs({"genre": "pop"}, songs, k=3)
    assert [s["id"] for s, _, _ in results] == [1, 2, 3]


def test_k_limits_results_and_handles_k_larger_than_catalog():
    songs = load_songs(DATA_PATH)
    assert len(recommend_songs({"genre": "pop"}, songs, k=3)) == 3
    assert len(recommend_songs({"genre": "pop"}, songs, k=50)) == 10
    assert recommend_songs({"genre": "pop"}, songs, k=0) == []


def test_recommend_songs_returns_song_score_explanation_tuples():
    results = recommend_songs({"genre": "pop"}, [song_dict()], k=1)
    song, score, explanation = results[0]
    assert song["id"] == 1
    assert isinstance(score, float)
    assert isinstance(explanation, str) and explanation


# --- Explanations ----------------------------------------------------------

def test_explanation_shows_matches_and_mismatches():
    _, reasons = score_song(
        {"genre": "pop", "mood": "sad", "energy": 0.8, "tempo_bpm": 100},
        song_dict(energy=0.5, tempo_bpm=150),
    )
    text = "; ".join(reasons)
    assert "genre match" in text
    assert "mood mismatch" in text
    assert "energy 0.50 vs target 0.80 (similarity 0.70)" in text
    assert "tempo 150 BPM vs target 100 BPM (similarity 0.75)" in text


# --- OOP / functional consistency -----------------------------------------

def test_oop_and_functional_share_scoring():
    dict_songs = load_songs(DATA_PATH)
    song_objs = [Song(**s) for s in dict_songs]
    user = UserProfile("lofi", "chill", 0.4, True, target_tempo_bpm=80)

    oop_order = [s.id for s in Recommender(song_objs).recommend(user, k=10)]
    func_results = recommend_songs(user.to_prefs(), dict_songs, k=10)
    assert oop_order == [s["id"] for s, _, _ in func_results]

    rec = Recommender(song_objs)
    for song_obj, (song_d, _, explanation) in zip(rec.recommend(user, k=10), func_results):
        assert rec.explain_recommendation(user, song_obj) == explanation
        assert asdict(song_obj) == song_d
