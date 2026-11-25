# ðŸŽµ VibeMatch 1.0 --- Music Recommender Simulation

## Project Summary

This project builds and examines **VibeMatch 1.0**, a small
content-based music recommender. A listener states what they like, such
as a favourite genre and mood, a target energy level, or a preferred
tempo. VibeMatch ranks the songs in a 10-song catalogue by how closely
each one matches those preferences.

Each recommendation includes: - a score between 0 and 1 - a
plain-language explanation of which preferences matched, which did not,
and by how much

VibeMatch is a **preference-based scoring system, not a trained
machine-learning model**. It learns nothing from data or user behaviour.
Every score comes from a fixed, transparent formula with hand-set
weights. The project uses it to explore how recommenders turn data into
rankings, how sensitive those rankings are to design choices, and where
bias can creep in. It is intended for classroom exploration, not real
users.

The project was extended with a separate **reliability auditor**. The
auditor evaluates recommendation outputs and catalogue characteristics,
reports findings, and does not change the recommender's ranking
algorithm.

------------------------------------------------------------------------

## How the System Works

### Song features

Each song in `data/songs.csv` is described by seven features:

  -----------------------------------------------------------------------
  Feature                 Type                    What it means
  ----------------------- ----------------------- -----------------------
  **genre**               category                e.g.Â pop, lofi, rock,
                                                  jazz

  **mood**                category                e.g.Â happy, chill,
                                                  intense, relaxed

  **energy**              0 to 1                  how intense or active
                                                  the song feels

  **tempo_bpm**           beats per minute        how fast the song is

  **valence**             0 to 1                  how positive or upbeat
                                                  the song sounds

  **danceability**        0 to 1                  how suitable the song
                                                  is for dancing

  **acousticness**        0 to 1                  how acoustic
                                                  (vs.Â electronic) the
                                                  song is
  -----------------------------------------------------------------------

### User preferences

A user profile can specify any of the following: - a favourite
**genre** - a favourite **mood** - a **target value** for energy, tempo,
valence, danceability or acousticness

The original `UserProfile` takes four values: genre, mood, target
energy, and a yes/no `likes_acoustic` flag. Optional target fields for
tempo, valence, danceability and acousticness were added without
breaking that original form.

### Scoring each song

For every preference the user gave, VibeMatch measures how similar the
song is, from 0 (no match) to 1 (perfect match):

-   **Genre and mood** are exact matches. A match scores 1 and a
    mismatch scores 0. Capital letters and extra spaces are ignored, but
    there is no partial credit, so "indie pop" does not count as "pop".
-   **Energy, valence, danceability and acousticness** score
    `1 - |song value - target|`, never going below 0. A song exactly on
    target scores 1, and one a full point away scores 0.
-   **Tempo** scores `1 - |song tempo - target tempo| / 200`, never
    going below 0. A song 200 BPM or more from the target scores 0.

Each feature's similarity is multiplied by its **weight**. All weights
start equal at 1.0 and live in one configuration table,
`FEATURE_WEIGHTS`. The song's final score is the **weighted average** of
the features the user specified:

``` text
score = sum(weight * similarity) / sum(weight)     (over specified features only)
```

Because each similarity is between 0 and 1, every score is also between
0 and 1.

### Unspecified preferences

If the user doesn't state a preference for a feature, that feature is
**left out of the calculation entirely**: it adds nothing to the top or
bottom of the average. A user who only cares about genre and energy is
never penalised for a song's tempo or danceability.

-   **Acousticness:**
    -   `likes_acoustic=True` means a target acousticness of 1.0.
    -   `likes_acoustic=False` means *no acousticness preference*, not a
        dislike.
    -   To ask for low acousticness, set `target_acousticness=0.0`. An
        explicit target always overrides the yes/no flag.
-   **No preferences at all:** every song scores 0.0, and the
    explanation says so.

### Choosing recommendations

Every song is scored and sorted from highest to lowest. Ties go to the
song with the lower ID, so results are always repeatable. The top *k*
songs (5 by default) are returned, each with its score and explanation.

### Input validation

Out-of-range or malformed preferences raise a clear `ValueError` instead
of being silently corrected. Examples are an energy of 1.5, a negative
tempo, or a word where a number is expected.

### Design

The function-based interface (`load_songs`, `score_song`,
`recommend_songs`) and the object-based interface (`Song`,
`UserProfile`, `Recommender`) share one scoring routine, so they always
give the same results.

------------------------------------------------------------------------

## Architecture

The architecture separates recommendation generation from
post-recommendation reliability auditing. The recommender produces
ranked recommendations; the auditor evaluates those recommendations
alongside the catalogue and user preferences. The auditor reports match
strength, catalogue coverage, genre diversity, findings, warnings, and
an overall status. It does not modify recommendation scores or ranking.

