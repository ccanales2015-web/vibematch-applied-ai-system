# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatch 1.0**: a content-based music recommender built for the
CodePath AI110 Module 3 simulation.

------------------------------------------------------------------------

## 2. Intended Use

**What it generates.** Given a listener's stated preferences, VibeMatch
ranks every song in a small catalogue and returns the top *k* (5 by
default). Each recommendation includes a score between 0 and 1 and a
plain-text explanation of how each preference compared with the song.

**Assumptions about the user.** - The user can state their taste
directly as a favourite genre, a favourite mood, and target values for
musical attributes such as energy or tempo. - Preferences are fixed for
a session. The system does not learn from listening history, skips, or
ratings. - Any preference the user leaves out is treated as "no opinion"
and has no effect on the score. - `likes_acoustic=True` is read as a
preference for highly acoustic music (target 1.0).
`likes_acoustic=False` is read as no acousticness preference, not as a
dislike. A user who wants low acousticness must set
`target_acousticness` explicitly.

**Audience.** This is a classroom exploration tool for learning how
recommenders turn data into rankings. It is **not** intended for real
users or production use. It has not been evaluated with real listeners,
and its catalogue is far too small for real-world use.

------------------------------------------------------------------------

## 3. How the Model Works

**Song features used.** Each song is described by seven features: -
**Genre** (for example pop, lofi or rock) - **Mood** (for example happy,
chill or intense) - **Energy**, **valence** (musical positivity),
**danceability** and **acousticness**, each measured from 0 to 1 -
**Tempo**, in beats per minute

**User preferences considered.** A user can give a favourite genre, a
favourite mood, and a target value for any of the five numeric features.
All of these are optional except in the original four-field profile
(genre, mood, energy and the acoustic yes/no flag).

**Turning preferences into a score.** 1. **Genre and mood** are either a
match or not. A match earns full credit (1) and a mismatch earns none
(0). Capital letters and extra spaces are ignored, but there is no
partial credit, so "indie pop" does not count as "pop". 2. **Energy,
valence, danceability and acousticness** earn credit based on how close
the song is to the target. A song exactly on target earns 1. Credit
falls off in a straight line as the gap grows and reaches 0 when the gap
is a full point (1.0). 3. **Tempo** works the same way, except credit
reaches 0 when the song is 200 BPM or more away from the target. 4. Each
feature's credit is multiplied by its **weight**. All weights start
equal at 1.0 and are stored in one adjustable table. 5. The final score
is the **weighted average over only the features the user actually
specified**. Unspecified features are left out entirely, so they cannot
help or hurt. This keeps every score between 0 and 1. 6. Songs are
sorted from highest to lowest score. Ties go to the song with the lower
ID, so results are always repeatable. 7. If the user specifies nothing
at all, every song scores 0 and the explanation says that no preferences
were given.

**Changes from the starter code.** In the starter, `recommend` returned
the first *k* songs unchanged, the explanation was a placeholder, and
the CSV loader returned nothing. VibeMatch adds: - real CSV loading -
the scoring rules above - per-feature explanations that show both
matches and mismatches - four optional target fields on the user
profile, while keeping the original four-argument profile working -
input validation that rejects out-of-range or malformed preferences with
a clear error instead of silently correcting them - a fix to the
`main.py` import, so `python -m src.main` runs from the project root

The object-based and function-based versions share one scoring routine,
so they always agree.

------------------------------------------------------------------------

## 4. Data

**Catalogue size.** The catalogue has 10 songs (`data/songs.csv`).

**Genres represented.**

  Genre                                       Songs
  ------------------------------------------- --------
  lofi                                        3
  pop                                         2
  rock, ambient, jazz, synthwave, indie pop   1 each

**Moods represented.**

  Mood                      Songs
  ------------------------- --------
  chill                     3
  happy                     2
  intense                   2
  relaxed, moody, focused   1 each

**Numeric ranges.** - Energy: 0.28 to 0.93 - Tempo: 60 to 152 BPM -
Acousticness: 0.05 to 0.92

**Changes to the data.** No songs were added, removed or edited. The
dataset is the unmodified starter file.

**Gaps in musical taste.** Many genres are absent, including hip-hop,
R&B, country, classical, metal, Latin, electronic/EDM, folk and
non-Western traditions. Several moods are also missing, such as sad,
angry and romantic. The data has no lyrics, language, vocals, era,
artist popularity or cultural context. Each song has exactly one genre
and one mood label, although real songs often mix several. The labels
are author-assigned and subjective.

------------------------------------------------------------------------

## 5. Strengths

