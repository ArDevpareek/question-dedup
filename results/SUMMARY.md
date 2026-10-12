# Summary of the evaluation runs

All numbers below are copied from the files in this `results/` folder.
The file each number comes from is named next to it.

**Update:** a third version of the judge rules was tested after this summary was first written.
It adds a definition-versus-calculation rule. See **section 7** at the end.
Sections 1 to 6 describe the first two rule sets ("old" and "new") and are unchanged,
except that file names in section 6 now say where each judge cache is kept.

Three judge rule sets appear in this folder:

| Name | Cache file | Cache version |
|---|---|---|
| old rules | `judge_cache_v1.json` | `09d27bfb7e4f` |
| new rules | `judge_cache_v2.json` | `51acce50ed6b` |
| new + calc rule (current `judge.py`) | `judge_cache.json` (backup: `judge_cache_v3.json`) | `0c86fbfe3100` |
| new + calc rule, with `gemini-3.8-flash` (18 PAWS verdicts only) | `judge_cache_v4_flash38.json` | `789a578c174a` |

**Fourth update (version 1 frozen):** section 10 adds the held-out test on fresh pairs, and section 11 lists
what changed when version 1 was frozen. Since then, the scripts named below live in `experiments/`, the data
files in `data/`, and every `judge_cache*.json` file in `experiments/judge_caches/`.

**Third update:** section 9 adds retry handling, a regression re-check, the public data
re-run with the current rules, and a clean demo database. After section 9, `judge_cache.json`
holds 155 verdicts (56 test + 99 public), and the `questions.db` with 43 questions is now `questions_dev_43.db`.

**Second update:** `detector.py` now uses the final design (section 8).
Where sections 5 and 7 say `detector.py` still uses (0.92, 0.75), that is no longer true.

## Before you read: two things that were already done

- **The new judge rules were already in `judge.py`** when this work started.
  The saved verdicts in `judge_cache.json` were made with the *old* rules.
  `judge_cache_v1.json` was already an exact copy of that old cache.
- So for the "old rules" runs (step 1 and step 3) I did **not** call the judge again.
  I ran `evaluate_pairs.py` through a small wrapper that reads the old verdicts
  from `judge_cache_v1.json`. The wrapper blocks any new judge call.
  `step1_stepA.txt` starts with a `[wrapper]` line that shows this.
- Step 3 (`step3_combined.txt`) read `judge_cache.json` while it still held the old verdicts.
  Its first line shows the old cache version (`09d27bfb7e4f`).
  The new-rules runs show version `51acce50ed6b`.

## How to read the numbers

- **Precision**: of the pairs we flagged as duplicates, how many really were.
- **Recall**: of the real duplicates, how many we caught.
- **Missed**: real duplicates we let through.
- **False alarms**: different questions we wrongly flagged.
- **Judge calls**: how many times we asked the LLM.
- **TEST half** = 30 pairs (`pairs[1::2]`) that were *not* used to pick any setting.
  This is the fair score. **All 60** includes the 30 pairs used for tuning.
- With only 30 test pairs, one pair is about 0.06 of recall or precision.
  Small differences are not reliable.

## 1. Main table (test_pairs.json)

Source for every row: `step6_mistakes_by_approach.txt`, section 1.
The same numbers also appear in the step 1 to step 4 files.

| Approach | Half | Precision | Recall | Missed | False alarms | Judge calls |
|---|---|---|---|---|---|---|
| Embedding only, line 0.80 (best line, see note) | TEST | 0.72 | 0.81 | 3 | 5 | 0 |
| | All 60 | 0.73 | 0.84 | 5 | 10 | 0 |
| Judge only, old rules | TEST | 0.94 | 0.94 | 1 | 1 | 28 |
| | All 60 | 0.97 | 0.88 | 4 | 1 | 56 |
| Judge only, new rules | TEST | 1.00 | 1.00 | 0 | 0 | 28 |
| | All 60 | 0.94 | 1.00 | 0 | 2 | 56 |
| Old cascade (0.92, 0.75), old rules | TEST | 0.93 | 0.81 | 3 | 1 | 17 |
| | All 60 | 0.93 | 0.78 | 7 | 2 | 34 |
| Old cascade (0.92, 0.75), new rules | TEST | 0.93 | 0.88 | 2 | 1 | 17 |
| | All 60 | 0.91 | 0.91 | 3 | 3 | 34 |
| Best step-1 setting (0.92, 0.50), old rules | TEST | 0.88 | 0.88 | 2 | 2 | 22 |
| | All 60 | 0.90 | 0.84 | 5 | 3 | 44 |
| Best cascade with new rules (0.98, 0.50) | TEST | 1.00 | 0.94 | 1 | 0 | 26 |
| | All 60 | 0.97 | 0.97 | 1 | 1 | 52 |
| Cross-encoder alone, line 0.5 | TEST | 1.00 | 0.62 | 6 | 0 | 0 |
| | All 60 | 0.89 | 0.53 | 15 | 2 | 0 |
| Combined D3 (HIGH 0.8, LOW 0.05), old rules | TEST | 0.93 | 0.81 | 3 | 1 | 8 |
| | All 60 | 0.96 | 0.69 | 10 | 1 | 15 |
| Combined D3 (HIGH 0.8, LOW 0.05), new rules | TEST | 1.00 | 0.81 | 3 | 0 | 8 |
| | All 60 | 1.00 | 0.72 | 9 | 0 | 15 |

Notes:
- **Embedding only**: no line reaches precision 0.90 (`step1_stepA.txt`, section 2).
  Line 0.80 makes the fewest mistakes (5 missed + 10 false alarms on all 60).
  That is why it is called the "best line" here.
