# Annotation Collection Guide

## What To Use First

Start with:

`paper/data/pilot_annotation_sheet.csv`

This file has 30 word pairs. It is small enough for a pilot round and balanced across high, medium, and low expected similarity bands. The hidden sampling information is not shown to annotators.

Use the full file only after the pilot:

`paper/data/annotation_sheet.csv`

## Option A: Google Sheets

1. Open Google Drive.
2. Click `New` -> `File upload`.
3. Upload `paper/data/pilot_annotation_sheet.csv`.
4. Open it with Google Sheets.
5. Rename it to `Zhasyryn Soz Pilot Annotation`.
6. Freeze the first row.
7. Add data validation to `human_score_0_10`:
   - criteria: number;
   - between 0 and 10;
   - reject invalid input.
8. Share the sheet with annotators or make one copy per annotator.

Recommended setup: one copy per annotator. This avoids people seeing each other's scores.

## Option B: Google Form

Google Forms is cleaner for annotators but slower to create manually.

1. Create a new Google Form.
2. Add the task instructions from `paper/drafts/annotation_protocol.md`.
3. For each word pair, add a linear scale question from 0 to 10.
4. Use the question text:
   `word_a - word_b`
5. Add an optional short-answer question at the end:
   `Were any words unfamiliar or unclear?`
6. Export responses to Google Sheets.

For 30 pilot pairs, Google Form is manageable. For 150 pairs, Google Sheets is faster unless you automate form creation.

## Pilot Round

Goal:

- 5 annotators;
- 30 pairs;
- 0-10 semantic similarity score;
- optional notes.

Who to ask:

- native Kazakh speakers;
- preferably people comfortable reading Kazakh Cyrillic;
- avoid only NLP experts, because the paper needs ordinary speaker intuition.

Message to send:

> I am collecting ratings for a Kazakh NLP research project. Please rate how similar each pair of Kazakh words is in meaning from 0 to 10. This should take about 10 minutes. Do not search online unless a word is completely unfamiliar; if a word is unclear, leave a note.

## After Pilot

Check:

- Are many scores missing?
- Are many words marked unfamiliar?
- Do annotators understand the 0-10 scale?
- Are some pairs confusing or culturally too narrow?
- Do annotators use different parts of the scale, or does everyone give only middle scores?

Then revise the pair list before the full round.

## Full Annotation Round

Recommended target:

- 150 pairs;
- at least 3 annotators per pair;
- preferably 5 annotators per pair.

Minimum usable target:

- 150 pairs;
- 3 annotators;
- 450 total ratings.

Better target:

- 150 pairs;
- 5 annotators;
- 750 total ratings.

## How To Store Results

Save each annotator response as:

`paper/data/annotations_raw/annotator_01.csv`

After collecting responses, combine them into one file:

`paper/data/annotations_combined.csv`

The combined file should eventually have:

- `annotator_id`
- `word_a`
- `word_b`
- `human_score_0_10`
- `notes`