**Observed:** - With the default `main.py` profile (genre pop, mood
happy, energy 0.8), the top result was *Sunrise City* (pop, happy,
energy 0.82) at 0.99. This matched intuition: it fits all three stated
preferences almost exactly. The output was:

  Rank   Song               Score
  ------ ------------------ -------
  1      Sunrise City       0.99
  2      Rooftop Lights     0.65
  3      Gym Hero           0.62
  4      Night Drive Loop   0.32
  5      Storm Runner       0.30

-   Every explanation showed exactly which features matched, which did
    not, and the compared values. It was always possible to see *why* a
    song received its score.
-   Rankings were deterministic and reproducible across runs.
-   All 50 automated tests passed, including nine tests covering the
    reliability auditor. They cover:
    -   the similarity formulas and the 0 to 1 bounds
    -   exclusion of unspecified features
    -   the acousticness rules
    -   input validation
    -   tie-breaking
    -   agreement between the object-based and function-based versions

**Assessed from the design (not separately measured):** - The system is
most likely to give sensible results to users whose favourite genre and
mood are well represented in the catalogue, such as lofi/chill or
pop/happy listeners. - Because unspecified features are excluded, a user
who cares only about genre is not penalised for songs that differ in
tempo or valence.

------------------------------------------------------------------------

## 6. Limitations and Bias

**Features not considered.** The system ignores lyrics, language, vocal
style, artist, release era, popularity, listening context (for example
workout or study), and any feedback from the user. It cannot capture
taste that changes over time or depends on the situation.

**Under-represented genres and moods.** Seven genres share 10 songs, and
five of those genres have only one song. A Rock/Intense listener has
exactly one rock song (*Storm Runner*) available for a genre match. A
lofi listener has three. This is a fact about the dataset, and it means
some users have far fewer strong matches available to them than others.

**Overfitting to one preference.** - Genre and mood are all-or-nothing.
A song in a closely related genre gets no genre credit, so it is ranked
as if the genre were completely unrelated. In the observed pop/happy
run, *Rooftop Lights* ("indie pop", happy, energy 0.76) scored 0.65
while *Sunrise City* ("pop") scored 0.99. Most of that gap comes from
the genre label alone. - In our Lo-fi/Chill weight experiments, tripling
a single feature's weight changed individual song scores by up to about
0.26 relative to the equal-weight baseline, and tripling mood reversed
positions 3 and 4. The output is therefore sensitive to weight choices,
and those choices were made by the designers rather than learned from
users.

**Ways the scoring could unintentionally favour some users.** - Users
whose tastes match the catalogue's dominant genres and moods (lofi,
chill, pop) are better served than users with niche or missing tastes. -
A user who specifies only a few preferences gets scores driven by those
few features, so one mismatch can sink a song. - Because
`likes_acoustic=False` means "no preference", a user who actually
dislikes acoustic music gets no penalty on acoustic songs unless they
know to set `target_acousticness=0.0`. This was a deliberate design
choice, but it relies on the user understanding the interface. - The
fixed 200 BPM tempo scale is an assumption, not a tuned value. It may be
too lenient for listeners who care strongly about tempo.

------------------------------------------------------------------------

## 7. Evaluation

This section reports what we observed when running the system. It is a
qualitative evaluation, not a formal one; see "What was not done" below.

**Method.** - Each profile was run through `recommend_songs` with *k* =
5 against the 10-song catalogue. - Weight variants were applied only in
memory, in an interactive session, using `unittest.mock.patch.dict`.
Project files were never altered, and the original weights were restored
automatically after each run. - Scores are rounded to two decimals.

### Profile comparison (equal weights)

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

**Observations.** - **Top picks.** In every profile, the top result
matched all stated preferences and scored 0.99 or 1.00. - **Lo-fi/Chill
had the deepest set of strong matches.** Its top two (Library Rain and
Midnight Coding) match both genre and mood. The next two each match one
of the two: Focus Flow is lofi but "focused", and Spacewalk Thoughts is
"chill" but ambient. - **Rock/Intense dropped off sharply after the
first result.** - Storm Runner is the only rock song in the catalogue. -
Gym Hero came second (0.66) only because its mood, "intense", matched. -
Positions 3 to 5 (0.28 to 0.31) matched neither genre nor mood and are
ranked by energy alone. - These results are consistent with the
catalogue's thin rock coverage (Section 6). - **Pop/Happy and genre
labels.** Rooftop Lights ("indie pop") received no genre credit despite
numeric values close to Sunrise City's. This illustrates the
all-or-nothing genre matching.

### Weight experiment (Lo-fi/Chill profile)

Each variant raises one weight to 3.0 and leaves the other weights at
1.0.

  --------------------------------------------------------------------------
  Rank           Equal weights  Genre ×3       Mood ×3        Energy ×3
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

