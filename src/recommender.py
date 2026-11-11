import csv
import math
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict

# ---------------------------------------------------------------------------
# Scoring configuration
# ---------------------------------------------------------------------------

# Relative importance of each feature. Only features the user explicitly
# supplies contribute; the final score is a weighted average over those.
FEATURE_WEIGHTS: Dict[str, float] = {
    "genre": 1.0,
    "mood": 1.0,
    "energy": 1.0,
    "tempo_bpm": 1.0,
    "valence": 1.0,
    "danceability": 1.0,
    "acousticness": 1.0,
}

CATEGORICAL_FEATURES: Tuple[str, ...] = ("genre", "mood")
UNIT_INTERVAL_FEATURES: Tuple[str, ...] = ("energy", "valence", "danceability", "acousticness")
TEMPO_FEATURE = "tempo_bpm"

# A tempo difference of this many BPM (or more) yields a similarity of 0.
TEMPO_RANGE_BPM = 200.0

NO_PREFERENCES_EXPLANATION = "No preferences specified, so no features were compared (score 0.00)"


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py

    The first four fields are the original starter interface. The optional
    target_* fields default to None, meaning "no preference" for that feature.

    Acousticness: likes_acoustic=True means a target acousticness of 1.0;
    likes_acoustic=False means no acousticness preference. An explicit
    target_acousticness always overrides the Boolean.
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    target_tempo_bpm: Optional[float] = None
    target_valence: Optional[float] = None
    target_danceability: Optional[float] = None
    target_acousticness: Optional[float] = None

    def __post_init__(self) -> None:
        # Fail fast on invalid values (raises ValueError).
        _resolve_preferences(self.to_prefs())

    def to_prefs(self) -> Dict[str, Any]:
        """Converts this profile into the preference dict used by score_song."""
        return {
            "genre": self.favorite_genre,
            "mood": self.favorite_mood,
            "energy": self.target_energy,
            "tempo_bpm": self.target_tempo_bpm,
            "valence": self.target_valence,
            "danceability": self.target_danceability,
            "acousticness": self.target_acousticness,
            "likes_acoustic": self.likes_acoustic,
        }


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py

    Delegates to the same scoring algorithm as the functional API.
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        _validate_k(k)
        prefs = _resolve_preferences(user.to_prefs())
        ranked = _rank(prefs, [asdict(song) for song in self.songs])
        return [self.songs[index] for index, _, _ in ranked[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        _, reasons = score_song(user.to_prefs(), asdict(song))
        return "; ".join(reasons)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    print(f"Loading songs from {csv_path}...")
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            songs.append({
                "id": int(row["id"]),
                "title": row["title"],
                "artist": row["artist"],
                "genre": row["genre"],
                "mood": row["mood"],
                "energy": float(row["energy"]),
                "tempo_bpm": float(row["tempo_bpm"]),
                "valence": float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })
    return songs


# ---------------------------------------------------------------------------
# Preference validation
# ---------------------------------------------------------------------------

def _validate_k(k: int) -> None:
    if isinstance(k, bool) or not isinstance(k, int) or k < 0:
        raise ValueError(f"k must be a nonnegative integer, got {k!r}")


def _validate_number(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Preference '{name}' must be a number, got {value!r}")
    if math.isnan(value) or math.isinf(value):
        raise ValueError(f"Preference '{name}' must be a finite number, got {value!r}")
    return float(value)


def _normalize_category(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Preference '{name}' must be a non-empty string, got {value!r}")
    return value.strip().lower()


def _resolve_preferences(user_prefs: Dict) -> Dict[str, Any]:
    """
    Validates user preferences and returns only the explicitly supplied ones,
    normalized for scoring. Missing keys and None values mean "unspecified".
    Raises ValueError for invalid values.
    """
    resolved: Dict[str, Any] = {}

    for feature in CATEGORICAL_FEATURES:
        value = user_prefs.get(feature)
        if value is not None:
            resolved[feature] = _normalize_category(feature, value)

    for feature in UNIT_INTERVAL_FEATURES:
        value = user_prefs.get(feature)
        if value is not None:
            number = _validate_number(feature, value)
            if not 0.0 <= number <= 1.0:
                raise ValueError(f"Preference '{feature}' must be between 0 and 1, got {value!r}")
            resolved[feature] = number

    tempo = user_prefs.get(TEMPO_FEATURE)
    if tempo is not None:
        number = _validate_number(TEMPO_FEATURE, tempo)
        if number < 0:
            raise ValueError(f"Preference '{TEMPO_FEATURE}' must be nonnegative, got {tempo!r}")
        resolved[TEMPO_FEATURE] = number

    likes_acoustic = user_prefs.get("likes_acoustic")
    if likes_acoustic is not None and not isinstance(likes_acoustic, bool):
        raise ValueError(f"Preference 'likes_acoustic' must be True or False, got {likes_acoustic!r}")
    # An explicit acousticness target overrides the Boolean; False means unspecified.
    if "acousticness" not in resolved and likes_acoustic is True:
        resolved["acousticness"] = 1.0

    return resolved


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _compare_feature(feature: str, target: Any, song: Dict) -> Tuple[float, str]:
    """Returns (similarity in [0, 1], human-readable reason) for one feature."""
    if feature in CATEGORICAL_FEATURES:
        actual = str(song[feature]).strip().lower()
        if actual == target:
            return 1.0, f"{feature} match: {actual} = {target} (similarity 1.00)"
        return 0.0, f"{feature} mismatch: {actual} vs preferred {target} (similarity 0.00)"

    actual = float(song[feature])
    if feature == TEMPO_FEATURE:
        similarity = max(0.0, 1.0 - abs(actual - target) / TEMPO_RANGE_BPM)
        return similarity, (
            f"tempo {actual:g} BPM vs target {target:g} BPM (similarity {similarity:.2f})"
        )

    similarity = max(0.0, 1.0 - abs(actual - target))
    return similarity, f"{feature} {actual:.2f} vs target {target:.2f} (similarity {similarity:.2f})"


def _score_resolved(prefs: Dict[str, Any], song: Dict) -> Tuple[float, List[str]]:
    """Core scoring algorithm, shared by the functional and OOP interfaces."""
    weighted_sum = 0.0
    total_weight = 0.0
    reasons: List[str] = []

    for feature, weight in FEATURE_WEIGHTS.items():
        if feature not in prefs:
            continue  # Unspecified: excluded from numerator and denominator.
        similarity, reason = _compare_feature(feature, prefs[feature], song)
        weighted_sum += weight * similarity
        total_weight += weight
        reasons.append(reason)

    if total_weight <= 0:
        return 0.0, [NO_PREFERENCES_EXPLANATION]
    return weighted_sum / total_weight, reasons


def _rank(prefs: Dict[str, Any], songs: List[Dict]) -> List[Tuple[int, float, List[str]]]:
    """Scores every song and returns (index, score, reasons) sorted by score desc, then id asc."""
    results = []
    for index, song in enumerate(songs):
        score, reasons = _score_resolved(prefs, song)
        results.append((index, score, reasons))
    results.sort(key=lambda r: (-r[1], songs[r[0]]["id"]))
    return results


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Required by recommend_songs() and src/main.py

    Returns (score, reasons), where score is a weighted average in [0, 1]
    over only the explicitly supplied preferences.
    """
    return _score_resolved(_resolve_preferences(user_prefs), song)


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py

    Returns up to k (song_dict, score, explanation) tuples, highest score first.
    """
    _validate_k(k)
    prefs = _resolve_preferences(user_prefs)
    ranked = _rank(prefs, songs)
    return [(songs[index], score, "; ".join(reasons)) for index, score, reasons in ranked[:k]]
