# 🎵 Music Recommender Simulation

## Project Summary

This project builds and examines **VibeMatch 1.0**, a small content-based music recommender. A listener states what they like, such as a favourite genre and mood, a target energy level, or a preferred tempo. VibeMatch then ranks the songs in a 10-song catalogue by how closely each one matches those preferences.

Each recommendation includes:
- a score between 0 and 1
- a plain-language explanation of which preferences matched, which did not, and by how much

VibeMatch is a **preference-based scoring system, not a trained machine-learning model**. It learns nothing from data or user behaviour. Every score comes from a fixed, transparent formula with hand-set weights. The project uses it to explore how recommenders turn data into rankings, how sensitive those rankings are to design choices, and where bias can creep in. It is intended for classroom exploration, not real users.

---

## How The System Works

### Song features

Each song in `data/songs.csv` is described by seven features:

| Feature | Type | What it means |
|---|---|---|
| **genre** | category | e.g. pop, lofi, rock, jazz |
| **mood** | category | e.g. happy, chill, intense, relaxed |
| **energy** | 0 to 1 | how intense or active the song feels |
| **tempo_bpm** | beats per minute | how fast the song is |
| **valence** | 0 to 1 | how positive or upbeat the song sounds |
| **danceability** | 0 to 1 | how suitable the song is for dancing |
| **acousticness** | 0 to 1 | how acoustic (vs. electronic) the song is |

### User preferences

A user profile can specify any of the following:
- a favourite **genre**
- a favourite **mood**
- a **target value** for energy, tempo, valence, danceability or acousticness

The original `UserProfile` takes four values: genre, mood, target energy, and a yes/no `likes_acoustic` flag. Optional target fields for tempo, valence, danceability and acousticness were added without breaking that original form.

### Scoring each song

For every preference the user gave, VibeMatch measures how similar the song is, from 0 (no match) to 1 (perfect match):

- **Genre and mood** are exact matches. A match scores 1 and a mismatch scores 0. Capital letters and extra spaces are ignored, but there is no partial credit, so "indie pop" does not count as "pop".
- **Energy, valence, danceability and acousticness** score `1 − |song value − target|`, never going below 0. A song exactly on target scores 1, and one a full point away scores 0.
- **Tempo** scores `1 − |song tempo − target tempo| / 200`, never going below 0. A song 200 BPM or more from the target scores 0.

Each feature's similarity is multiplied by its **weight**. All weights start equal at 1.0 and live in one configuration table, `FEATURE_WEIGHTS`. The song's final score is the **weighted average** of the features the user specified:

```
score = sum(weight × similarity) / sum(weight)     (over specified features only)
```

Because each similarity is between 0 and 1, every score is also between 0 and 1.

### Unspecified preferences

If the user doesn't state a preference for a feature, that feature is **left out of the calculation entirely**: it adds nothing to the top or bottom of the average. A user who only cares about genre and energy is never penalised for a song's tempo or danceability.

- **Acousticness:**
  - `likes_acoustic=True` means a target acousticness of 1.0.
  - `likes_acoustic=False` means *no acousticness preference*, not a dislike.
  - To ask for low acousticness, set `target_acousticness=0.0`. An explicit target always overrides the yes/no flag.
- **No preferences at all:** every song scores 0.0, and the explanation says so.

### Choosing recommendations

Every song is scored and sorted from highest to lowest. Ties go to the song with the lower ID, so results are always repeatable. The top *k* songs (5 by default) are returned, each with its score and explanation.

### Input validation

Out-of-range or malformed preferences raise a clear `ValueError` instead of being silently corrected. Examples are an energy of 1.5, a negative tempo, or a word where a number is expected.

### Design

The function-based interface (`load_songs`, `score_song`, `recommend_songs`) and the object-based interface (`Song`, `UserProfile`, `Recommender`) share one scoring routine, so they always give the same results.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
   ```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Actual output of `python -m src.main` using the default profile (genre pop, mood happy, energy 0.8) and equal weights:

```
Loading songs from data/songs.csv...