**Observations.** - **Top two unchanged.** Library Rain and Midnight
Coding stayed at the top under every weighting, because they match
genre, mood and energy closely. - **Genre ×3** widened the gap between
the two single-match songs: Focus Flow (genre match) rose to 0.79 and
Spacewalk Thoughts (mood match) fell to 0.39. Their near-tie at baseline
(0.65 vs 0.64) became a 0.40 gap. - **Mood ×3** reversed positions 3 and
4. Spacewalk Thoughts rose to 0.79 and Focus Flow fell to 0.39. This was
the only variant that changed the order of the top five. - **Energy ×3**
kept the baseline order but compressed the scores. Positions 3 and 4
moved to 0.77 and 0.76, and Coffee Shop Stories, which matches neither
genre nor mood, rose from 0.33 to 0.59 because its energy (0.37) is
close to the 0.35 target. - **Ranks and scores need separate reading.**
Weight changes moved individual song scores by up to about 0.26 relative
to the equal-weight baseline, even when the order stayed the same.
Coffee Shop Stories went from 0.33 to 0.59 under energy ×3, and
Spacewalk Thoughts from 0.64 to 0.39 under genre ×3. - **Explanations
don't reveal weights.** The explanation text lists each feature's
similarity but not its weight, so it read the same under every variant
even when scores changed. The weight setting had to be recorded
separately.

**What surprised us.** - Positions 3 and 4 depended entirely on which
categorical feature was emphasised. A song matching only the genre and a
song matching only the mood were nearly tied at equal weights, and
either could be placed well ahead of the other by tripling one weight. -
In the Rock/Intense run, three of the top five songs matched neither
genre nor mood, simply because the catalogue had nothing closer.

**Automated tests.** The pytest suite (50 tests) passed in full,
including the original recommender tests and nine auditor tests. These
tests check implementation correctness, not recommendation quality.

### Reliability Auditor Evaluation

A reliability auditor was added to evaluate recommendation outputs
independently of the underlying recommendation algorithm. It examines
recommendation strength, catalogue coverage, and genre diversity. It
produces structured findings and warnings but does not modify
recommendation rankings.

The auditor uses two explicitly defined thresholds:

-   **Weak recommendation:** score below 0.50.
-   **Limited catalogue coverage:** the preferred genre represents less
    than 20% of the catalogue.

These thresholds are design choices rather than values learned from user
behavior.

#### Experiment 1: Preference Profile Evaluation

Three preference profiles were evaluated against the original ten-song
catalogue. Each profile requested five recommendations.

  -----------------------------------------------------------------------
  Profile      Average score   Weak matches Genre coverage          Genre
                                                                diversity
  ----------- -------------- -------------- -------------- --------------
  Pop / Happy          0.577              2            20%            80%
  / 0.80
  energy

  Lofi /               0.719              1            30%            60%
  Chill /
  0.40 energy

  Classical /          0.245              5             0%            60%
  Sad / 0.10
  energy
  -----------------------------------------------------------------------

All three profiles produced an overall warning status. The pop and lofi
profiles were flagged because they each contained at least one weak
recommendation. The classical profile had five weak recommendations and
no catalogue representation for the preferred genre.

The lofi profile produced the highest average score and had the highest
catalogue coverage. These observations do not establish that catalogue
coverage independently causes higher recommendation scores because
genre, mood, and energy were changed simultaneously.

#### Experiment 2: Catalogue Coverage Threshold

A synthetic catalogue of ten songs was used to test the auditor's
coverage thresholds independently of the original dataset.

  Test     Matching songs   Coverage Finding                                 Overall status
  ------ ---------------- ---------- --------------------------------------- ----------------
  A                     0         0% Warning: no representation              Warning
  B                     1        10% Informational: limited representation   Passed
  C                     2        20% None                                    Passed
  D                     3        30% None                                    Passed

The results confirmed the intended threshold behavior. At zero coverage,
the auditor generates a warning because the preferred genre is entirely
absent. At 10% coverage, it generates an informational finding without
changing the overall status to warning. At exactly 20% and above, no
coverage finding is generated.

During testing, an inconsistency was identified in which informational
findings also caused an overall warning status. This was corrected:
informational findings remain visible in the findings list but do not
independently cause a warning status. Two additional regression tests
verify this behavior for limited catalogue coverage and low genre
diversity.

#### Experiment 3: Recommendation Consistency

The baseline Pop / Happy / 0.80 energy profile was executed ten
consecutive times against the same catalogue.

All ten executions produced identical results, including recommendation
ordering, individual scores, average match score, weak-match
identification, warning messages, and overall audit status. The
experiment demonstrated repeatability for the tested configuration and
execution environment. It does not establish determinism across
different environments, datasets, or software configurations.