- **Best step-1 setting**: step 1 picked (0.92, 0.5) on the tune half (`step1_stepA.txt`).
  On the test half it drops below 0.90 precision (0.88), so it did not hold up.
- **Best cascade with new rules**: step 4 re-ran the same tuning with the new judge
  and picked (0.98, 0.5) (`step4_new_judge.txt`). The 0.98 top line means the
  "auto-duplicate" zone is almost switched off. Almost everything goes to the judge.
- **D3**: the tuning picked HIGH 0.8, LOW 0.05 with both old and new rules
  (`step3_combined.txt`, `step4_combined_new_judge.txt`). On the test half,
  HIGH 0.8 with LOW 0.10 scored the same recall with fewer calls (6 instead of 8).
  But that setting was not chosen, because it did worse on the tune half.

## 2. Which test pairs each approach still gets wrong (all 60 pairs)

Source: `step6_mistakes_by_approach.txt`, section 2.

**Embedding only, line 0.80** (15 mistakes)
- paraphrase: P7
- numbers_changed: N2, N5, N6
- same_topic_different_concept: D1, D4, D5
- near_miss_wording: W2, W3, W5, W6, W7, W8
- different_topic: T2
- other_subject_paraphrase: C4

**Judge only, old rules** (5 mistakes)
- numbers_changed: N1
- extra_part: X1, X3, X4
- near_miss_wording: W4 ("real image" vs "virtual image")

**Judge only, new rules** (2 mistakes)
- same_topic_different_concept: D1, D7

**Old cascade (0.92, 0.75), old rules** (9 mistakes)
- paraphrase: P7
- numbers_changed: N1, N6
- extra_part: X1, X3, X4
- near_miss_wording: W5, W6
- other_subject_paraphrase: C4

**Old cascade (0.92, 0.75), new rules** (6 mistakes)
- paraphrase: P7
- numbers_changed: N6
- same_topic_different_concept: D1
- near_miss_wording: W5, W6
- other_subject_paraphrase: C4

**Best step-1 setting (0.92, 0.50), old rules** (8 mistakes)
- numbers_changed: N1
- extra_part: X1, X3, X4
- near_miss_wording: W4, W5, W6
- other_subject_paraphrase: C4

**Best cascade with new rules (0.98, 0.50)** (2 mistakes)
- same_topic_different_concept: D1
- other_subject_paraphrase: C4

**Cross-encoder alone, line 0.5** (17 mistakes)
- paraphrase: P1, P5, P7, P8
- numbers_changed: N1, N2, N3, N4, N5, N6
- extra_part: X3, X6
- near_miss_wording: W3, W7
- other_subject_paraphrase: C1, C3, C4

**D3 (0.8, 0.05), old rules** (11 mistakes)
- paraphrase: P7
- numbers_changed: N1, N2, N3, N4, N5
- extra_part: X3
- near_miss_wording: W4
- other_subject_paraphrase: C1, C3, C4

**D3 (0.8, 0.05), new rules** (9 mistakes)
- paraphrase: P7
- numbers_changed: N1, N2, N3, N4, N5
- other_subject_paraphrase: C1, C3, C4

What the patterns show:
- **Near-miss wording** ("can" vs "cannot", "real" vs "virtual") fools the embedding.
  These pairs score up to 0.97 (`step1_stepA.txt`). So any high "auto-duplicate" line
  like 0.92 lets W5 and W6 through as false alarms. The judge gets them right.
- **Number-changed and short paraphrases** fool the cross-encoder. It gives most
  number-changed pairs scores of 0.00 to 0.39 (`step2_cross_encoder.txt`).
  (A likely reason, not tested here: it was trained on Quora questions,
  where different numbers often mean a different question.)
  So D3's LOW line throws these pairs away before the judge sees them.
- **The new rules fixed the old judge's mistakes** (N1, X1, X3, X4, W4).
  But they added two false alarms: D1 and D7.
  - D1: "What is the angle of reflection?" vs "The angle of incidence is 30°. What is the angle of reflection?"
  - D7: "What is lateral inversion?" vs "Why is the word AMBULANCE written in reverse on the front of ambulances?"
- **C4** ("Who wrote the Indian national anthem?" vs "Name the author of Jana Gana Mana")
  has an embedding score of only 0.39. Any cascade with a low line of 0.40 or more misses it,
  even though the judge gets it right.

## 3. Regression test (original 10 questions)

Source: `step4_regression.txt`.

- Result with the new judge rules: **Correct 9/10, Wrong 1, LLM judge calls 4.**
- The wrong one is **Q7**. It is the *same question pair* as test pair D1:
  "What is the angle of reflection?" then "The angle of incidence is 30°. What is the angle of reflection?".
  The expected answer is "new". The new judge said "duplicate". Its reason:
  "It is the same core question about the angle of reflection with a specific number added."
- So the new rule "a small extra part added = duplicate" is too broad here.
  A definition question and a calculation question are different, but the judge treats the number as an "extra part".
- I do not have a saved score of this test with the old rules, so I cannot say if it got worse.

## 4. Public data (QQP and PAWS)

**Important:** QQP and PAWS use their *own* idea of "duplicate", not ours.
- QQP (Quora) calls two questions duplicates only if they have the same *intent*.
  A small extra detail can make them "different" there. Our rules call that a duplicate.
- PAWS pairs use almost the same words, often just in a different order
  ("A beat B" vs "B beat A"). Their "different" pairs are word-order traps.
- So a low score here does not always mean our detector is wrong.
  It partly shows that the definitions do not match.
- Only the **new** judge rules were tested on public data, because `judge.py` already had them.

The sample: 50 QQP pairs (17 duplicate, 33 different) and 50 PAWS pairs
(24 duplicate, 26 different), picked with a fixed random seed
(`step5_make_public_pairs.txt`, `public_pairs.json`).