![VibeMatch architecture](assets/architecture.svg)

Editable Mermaid source:
[`diagrams/architecture.mmd`](diagrams/architecture.mmd).

Key components:

-   `src/main.py` --- command-line entry point; loads the catalogue,
    runs the recommender, and displays the recommendations and audit
    report.
-   `src/recommender.py` --- loads songs, scores candidates, and returns
    ranked recommendations.
-   `src/auditor.py` --- independently evaluates the recommendation
    output and catalogue coverage.
-   `data/songs.csv` --- the ten-song example catalogue.
-   `tests/` --- automated tests for recommender and auditor behavior.
-   `experiments/` --- scripts and JSON outputs for the three
    reliability experiments.

------------------------------------------------------------------------

## Reliability Auditor

The reliability auditor evaluates recommendation outputs independently
of the recommendation algorithm. It examines:

1.  **Match strength:** identifies recommendations with scores below the
    configured weak-match threshold.
2.  **Catalogue coverage:** checks how much of the catalogue represents
    the user's preferred genre.
3.  **Genre diversity:** describes the number of represented genres
    relative to the number of recommendations.

The current design thresholds are: - Weak recommendation: score below
`0.50`. - Limited catalogue coverage: preferred genre represents less
than `20%` of the catalogue.

These are explicit design choices, not thresholds learned from listener
data. A finding marked `info` is reported but does not independently
cause the overall audit status to become `warning`. Warnings do affect
the overall status.

The auditor is a reporting layer. It does not alter recommendation
rankings, scores, or the underlying scoring formula.

------------------------------------------------------------------------

## Getting Started

### Requirements

-   Python 3.10 or later is recommended.
-   Dependencies are listed in `requirements.txt`.

### Setup

1.  Create a virtual environment (optional but recommended):

    ``` bash
    python -m venv .venv
    ```

2.  Activate it:

    **Windows PowerShell**

    ``` powershell
    .\.venv\Scripts\Activate.ps1
    ```

    **macOS / Linux**

    ``` bash
    source .venv/bin/activate
    ```

3.  Install dependencies:

    ``` bash
    python -m pip install -r requirements.txt
    ```

### Run the application

From the repository root:

``` bash
python -m src.main
```

The application loads `data/songs.csv`, generates the default
recommendations, and prints the reliability audit.

### Run the tests

From the repository root:

``` bash
python -m pytest -q
```

The current test suite contains **50 tests**: 41 original recommender
tests and 9 auditor tests.

### Run the experiments

Run each experiment from the repository root:

``` bash
python -m experiments.experiment_1
python -m experiments.experiment_2
python -m experiments.experiment_3
```

Each script writes its results to a corresponding JSON file in
`experiments/`.

------------------------------------------------------------------------

## Sample Recommendation and Audit Output

The following is the observed output for the default profile (genre
`pop`, mood `happy`, energy `0.8`). Scores are rounded to two decimal
places.

``` text
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


----------------------------------------
VIBEMATCH RELIABILITY AUDIT
----------------------------------------
Recommendations evaluated: 5
Average match score: 0.577
Weak matches: 2
Preferred-genre catalogue share: 20%
Distinct-genre ratio: 80%

Weak recommendations:
  - Night Drive Loop
  - Storm Runner

WARNINGS:
  - One or more recommendations have weak match scores.

Overall status: WARNING
----------------------------------------
```

------------------------------------------------------------------------

## Original Recommender Experiments

The following experiments examine the original recommendation scoring
behavior. They are distinct from the later reliability-auditor
experiments documented below.

All results in this section are from the original recommender
experiments, with *k* = 5 and scores rounded to two decimals. Weight
changes were applied only in memory during an interactive session, using
`unittest.mock.patch.dict`. No project files were changed, and the
original weights were restored automatically.

### Experiment 1: Three user profiles (equal weights)

  -----------------------------------------------------------------------
  Rank              Pop/Happy, energy Lo-fi/Chill,      Rock/Intense,
                    0.80              energy 0.35       energy 0.90
  ----------------- ----------------- ----------------- -----------------
  1                 Sunrise City 0.99 Library Rain 1.00 Storm Runner 1.00

  2                 Rooftop Lights    Midnight Coding   Gym Hero 0.66
                    0.65              0.98

  3                 Gym Hero 0.62     Focus Flow 0.65   Sunrise City 0.31

  4                 Night Drive Loop  Spacewalk         Rooftop Lights
                    0.32              Thoughts 0.64     0.29

  5                 Storm Runner 0.30 Coffee Shop       Night Drive Loop
                                      Stories 0.33      0.28
  -----------------------------------------------------------------------