#### Automated Verification

After the auditor changes, the complete pytest suite passed all 50
tests:

-   41 original recommender tests.
-   9 auditor tests, including two regression tests for informational
    finding classification.

#### Evaluation Limitations

These experiments evaluate the auditor's implementation and the
consistency of the recommendation pipeline. They do not establish that
recommendations are objectively relevant or satisfactory to listeners.

In particular:

-   The weak-match and catalogue-coverage thresholds are
    designer-selected.
-   The synthetic catalogue experiment verifies threshold behavior, not
    real-world recommendation quality.
-   The consistency experiment covers only one preference profile and
    one execution environment.
-   No independent listener judgments or formal ranking metrics were
    collected.
-   Genre diversity is a simple descriptive measure and does not
    establish meaningful musical variety.

The experiments should therefore be interpreted as implementation-level
reliability checks rather than comprehensive validation of
recommendation quality.

------------------------------------------------------------------------

**What was not done.** - No real user feedback or independent relevance
judgements were collected. - No formal ranking metrics (Precision@K,
Recall@K or NDCG@K) were calculated, because there is no ground-truth
set of relevant songs for each profile. - All judgements about whether a
ranking is "good" are qualitative and based on the designers' intuition.
The scores above are the system's outputs, not measures of
recommendation quality.

------------------------------------------------------------------------

## 8. Future Work

All items below are **proposals**. None have been implemented or tested.

**Additional features or preferences.** - Partial-credit genre
similarity, for example "indie pop" treated as close to "pop". -
Multiple favourite genres or moods per user. - Explicit dislikes. -
Context such as activity or time of day. - Tolerance ranges instead of
single target values.

**Better explanations.** - Show each feature's weight and its weighted
contribution to the final score. - Sort the explanation by the features
that mattered most. - Write short natural-language summaries alongside
the detailed breakdown.

**Diversity among top results.** - Add a diversity rule, such as
limiting repeats of the same artist or genre in the top five. - Re-rank
the results to balance relevance against variety.

**Handling more complex tastes and validating quality.** - Learn weights
from user feedback instead of setting them by hand. - Expand the
catalogue so every genre has several songs. - Collect real or simulated
relevance judgements, so that Precision@k, Recall@k and NDCG can be
measured. - Warn the user when an unknown preference key (for example a
typo) is ignored.

------------------------------------------------------------------------

## 9. Personal Reflection

**What I learned about recommender systems.** Building VibeMatch showed
that a recommender is mostly a set of human design decisions expressed
as math. These include which features count, how "close" is measured,
how much each feature matters, and what to do when information is
missing. Even a short, transparent formula produces rankings that feel
authoritative, but those rankings depend on choices someone made.

**Something unexpected.** The weight experiments were the most revealing
part. Raising one feature's weight from 1 to 3 was enough to swap the
mid-ranked songs or change an individual song's score by about 0.26, so
"the right answer" depends heavily on tuning. It was also striking that
a single categorical label, "indie pop" versus "pop", could cost a song
a large share of its score even when its sound was nearly identical to
the top pick.

**How this changes my view of music apps.** Real streaming recommenders
work at a far larger scale and learn from behaviour, but they still rest
on choices about features, weights and data coverage. This project made
it clearer how under-represented genres or a narrowly built catalogue
could quietly steer some listeners toward the mainstream. Explanations
and transparency matter because they let users see, and question, why
something was recommended.

------------------------------------------------------------------------

## 10. AI Assistance and Human Verification

OpenAI ChatGPT (GPT-6) assisted with planning, implementation guidance,
experimental design, test development, documentation, and interpretation
of results for the VibeMatch reliability auditor.

**Accepted AI suggestions.** The developer accepted and implemented
AI-assisted recommendations to:

- Introduce an independent reliability auditor without modifying the
  underlying recommendation algorithm.
- Evaluate recommendation strength, catalogue coverage, and genre
  diversity.
- Establish explicit thresholds for weak recommendations and limited
  catalogue coverage.
- Produce structured findings and warnings to make potential reliability
  problems visible.
- Develop automated tests and experiments to evaluate auditor behavior
  and recommendation consistency.

**Rejected and revised suggestions.** No major AI suggestions were
explicitly rejected outright during the documented development process.
Suggestions were generally evaluated through developer review,
implementation, and testing. Where testing exposed incorrect or
misleading behavior, the implementation was revised rather than accepted
without qualification. For example, testing revealed that informational
findings incorrectly contributed to an overall warning status. This
behavior was corrected, and regression tests were added.

The developer manually reviewed and applied proposed code changes,
executed the experiments, inspected their outputs, and verified the
resulting implementation through automated tests.

Final implementation decisions and verification remained under human
control.