To get QQP and PAWS separately, I split `public_pairs.json` into `public_qqp.json` and
`public_paws.json` and ran both scripts on each part. The judge used cached verdicts, so no new calls were made.

| Approach | Data | Precision | Recall | Missed | False alarms | Judge calls | Source |
|---|---|---|---|---|---|---|---|
| Judge only (new rules) | QQP | 0.76 | 0.94 | 1 | 5 | 49 | `step5_public_judge_qqp.txt` |
| Judge only (new rules) | PAWS | 0.64 | 0.96 | 1 | 13 | 50 | `step5_public_judge_paws.txt` |
| Judge only (new rules) | both | 0.68 | 0.95 | 2 | 18 | 99 | `step5_public_judge.txt` |
| Cross-encoder alone, line 0.5 | QQP | 0.94 | 0.88 | 2 | 1 | 0 | `step5_public_cross_encoder_qqp.txt` |
| Cross-encoder alone, line 0.5 | PAWS | 0.48 | 0.92 | 2 | 24 | 0 | `step5_public_cross_encoder_paws.txt` |
| Cross-encoder alone, line 0.5 | both | 0.60 | 0.90 | 4 | 25 | 0 | `step5_public_cross_encoder.txt` |
| Embedding only, line 0.80 | QQP | 0.70 | 0.82 | 3 | 6 | 0 | `step5_public_judge_qqp.txt` |
| Embedding only, line 0.80 | PAWS | 0.48 | 1.00 | 0 | 26 | 0 | `step5_public_judge_paws.txt` |
| Old cascade (0.92, 0.75) | QQP | 0.79 | 0.88 | 2 | 4 | 20 | `step5_public_judge_qqp.txt` |
| Old cascade (0.92, 0.75) | PAWS | 0.49 | 1.00 | 0 | 25 | 1 | `step5_public_judge_paws.txt` |

All rows above are on all pairs of that set, not a tune/test split.
(The one judge "review" on QQP counts as caught.)

What this shows:
- **PAWS breaks the embedding.** Every PAWS pair scores 0.91 or higher (`step5_public_judge.txt`).
  So any embedding line flags all of them, and the cascade sends almost nothing to the judge.
  The judge does better than the cross-encoder on PAWS (13 vs 24 false alarms out of 26 "different" pairs).
  But it still calls half of the word-order traps duplicates.
- **On QQP the cross-encoder wins** (precision 0.94 vs 0.76 for the judge).
  That is expected: it was trained on Quora data, so it learned QQP's own definition.
  The judge's QQP false alarms include pairs like "Is Economics good major?" vs
  "Is economics a good major for an entrepreneur?". Our "extra part = duplicate" rule
  says yes, but QQP says no (`step5_public_judge.txt`, section 5).
- No setting reached precision 0.90 on the public tune halves, so the "Chosen" line in
  those files is just the top of the list, not a real pick.
- The section headings in `evaluate_pairs.py` say "all 60 pairs" and "30 pairs".
  Those labels are fixed text. On public data the real sizes are 100 and 50
  (or 50 and 25 for the per-dataset files).

## 5. Recommendation

**Recommended design: exact check → low embedding line at 0.50 → judge (new rules) decides everything else.
No "auto-duplicate" zone** (top line 0.98, which in practice means almost off).

This is the setting the step 4 tuning picked: (0.98, 0.50) with the new rules.

Why, using the numbers in table 1:
1. **The judge is what makes it accurate.** On the test half, the judge with the new rules scores
   precision 1.00 and recall 1.00. No method without the judge comes close.
   - The embedding alone gets at best 0.72 / 0.81.
   - The cross-encoder alone gets 1.00 / 0.62.
2. **A high "auto-duplicate" line hurts.** Any top line of 0.92 lets the near-miss pairs
   W5 and W6 through as false alarms. Those pairs score 0.94 to 0.97, and the judge would have caught them.
   The new-rules tuning moved the top line up to 0.98 for this reason.
3. **The low line at 0.50 saves only a few calls.** On all 60 pairs it uses 52 judge calls instead of 56
   and gives 0.97 / 0.97. On the test half it gives 1.00 / 0.94 with 26 calls instead of 28.
   It loses one pair (C4, embedding score 0.39).
4. **The cross-encoder should not be the gate.** D3 with the new rules cuts judge calls a lot:
   8 instead of 28 on the test half (about 70% fewer).
   But recall drops from 1.00 to 0.81, and on all 60 pairs it misses 9 duplicates.
   Five of those are number-changed questions (N1 to N5), which matter a lot for an exam bank.

**The trade-off in one line:**
- Best accuracy: send nearly every non-exact pair to the judge (26 to 28 calls per 30 test pairs).
- Or save about 70% of LLM calls with D3 and accept missing about 1 in 5 real duplicates
  (test-half recall 0.81).
- The numbers here favour accuracy. The cheap options lose exactly the cases that matter most:
  changed numbers and reworded questions.

**Before using it, fix one known weak spot in the new rules.**
With the recommended setting, the only false alarm on all 60 pairs is D1. The regression
test's only failure is Q7, the same question pair: a definition question ("What is the angle of reflection?")
against a calculation with a number added. The judge treats the number as a "small extra part".
- This is a definition-versus-calculation pair, which the new rules list as DIFFERENT.
- So a sentence in the prompt that says "adding numbers to turn a definition into a calculation
  makes it DIFFERENT" would likely fix it.
- This was not tested here.

**Things to keep in mind:**
- The test half is only 30 pairs. The gap between "judge only" (1.00 / 1.00)
  and the recommended cascade (1.00 / 0.94) is one pair, so the two are basically tied.