**Observed:** - In every profile, the top result matched all three
stated preferences and scored 0.99 or 1.00. - Lo-fi/Chill had the most
strong matches. Two songs matched both genre and mood, and two more
matched one of them. - Rock/Intense dropped off sharply after the first
result. Storm Runner is the only rock song. Gym Hero came second (0.66)
because its mood (`intense`) matched and its energy (0.93) was close to
the 0.90 target, even though its genre (`pop`) did not match. Positions
3 to 5 matched neither genre nor mood and were ranked by energy alone. -
In the Pop/Happy run, Rooftop Lights (`indie pop`) got no genre credit
even though its energy (0.76) is close to Sunrise City's (0.82).

### Experiment 2: Feature weights (Lo-fi/Chill profile)

Each variant raises one weight to 3.0 and leaves the others at 1.0.

  --------------------------------------------------------------------------
  Rank           Equal weights  Genre Ã—3       Mood Ã—3        Energy Ã—3
  -------------- -------------- -------------- -------------- --------------
  1              Library Rain   Library Rain   Library Rain   Library Rain
                 1.00           1.00           1.00           1.00

  2              Midnight       Midnight       Midnight       Midnight
                 Coding 0.98    Coding 0.99    Coding 0.99    Coding 0.96

  3              Focus Flow     Focus Flow     **Spacewalk    Focus Flow
                 0.65           0.79           Thoughts       0.77
                                               0.79**

  4              Spacewalk      Spacewalk      **Focus Flow   Spacewalk
                 Thoughts 0.64  Thoughts 0.39  0.39**         Thoughts 0.76

  5              Coffee Shop    Coffee Shop    Coffee Shop    Coffee Shop
                 Stories 0.33   Stories 0.20   Stories 0.20   Stories 0.59
  --------------------------------------------------------------------------

**Observed:** - **Top two unchanged.** Library Rain and Midnight Coding
stayed first and second under every weighting. - **Genre Ã—3** favoured
Focus Flow, which matches the genre (`lofi`) but not the mood. Its
near-tie with Spacewalk Thoughts at baseline (0.65 vs 0.64) became a
0.40 gap between the two songs (0.79 vs 0.39). - **Mood Ã—3** reversed
positions 3 and 4, favouring Spacewalk Thoughts, which matches the mood
(`chill`) but not the genre. This was the only variant that changed the
order of the top five. - **Energy Ã—3** kept the baseline order but
compressed the scores. Coffee Shop Stories, which matches neither genre
nor mood but has energy 0.37, rose from 0.33 to 0.59. - **Largest
change.** The largest change in any individual song's score from the
equal-weight baseline was about 0.26. Coffee Shop Stories went from 0.33
to 0.59 under energy Ã—3, and Spacewalk Thoughts from 0.64 to 0.39 under
genre Ã—3. - **Explanations don't show weights.** The explanation text
lists each feature's similarity but not its weight, so it looked the
same in every variant even when scores changed.

------------------------------------------------------------------------

## Reliability Auditor Experiments

These three experiments evaluate the auditor and the repeatability of
the tested recommendation pipeline. Their results are stored in
`experiments/experiment_1_results.json`,
`experiments/experiment_2_results.json`, and
`experiments/experiment_3_results.json`.

### Experiment 1: Preference-profile evaluation

Three profiles were evaluated against the original ten-song catalogue.
Each requested five recommendations.

  -------------------------------------------------------------------------
  Profile          Average Weak matches        Genre        Genre Overall
                     score                  coverage    diversity status
  ----------- ------------ ------------ ------------ ------------ ---------
  Pop / Happy        0.577            2          20%          80% Warning
  / 0.80
  energy

  Lofi /             0.719            1          30%          60% Warning
  Chill /
  0.40 energy

  Classical /        0.245            5           0%          60% Warning
  Sad / 0.10
  energy
  -------------------------------------------------------------------------

All three profiles produced an overall warning status. The pop and lofi
profiles each contained at least one weak recommendation. The classical
profile had five weak recommendations and no catalogue representation
for the preferred genre.

The lofi profile produced the highest average score and highest
catalogue coverage. Genre, mood, and energy changed together across
profiles, so this experiment does not isolate the independent effect of
catalogue coverage.

### Experiment 2: Catalogue-coverage threshold

A synthetic catalogue of ten songs was used to test coverage behavior.

  Test     Matching songs   Coverage Finding                                 Overall status
  ------ ---------------- ---------- --------------------------------------- ----------------
  A                     0         0% Warning: no representation              Warning
  B                     1        10% Informational: limited representation   Passed
  C                     2        20% None                                    Passed
  D                     3        30% None                                    Passed

At zero coverage, the auditor warns that the preferred genre is absent.
At 10% coverage, it reports an informational finding without changing
the overall status to warning. At exactly 20% and above, no coverage
finding is generated.