Top recommendations:

Sunrise City - Score: 0.99
Because: genre match: pop = pop (similarity 1.00); mood match: happy = happy (similarity 1.00); energy 0.82 vs target 0.80 (similarity 0.98)

Rooftop Lights - Score: 0.65
Because: genre mismatch: indie pop vs preferred pop (similarity 0.00); mood match: happy = happy (similarity 1.00); energy 0.76 vs target 0.80 (similarity 0.96)

Gym Hero - Score: 0.62
Because: genre match: pop = pop (similarity 1.00); mood mismatch: intense vs preferred happy (similarity 0.00); energy 0.93 vs target 0.80 (similarity 0.87)

Night Drive Loop - Score: 0.32
Because: genre mismatch: synthwave vs preferred pop (similarity 0.00); mood mismatch: moody vs preferred happy (similarity 0.00); energy 0.75 vs target 0.80 (similarity 0.95)

Storm Runner - Score: 0.30
Because: genre mismatch: rock vs preferred pop (similarity 0.00); mood mismatch: intense vs preferred happy (similarity 0.00); energy 0.91 vs target 0.80 (similarity 0.89)
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

All results below are **actual outputs** of the implementation, with *k* = 5 and scores rounded to two decimals. Weight changes were applied only in memory during an interactive session, using `unittest.mock.patch.dict`. No project files were changed, and the original weights were restored automatically.

### Experiment 1: Three user profiles (equal weights)

| Rank | Pop/Happy, energy 0.80 | Lo-fi/Chill, energy 0.35 | Rock/Intense, energy 0.90 |
|---|---|---|---|
| 1 | Sunrise City 0.99 | Library Rain 1.00 | Storm Runner 1.00 |
| 2 | Rooftop Lights 0.65 | Midnight Coding 0.98 | Gym Hero 0.66 |
| 3 | Gym Hero 0.62 | Focus Flow 0.65 | Sunrise City 0.31 |
| 4 | Night Drive Loop 0.32 | Spacewalk Thoughts 0.64 | Rooftop Lights 0.29 |
| 5 | Storm Runner 0.30 | Coffee Shop Stories 0.33 | Night Drive Loop 0.28 |

**Observed:**
- In every profile, the top result matched all three stated preferences and scored 0.99 or 1.00.
- Lo-fi/Chill had the most strong matches. Two songs matched both genre and mood, and two more matched one of them.
- Rock/Intense dropped off sharply after the first result. Storm Runner is the only rock song. Gym Hero came second (0.66) because its mood ("intense") matched and its energy (0.93) was close to the 0.90 target, even though its genre (pop) did not match. Positions 3 to 5 matched neither genre nor mood and were ranked by energy alone.
- In the Pop/Happy run, Rooftop Lights ("indie pop") got no genre credit even though its energy (0.76) is close to Sunrise City's (0.82).

### Experiment 2: Feature weights (Lo-fi/Chill profile)

Each variant raises one weight to 3.0 and leaves the others at 1.0.

| Rank | Equal weights | Genre ×3 | Mood ×3 | Energy ×3 |
|---|---|---|---|---|
| 1 | Library Rain 1.00 | Library Rain 1.00 | Library Rain 1.00 | Library Rain 1.00 |
| 2 | Midnight Coding 0.98 | Midnight Coding 0.99 | Midnight Coding 0.99 | Midnight Coding 0.96 |
| 3 | Focus Flow 0.65 | Focus Flow 0.79 | **Spacewalk Thoughts 0.79** | Focus Flow 0.77 |
| 4 | Spacewalk Thoughts 0.64 | Spacewalk Thoughts 0.39 | **Focus Flow 0.39** | Spacewalk Thoughts 0.76 |
| 5 | Coffee Shop Stories 0.33 | Coffee Shop Stories 0.20 | Coffee Shop Stories 0.20 | Coffee Shop Stories 0.59 |