- `detector.py` still uses the old lines (0.92, 0.75). It was not changed, as asked.
  The regression score of 9/10 is for those old lines with the new judge rules.
- The public data shows the design has a weak spot with word-order traps (PAWS).
  The embedding cannot see them at all, and the judge catches only half.
  If your question bank has pairs like "A causes B" vs "B causes A", this needs more work.

## 6. Errors and things that did not go as planned

- **No step failed.** All judge calls worked: 56 in step 4 and 99 in step 5.
  There were no 429 / RESOURCE_EXHAUSTED errors, so `SLEEP_BETWEEN_CALLS` stayed at 4.
  Both public datasets downloaded.
- **Some step changes were already done when work began.**
  - `evaluate_pairs.py` already had parts b, c and d of step 1. I only added part a
    (the pairs file as a command-line argument).
  - `evaluate_cross_encoder.py` already had the given code. I only added the command-line argument.
  - `judge.py` already had the new judge text from step 4. I checked it and did not edit it.
  - `judge_cache_v1.json` was already an exact copy of the old cache.
    I copied it again as asked (no change).
- **The old-rules runs used a wrapper** (see the top of this file), because the old
  prompt text was no longer in `judge.py`. It would have been needed to reuse the old cache normally.
- **About 100 public judge calls became 99.** One QQP pair was an exact match, so the exact
  check handled it and no judge call was needed (49 QQP calls + 50 PAWS calls).
- **The new-rules verdicts are kept in `judge_cache_v2.json`.** That file holds both the
  56 test verdicts and the 99 public verdicts (155 in total; the pair ids do not overlap).
  The old verdicts are kept in `judge_cache_v1.json`.
  `judge_cache.json` now holds only the 56 test verdicts for the new + calc rule (section 7).
- **Installing `datasets` changed one package version:** `fsspec` went from 2026.9.0 to 2026.7.0.
- **Extra files I added** to get the numbers this summary needed:
  - `evaluate_combined.py` (step 3, as asked)
  - `make_public_pairs.py` and `public_pairs.json` (step 5, as asked)
  - `public_qqp.json` and `public_paws.json` (the per-dataset split)
  - `list_mistakes.py`, which writes `step6_mistakes_by_approach.txt`. It gives the
    all-60 numbers and the mistake lists that the other files do not print.
- **Warnings that are not errors:** Hugging Face warnings about the missing `HF_TOKEN`
  and about symlinks on Windows appear in some result files. They did not affect any result.

## 7. Follow-up: the definition-versus-calculation rule

### What changed

One new item was added to the DIFFERENT list in `judge.py`:

> a question that asks what something is (a definition or explanation) versus a
> question that gives numbers and asks to calculate it. Adding numbers to a
> definition question turns it into a calculation; this is not a small extra part.
> For example "What is speed?" versus "A car travels 100 km in 2 hours. Find its speed."

The example is about speed on purpose. No test pair or seed question mentions speed,
so the rule does not hand the judge the answer to D1 or Q7.

Before the run, the new-rules cache was saved as `judge_cache_v2.json`,
because a changed prompt makes `evaluate_pairs.py` throw the old cache away.
This run made 56 judge calls with no errors (`step7_rule3_judge.txt`).
The public data was **not** re-run with this rule.

### Results on test_pairs.json

Source for the table: `step7_mistakes_by_approach.txt`, section 1.

| Approach | Half | Precision | Recall | Missed | False alarms | Judge calls |
|---|---|---|---|---|---|---|
| Judge only, new rules | TEST | 1.00 | 1.00 | 0 | 0 | 28 |
| | All 60 | 0.94 | 1.00 | 0 | 2 | 56 |
| Judge only, new + calc rule | TEST | 1.00 | 1.00 | 0 | 0 | 28 |
| | All 60 | 0.97 | 1.00 | 0 | 1 | 56 |
| Cascade (0.98, 0.50), new rules | TEST | 1.00 | 0.94 | 1 | 0 | 26 |
| | All 60 | 0.97 | 0.97 | 1 | 1 | 52 |
| Cascade (0.98, 0.50), new + calc rule | TEST | 1.00 | 0.94 | 1 | 0 | 26 |
| | All 60 | 1.00 | 0.97 | 1 | 0 | 52 |
| Old cascade (0.92, 0.75), new + calc rule | TEST | 0.93 | 0.88 | 2 | 1 | 17 |
| | All 60 | 0.94 | 0.91 | 3 | 2 | 34 |
| D3 (0.8, 0.05), new + calc rule | TEST | 1.00 | 0.81 | 3 | 0 | 8 |
| | All 60 | 1.00 | 0.72 | 9 | 0 | 15 |

Mistakes on all 60 pairs (`step7_mistakes_by_approach.txt`, section 2):
- **Judge only, new + calc rule** (1 mistake): same_topic_different_concept D7
  ("What is lateral inversion?" vs the AMBULANCE question).
- **Cascade (0.98, 0.50), new + calc rule** (1 mistake): other_subject_paraphrase C4.
  D7 never reaches the judge in this cascade, because its embedding score is below the 0.50 line.
- **D3 (0.8, 0.05), new + calc rule**: the same 9 mistakes as with the new rules
  (P7, N1 to N5, C1, C3, C4). D3 sends very few pairs to the judge, so the rule makes no difference.

The new rule changed nothing on the TEST half. All its gains are on the tune half (D1 is a tune-half pair).

### The tuning now picks a different setting