Testing identified and corrected an issue where informational findings
also caused an overall warning status. Two regression tests verify that
informational coverage and diversity findings do not independently cause
a warning.

### Experiment 3: Recommendation consistency

The baseline Pop / Happy / 0.80 energy profile was executed ten
consecutive times against the same catalogue. All ten runs produced
identical recommendation ordering and corresponding audit results. The
experiment demonstrates repeatability for this tested configuration and
execution environment; it does not establish determinism across other
environments, datasets, or software configurations.

### Automated tests

The complete pytest suite passed **50 tests**: - 41 original recommender
tests. - 9 auditor tests, including regression tests for informational
finding classification.

The tests check implementation behavior. They do not establish that
recommendations are objectively relevant or satisfactory to listeners.

------------------------------------------------------------------------

## Limitations and Risks

-   **Tiny, uneven catalogue.** There are only 10 songs.
    -   Lofi has 3 songs and pop has 2. Rock, ambient, jazz, synthwave
        and indie pop have one each.
    -   Many genres (hip-hop, country, classical and others) and moods
        (sad, angry and others) are absent.
    -   As the Rock/Intense run showed, users with under-represented
        tastes run out of good matches quickly.
-   **All-or-nothing categorical matching.** Genre and mood give no
    partial credit, so closely related labels (`indie pop` vs.Â `pop`)
    are treated as completely different. Each song also has only one
    genre and one mood label, and those labels are subjective.
-   **Hand-set feature weights.** The weights are a design choice, not
    learned from listeners. The original experiments showed that
    changing a single weight can reorder mid-ranked songs and change an
    individual score by about 0.26. Equal weights are a starting
    assumption, not a validated setting. The 200 BPM tempo scale is
    likewise an assumption.
-   **Explanations omit weights.** Users see each feature's similarity
    but not how much each feature counted.
-   **The acousticness flag can be misread.** `likes_acoustic=False`
    means "no preference", so a user who dislikes acoustic music must
    know to set `target_acousticness=0.0`.
-   **Missing signals.** There are no lyrics, language, artist, era,
    popularity, listening context or user feedback, and no learning over
    time.
-   **No independent recommendation-quality evaluation.**
    -   We collected no user feedback or independent relevance
        judgements.
    -   We calculated no formal ranking metrics (Precision@K, Recall@K,
        NDCG@K).
    -   The auditor's thresholds are designer-selected, not calibrated
        against listener outcomes.
    -   The repeatability experiment covered one profile and one
        execution environment.
    -   Scores are system outputs, not measures of recommendation
        quality.

The auditor improves visibility into weak matches and catalogue
limitations, but it does not solve the underlying limitations of the
recommender or establish real-world recommendation quality.

------------------------------------------------------------------------

## Reflection

Building VibeMatch showed me that a recommender, even a simple one, is a
series of human decisions expressed as math. I had to decide which
features count, how "closeness" is measured, how much each feature
matters, and what to do when a preference is missing. The formula is
short and every score is explainable, yet I found that the output still
feels authoritative. The weight experiments made the trade-offs concrete
for me. Tripling the genre weight or the mood weight determined which of
two nearly tied songs came out well ahead, and tripling energy lifted a
jazz song that matched neither genre nor mood from 0.33 to 0.59. I came
away seeing that there is no single "correct" ranking, only rankings
that follow from the choices I made.

The project also showed me how bias can enter without anyone intending
it. Because the catalogue has three lofi songs but only one rock song, a
lofi listener gets several strong matches while a rock listener gets
one, followed by songs that match neither their genre nor their mood.
Exact-match genre labels add to this by treating related styles as
unrelated. I now see how, in a real system, gaps in the catalogue, the
way genres are labelled, and the choice of weights could quietly steer
some listeners toward the mainstream. In my view, transparent
explanations, and evaluating with independent relevance judgements
rather than designer intuition, are important ways to notice and correct
that.

The reliability-auditor extension added another lesson: a system should
not only produce outputs, but also make important limitations visible.
The experiments helped verify that the auditor applies its defined
thresholds consistently and that the tested pipeline is repeatable under
one configuration. They did not prove that listeners would consider the
recommendations good. That distinction matters: implementation checks,
repeatability, and user-centered evaluation answer different questions.

------------------------------------------------------------------------

## AI Assistance

OpenAI ChatGPT (GPT-6) assisted with planning, implementation guidance,
experimental design, test development, documentation, and interpretation
of results for the reliability-auditor extension. The developer reviewed
and applied proposed changes, ran the application and experiments,
inspected outputs, and verified the implementation through the automated
test suite. Final implementation decisions and verification remained
under human control.