**Observed:**
- **Top two unchanged.** Library Rain and Midnight Coding stayed first and second under every weighting.
- **Genre ×3** favoured Focus Flow, which matches the genre (lofi) but not the mood. Its near-tie with Spacewalk Thoughts at baseline (0.65 vs 0.64) became a 0.40 gap between the two songs (0.79 vs 0.39).
- **Mood ×3** reversed positions 3 and 4, favouring Spacewalk Thoughts, which matches the mood (chill) but not the genre. This was the only variant that changed the order of the top five.
- **Energy ×3** kept the baseline order but compressed the scores. Coffee Shop Stories, which matches neither genre nor mood but has energy 0.37, rose from 0.33 to 0.59.
- **Largest change.** The largest change in any individual song's score from the equal-weight baseline was about 0.26. Coffee Shop Stories went from 0.33 to 0.59 under energy ×3, and Spacewalk Thoughts from 0.64 to 0.39 under genre ×3.
- **Explanations don't show weights.** The explanation text lists each feature's similarity but not its weight, so it looked the same in every variant even when scores changed.

### Automated tests

All 41 pytest tests pass. They check that the scoring rules are implemented correctly, covering:
- the formulas and the 0 to 1 bounds
- exclusion of unspecified features
- the acousticness rules
- input validation
- tie-breaking
- agreement between the two interfaces

They do not measure recommendation quality.

---

## Limitations and Risks

- **Tiny, uneven catalogue.** There are only 10 songs.
  - Lofi has 3 songs and pop has 2. Rock, ambient, jazz, synthwave and indie pop have one each.
  - Many genres (hip-hop, country, classical and others) and moods (sad, angry and others) are absent.
  - As the Rock/Intense run showed, users with under-represented tastes run out of good matches quickly.
- **All-or-nothing categorical matching.** Genre and mood give no partial credit, so closely related labels ("indie pop" vs "pop") are treated as completely different. Each song also has only one genre and one mood label, and those labels are subjective.
- **Hand-set feature weights.** The weights are a design choice, not learned from listeners. The experiments showed that changing a single weight can reorder mid-ranked songs and change an individual score by about 0.26. Equal weights are a starting assumption, not a validated setting. The 200 BPM tempo scale is likewise an assumption.
- **Explanations omit weights.** Users see each feature's similarity but not how much each feature counted.
- **The acousticness flag can be misread.** `likes_acoustic=False` means "no preference", so a user who dislikes acoustic music must know to set `target_acousticness=0.0`.
- **Missing signals.** There are no lyrics, language, artist, era, popularity, listening context or user feedback, and no learning over time.
- **No independent evaluation.**
  - We collected no user feedback or independent relevance judgements.
  - We calculated no formal metrics (Precision@K, Recall@K, NDCG@K).
  - Judgements about whether results are "good" are our own qualitative impressions.
  - Scores are system outputs, not measures of quality.

These are explored further in the model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Building VibeMatch showed me that a recommender, even a simple one, is a series of human decisions expressed as math. I had to decide which features count, how "closeness" is measured, how much each feature matters, and what to do when a preference is missing. The formula is short and every score is explainable, yet I found that the output still feels authoritative. The weight experiments made the trade-offs concrete for me. Tripling the genre weight or the mood weight determined which of two nearly tied songs came out well ahead, and tripling energy lifted a jazz song that matched neither genre nor mood from 0.33 to 0.59. I came away seeing that there is no single "correct" ranking, only rankings that follow from the choices I made.

The project also showed me how bias can enter without anyone intending it. Because the catalogue has three lofi songs but only one rock song, a lofi listener gets several strong matches while a rock listener gets one, followed by songs that match neither their genre nor their mood. Exact-match genre labels add to this by treating related styles as unrelated. I now see how, in a real system, gaps in the catalogue, the way genres are labelled, and the choice of weights could quietly steer some listeners toward the mainstream. In my view, transparent explanations, and evaluating with independent relevance judgements rather than designer intuition, are important ways to notice and correct that.