With the new rule, the step 1 tuning picks **(0.92, 0.50)**, not (0.98, 0.50) (`step7_rule3_judge.txt`).
- On the tune half both settings catch every duplicate (recall 1.00).
- (0.92, 0.50) has precision 0.94 with 22 calls; (0.98, 0.50) has precision 1.00 with 26 calls.
- Both pass the 0.90 precision floor, so the rule takes the one with fewer judge calls.
- On the TEST half: (0.92, 0.50) scores 0.94 / 0.94 with 22 calls; (0.98, 0.50) scores 1.00 / 0.94 with 26 calls.
- On all 60 pairs, (0.92, 0.50) still makes the near-miss false alarms W5 and W6.

### Did it fix D1 and Q7? Only by luck

- **Pair test:** D1 is now correct ("different").
- **Regression test:** still **9/10**. Q7 is still wrong ("semantic_duplicate"), with 4 judge calls
  (`step7_rule3_regression.txt`). Q7 is the same question pair as D1.
- To find out why, I made 6 extra judge calls on this one pair (`step7_q7_diagnostic.txt`):
  - with the 3 neighbours the detector really sends (Q6, Q1, Q5): duplicate
  - with only Q6, labelled `[Q6]` as in `detector.py`: duplicate (3 times out of 3)
  - with only the question, labelled `[A]` as in `evaluate_pairs.py`: **different once, duplicate once**
- So the exact same prompt gave two different answers, even at temperature 0.
  The judge is not stable on this pair. 5 of the 6 extra calls said "duplicate".
- **Conclusion:** the new rule did not reliably fix this case. The pair test got the right answer
  in its one call, but most calls still say "duplicate". The 9/10 regression score is the more honest picture.
- This also means every single-run number in this summary carries some noise from the judge.
  With 30 test pairs, one flipped verdict moves precision or recall by about 0.06.

### What this means for the recommendation

- The recommendation in section 5 still stands: exact check, then a low embedding line at 0.50,
  then the judge, with no auto-duplicate zone (top line 0.98).
- With the new + calc rule this setting makes 1 mistake on all 60 pairs (C4) and uses 52 judge calls
  (`step7_mistakes_by_approach.txt`).
- The tuning rule now prefers (0.92, 0.50) to save 4 judge calls on the tune half.
  That brings back the W5 and W6 false alarms on all 60 pairs, and one false alarm on the test half.
  Which you prefer depends on whether 4 calls in 30 matter more to you than one false alarm.
- **Definition vs calculation is still not solved** (Q7). Asking the judge once is not
  reliable for this kind of pair. Options not tested here:
  - ask the judge 3 times and take the majority
  - add a simple check for "one question has numbers, the other does not"

## 8. Final design

### The design (now in `detector.py`)

1. **Exact check.** Same text after cleaning means duplicate. No LLM call.
2. **Embedding search.** If the closest question scores below **0.50**, the question is new. No LLM call.
3. **Judge decides everything else** (new + calc rules). There is no auto-duplicate zone any more
   (`DUP_THRESHOLD = 1.01`), so only the exact check can mark a duplicate without the judge.
4. **Numbers guard.** If the judge says "duplicate" but only one of the two questions has a number,
   the result is "review" instead. This catches definition-versus-calculation clashes such as Q7.

Backups made before the changes: `questions_before_final.db` (the database had 35 questions)
and `judge_cache_v3.json`.

### Final setting (1.01, 0.50) on test_pairs.json

Source: `final_pairs_guard_on.txt` and `final_pairs_guard_off.txt`, section 6 (both files show the same numbers).
Cached verdicts only, no new judge calls.

| Half | Numbers guard | Precision | Recall | Missed | False alarms | Review | Judge calls |
|---|---|---|---|---|---|---|---|
| TEST (30) | on | 1.00 | 0.94 | 1 | 0 | 0 | 27 |
| TEST (30) | off | 1.00 | 0.94 | 1 | 0 | 0 | 27 |
| All 60 | on | 1.00 | 0.97 | 1 | 0 | 0 | 53 |
| All 60 | off | 1.00 | 0.97 | 1 | 0 | 0 | 53 |

- The only mistake is **C4** (embedding score 0.39, below the 0.50 line) (`final_pairs_guard_on.txt`, section 7).
- **The guard changes nothing on these pairs.** Only 4 of the 60 pairs have a number in just one question:
  D1, D8, D9 and D11 (`final_guard_pairs.txt`). All 4 are labelled "different", and the current
  judge said "different" for all 4, so the guard never fires. It also means that on this test set
  the guard can never cause a missed duplicate.
- With the rule version 2 verdicts, D1 was judged "duplicate" (`final_guard_pairs.txt`).
  There the guard would have changed it to "review", so a person would check it instead of it being rejected automatically.
  (In these tables "review" counts as flagged, so it would still count as a false alarm.)
- (1.01, 0.50) uses 53 judge calls on all 60 pairs, one more than (0.98, 0.50), which used 52 (`step7_mistakes_by_approach.txt`).

### Regression test (original 10 questions)

Source: `final_regression.txt`.

- **Correct: 9/10.** The script counts Q7 as wrong, because the expected label is "new".
- Q7 now shows **"review" by "numbers guard"**, with the reason "Only one question has numbers.
  This is the same question about the angle of reflection with numbers added to the setup."
  This is the intended safe result: a person checks it, instead of it being rejected as a duplicate.
- The script reports **7 LLM judge calls**, but it only counts results marked "judge".
  Q2 to Q9 all went to the judge (8 calls). Q7's call is counted under "numbers guard" instead.
- Q2 and Q4 used to be decided by the embedding alone. They now go to the judge, because the auto-duplicate zone is off.

### Generator run (`python run_generate.py`, topic "reflection of light", 5 questions)

**First run: crashed** (`final_generate.txt`).
- After 10 candidates, the run stopped with **429 RESOURCE_EXHAUSTED**.
  This is the free-tier limit of **15 requests per minute** for `gemini-3.5-flash-lite`.
- The regression test had just used the same quota. And the generator sends judge calls one after another
  with no pause, while the final design sends almost every candidate to the judge.
- Before the crash: **3 accepted** (Q36, Q37, Q38), **4 rejected**, **3 review**.
  All 3 reviews were judge calls that failed with 429, not real verdicts.
- LLM calls: 1 generation call, 10 judge calls (7 answered, 3 failed), then the round-2 generation call failed and the script stopped.
- No final "Accepted / Rejected" line was printed, because the script crashed.

**Retry after the per-minute quota reset** (`final_generate_retry.txt`).
- **Accepted: 5, Rejected: 3, Review: 1, Checked: 9.** All in round 1.
- LLM calls: 1 generation call and 9 judge calls. All 9 checked questions were decided by the judge or the guard.
- The one review came from the numbers guard. The new question "If the linear magnification produced by
  a spherical mirror has a negative value, what does this indicate..." was judged a duplicate of Q37,
  which says "a negative value of -2". The guard fired only because of the "-2".
  This is a case where the guard is too strict.

The database went from 35 to 43 questions (8 added in total: Q36 to Q43).

### Stronger judge model (`gemini-3.8-flash`): mostly could not run

- The model exists and worked for 18 calls. Then the key hit the **free-tier daily limit:
  20 requests per day for this model**, with "retry in 9h31m" (`strong_judge_paws_run4.txt`).
- PAWS, first run: 18 verdicts, 29 failures with 429 and 3 with 503 "high demand" (`strong_judge_paws_run1.txt`).
  Retries 2, 3 and 4 each failed all 32 remaining calls with 429.
  Raising `SLEEP_BETWEEN_CALLS` to 10 cannot help with a per-day limit, so it was left at 4.
- **The test-pairs run with this model was skipped.** All 56 calls would have hit the same daily limit.
  So there is no `strong_judge_pairs.txt`.
- The numbers inside `strong_judge_paws_run1.txt` to `run4.txt` are **not usable**:
  missing verdicts are counted there as "review".
- **Partial comparison on the 18 PAWS pairs that did get a verdict** (7 duplicate, 11 different).
  Source: `strong_judge_paws_partial_compare.txt`.

| Judge | Rules | Precision | Recall | Missed | False alarms |
|---|---|---|---|---|---|
| gemini-3.8-flash | current (new + calc rule) | 0.67 | 0.86 | 1 | 3 |
| gemini-3.5-flash-lite | rule version 2 (from `step5_public_judge_paws.txt`) | 0.50 | 0.86 | 1 | 6 |

- The stronger model made half as many false alarms on these word-order traps.
  It got PAWS2, PAWS10 and PAWS14 right where flash-lite was wrong. Every other verdict was the same.
- Treat this with care. It is only 18 pairs, and **the two runs used different rule versions**:
  flash-lite used rule version 2, not the current rules. So the gain may come partly from the rules, not only the model.
- The strong model's 18 verdicts are saved in `judge_cache_v4_flash38.json`.

**Restores (confirmed in `final_restore_check.txt`):**
- `llm.py` is back to `MODEL = "gemini-3.5-flash-lite"`.
- `judge_cache.json` is again an exact copy of `judge_cache_v3.json` (56 verdicts, version `0c86fbfe3100`).
  It matches the current prompt and model, so the next run will use these saved verdicts and make no new calls.

### Known limitations

- **Word-order traps (PAWS).** These pairs use the same words in a different order and mean different things.
  The embedding scores all of them 0.91 or higher (`step5_public_judge.txt`).
  The flash-lite judge (rule version 2) called 13 of 26 such pairs duplicates (`step5_public_judge_paws.txt`).
  The PAWS data has not been re-run with the current rules.
- **World-knowledge paraphrases below the 0.50 line.** C4 ("Who wrote the Indian national anthem?" vs
  "Name the author of Jana Gana Mana") scores only 0.39, so it is called "new" before the judge sees it.
  This is the final design's only mistake on the 60 pairs.
- **The judge is not stable between calls.** The same prompt gave "different" once and "duplicate" once on the
  Q7/D1 pair (`step7_q7_diagnostic.txt`). One flipped verdict moves the test-half scores by about 0.06.
- **The judge rules were tuned on the same 60 pairs.** Rule versions 2 and 3 were written after looking at
  mistakes on these pairs, so even the TEST half is not truly new data for the prompt.
  Only the public data is outside data, and it was not re-run with the current rules.
- **The numbers guard is crude.** Any digit counts, so "-2" in Q37 was enough to send a likely duplicate to review
  (`final_generate_retry.txt`).
- **Rate limits.** With the auto-duplicate zone off, almost every candidate needs a judge call.
  The generator has no pause between calls, and the first generator run crashed on the 15-per-minute free-tier limit.
- **Topic drift and correctness in generated questions.** The generator files show some examples
  (these are judgement calls, not measured numbers):
  - The bank already holds a question on total internal reflection, which belongs to refraction, a neighbouring topic.
    It is in the context list in `final_generate.txt`.
  - Q43 asks about parabolic mirrors and spherical aberration in reflecting telescopes, which is beyond a basic "reflection of light" chapter.
  - Q39 asks "why a plane mirror reverses an image left-to-right rather than top-to-bottom".
    Its premise is misleading: a plane mirror really reverses front-to-back.
  - The detector only checks for duplicates. It does not check whether a question stays on topic or is correct.

## 9. Final checks

### What changed

- **`llm.py` now waits and retries on temporary errors.** If an error mentions "429",
  "RESOURCE_EXHAUSTED", "503" or "UNAVAILABLE", it waits 15, 30, 45 and then 60 seconds and tries again
  (up to 4 retries). It does not retry a per-day limit (an error containing "PerDay"), or any other error.
  The function name and arguments are the same, and `MODEL` is still `gemini-3.5-flash-lite`.
- An offline test with a fake API, with no real calls and waits set to 0 (`final_llm_retry_test.txt`), showed:
  - two busy errors, then success: 3 calls, then it returned the answer
  - always busy: 5 calls (1 + 4 retries), then it gave up
  - a per-day limit: 1 call, then it gave up at once
  - any other error: 1 call, then it gave up at once
- **The generator no longer crashes** when the call that writes new questions fails.
  It prints one short line, stops the rounds, and still prints the final "Accepted / Rejected / Review / Checked" line.
  Nothing else in the generator changed. This was not tested with a real failure, because you asked me not to run the generator.
- **`evaluate_detector.py` now counts judge calls correctly.** It counts results decided by "judge",
  "judge failed" and "numbers guard".
- `SLEEP_BETWEEN_CALLS` in `evaluate_pairs.py` is now 5.

### Regression test

Source: `final_regression_v2.txt`.

- **Correct: 9/10, LLM judge calls: 8.** Before the fix, the same run reported 7, because the call for Q7 was not counted.
- Q7 is still "review" by "numbers guard". The script counts it as wrong, because the expected label is "new".

### Public data with the current rules (flash-lite)

QQP: 49 judge calls, PAWS: 50. No call failed, and no retry was needed (`final_public_qqp.txt`, `final_public_paws.txt`).

Judge only, on all 50 pairs of each set. The current-rules numbers include the numbers guard; the rule version 2 numbers do not (it did not exist then).

| Data | Rules | Precision | Recall | Missed | False alarms | Review | Judge calls | Source |
|---|---|---|---|---|---|---|---|---|
| QQP | rule version 2 | 0.76 | 0.94 | 1 | 5 | 1 | 49 | `step5_public_judge_qqp.txt` |
| QQP | current | 0.74 | 1.00 | 0 | 6 | 2 | 49 | `final_public_qqp.txt` |
| PAWS | rule version 2 | 0.64 | 0.96 | 1 | 13 | 0 | 50 | `step5_public_judge_paws.txt` |
| PAWS | current | 0.60 | 1.00 | 0 | 16 | 0 | 50 | `final_public_paws.txt` |

The final design, (1.01, 0.50) with the guard on, all 50 pairs:

| Data | Precision | Recall | Missed | False alarms | Review | Judge calls | Source |
|---|---|---|---|---|---|---|---|
| QQP | 0.77 | 1.00 | 0 | 5 | 1 | 32 | `final_public_qqp.txt`, section 6 |
| PAWS | 0.60 | 1.00 | 0 | 16 | 0 | 50 | `final_public_paws.txt`, section 6 |

What this shows:
- **The current rules lean more towards "duplicate".** They catch every duplicate in both sets,
  but give more false alarms than rule version 2: 6 instead of 5 on QQP, and 16 instead of 13 on PAWS.
- **On QQP the final design saves calls.** Pairs below 0.50 skip the judge, so it uses 32 calls instead of 49.
  On PAWS every pair scores high, so all 50 go to the judge.
- **The numbers guard fired once** (QQP47, which became "review" instead of "duplicate").
  On PAWS it changed nothing.
- As before, QQP and PAWS use their own idea of "duplicate", not ours.

**The stronger model really is better on word-order traps.** Now that flash-lite also has
current-rule verdicts, the two models can be compared with the same rules on the same 18 PAWS pairs
(7 duplicate, 11 different). Source: `final_paws_model_compare.txt`.

| Judge | Rules | Precision | Recall | Missed | False alarms |
|---|---|---|---|---|---|
| gemini-3.8-flash | current | 0.67 | 0.86 | 1 | 3 |
| gemini-3.5-flash-lite | current | 0.44 | 1.00 | 0 | 9 |
| gemini-3.5-flash-lite | rule version 2 | 0.50 | 0.86 | 1 | 6 |

With the same rules, the stronger model made 3 false alarms instead of 9.
So the gain in section 8 comes from the model, not from the rules. It is still only 18 pairs.

### Cache safety

- The public verdicts were added to the same cache, because the prompt and model did not change.
  No test-pair verdict was lost or changed: 56 of 56 are present (`final_cache_check.txt`).
- `judge_cache.json` now holds 155 verdicts (56 test, 49 QQP, 50 PAWS).
  A copy is saved as `judge_cache_v3_with_public.json`. `judge_cache_v3.json` still holds only the 56 test verdicts.

### Clean demo database

- The old database (43 questions) was renamed to `questions_dev_43.db`. It was kept, not deleted.
- The new `questions.db` was built with `load_seed.py` and `build_clusters.py`:
  - **10 questions** (`demo_load_seed.txt`, `demo_db_check.txt`)
  - **3 clusters** (`demo_clusters.txt`): one with 8 questions, one with only Q6, and one with only Q7.
- Note: `load_seed.py` loads all 10 seed questions as they are. The seed set is the duplicate test set, so this
  "clean" database already contains its planned duplicates: Q2, Q3 and Q4 reword Q1, and Q10 is an exact copy of Q2.
  For a demo bank with no duplicates, you would load only Q1, Q5, Q6, Q7 and Q9 (and maybe Q8).
- The generator was not run.

### One extra thing to know

While checking that the edited files load, I imported `evaluate_detector.py` by mistake.
Its code runs on import, so it started the regression test and may have made a few judge calls before it stopped.
Nothing was saved, and no file or cache changed. It only used a little of the per-minute quota.

## 10. Held-out test (fresh pairs)

### What was tested

`fresh_pairs.json` has 26 new pairs: 14 duplicate and 12 different. They are on chapters
the rules were never tuned on: refraction, lenses, the human eye and electricity.

**Be honest about where these pairs come from.** They were written by the AI assistant that
helped design the system. They were written before the run, and the labels were not changed
after it. But the writer knew the rules, so this is not the same as pairs from an independent person.

The test was run **once**. No rule, line (threshold) or prompt was changed after seeing the result.
The run made 26 judge calls with no errors and no retries (`fresh_heldout.txt`).
The tune/test split printed in `fresh_heldout.txt` has no meaning here: the whole file is a test set.
The numbers below come from `fresh_heldout_final.txt`, which reads the saved verdicts and makes no LLM calls.

### Results on all 26 pairs

| Approach | Precision | Recall | Missed | False alarms | Review | Judge calls | Source |
|---|---|---|---|---|---|---|---|
| Final design (1.01, 0.50), guard on | 1.00 | 0.93 | 1 | 0 | 0 | 24 | `fresh_heldout_final.txt`, section 1 |
| Judge only | 1.00 | 1.00 | 0 | 0 | 0 | 26 | `fresh_heldout_final.txt`, section 1 |
| Old cascade (0.92, 0.75) | 0.80 | 0.57 | 6 | 2 | 0 | 10 | `fresh_heldout.txt`, section 2 |
| Embedding only, line 0.80 | 0.58 | 0.50 | 7 | 5 | 0 | 0 | `fresh_heldout.txt`, section 2 |
| Cross-encoder alone, line 0.5 | 0.50 | 0.21 | 11 | 3 | - | 0 | `fresh_heldout_cross_encoder.txt` |

- **The final design's only mistake is F5**: "What is myopia?" vs "Explain short-sightedness."
  The embedding score is 0.44, below the 0.50 line, so the pair is called "new" before the judge sees it.
  The judge itself said "duplicate" for this pair. This is the same kind of mistake as C4 in the 60 pairs:
  a paraphrase that needs world knowledge (myopia = short-sightedness), so the words do not overlap.
- **The judge got all 26 pairs right**, including the two opposite-case traps F15 and F16
  (embedding scores 0.99 to 1.00) and the four near-miss pairs.
- **The numbers guard never fired** (review 0). Both definition-versus-calculation pairs were already
  called "different" (F17 by the judge, F18 by the embedding line).
- **The cross-encoder did badly here** (recall 0.21). It scored all 3 number-changed pairs 0.00 to 0.02 and the
  2 low-overlap paraphrases 0.00, and it called both opposite-case traps duplicates (0.97, 0.98).

### How to read this

- 26 pairs is a small set. One pair moves recall by about 0.07 (1 of 14 duplicates; computed).
- The result agrees with the 60-pair test: the judge is accurate, and the 0.50 line costs one
  low-overlap paraphrase while saving 2 of 26 judge calls (computed: 26 − 24).

## 11. Version 1 frozen

Version 1 is saved as the git tag **`v1-two-gate`**
("Version 1: exact check + embedding search + LLM judge + numbers guard").
The full write-up is `REPORT.md` in the project folder; a one-page overview is `README.md`.

### What changed in this session

- **Git.** The folder became a git repository (branch `main`). A first commit, "Snapshot before final cleanup",
  saves everything as it was before this session's changes.
- **Step 1 (final checks)** was already done in the earlier session (section 9). Nothing was redone.
- **Held-out test** on 26 fresh pairs, run once (section 10). New files: `fresh_heldout.txt`,
  `fresh_heldout_cross_encoder.txt`, `fresh_heldout_final.txt`. Before the run, the judge cache was copied to
  `judge_cache_v3_before_fresh.json`. After it, `judge_cache.json` holds 181 verdicts (155 + 26 fresh);
  all 56 test-pair verdicts are unchanged.
- **Evidence that was only seen in chat, now saved** (no rule changes):
  - `score_table_seed10.txt`, `exact_check.txt` (no API calls)
  - `benchmark_run1.txt` to `benchmark_run3.txt`: embedding 4.2 to 4.8 ms per question; search in 100,000
    questions 23.57 to 25.82 ms
  - `benchmark_clusters_spread06.txt` (average random similarity 0.49) and `benchmark_clusters_spread04.txt` (0.58).
    At nprobe 5 the clustered search found the true closest match 200/200 and 192/200 times. In this numpy code it
    was not faster than brute force at nprobe 5 (9.42 ms vs 8.99 ms with spread 0.6); it was faster at nprobe 1 and 2.
  - `test_switch.txt`: brute force and clustered search gave the same labels on 4 candidates.
- **Folder clean-up.** Data in `data/`, evaluation scripts in `experiments/`, judge caches in
  `experiments/judge_caches/`. Paths are built from each file's own location. All checks passed afterwards
  (`verify_after_cleanup.txt`): every file compiles, `check_exact.py` and `score_table.py` give identical output,
  both pair files need 0 new judge calls, and the regression test gives 9/10 with 8 judge calls.
- **Configurable database path** (`store.set_db_path`) and a **tag filter** (`store.get_questions_by_tags`).
  The detector and judge never read tags.
- **`demo.py`** (`demo_output.txt`): on its own `demo.db`, 10 of 10 detector cases matched the expected label
  (2 exact duplicates, 3 semantic duplicates, 3 different, 2 tricky cases). The generation part accepted 3 of 3
  candidates. `questions.db` was not changed.
- **Small label fixes:** `evaluate_pairs.py` headings now show the real pair counts, and three experiment scripts
  print file names instead of full paths. Listed in `REPORT.md`, appendix.
- **No rule changed:** no threshold, judge prompt, detection or generation logic, or test label.
