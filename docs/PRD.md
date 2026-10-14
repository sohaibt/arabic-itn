# PRD: arabic-itn

Source idea: Arabic Voice Value Normalizer · <https://www.producthunt.com/products/premove-itn> · Fit score 8.9 · Pipeline ID oss-001

## 1\. One-line pitch

A small, local Python library and CLI that turns spoken-form Arabic ASR transcripts into exact values (phone numbers, amounts, dates, times, order IDs, emails) for voice-agent developers in MENA.

## 2\. Problem

  - Arabic voice agents get transcripts that read well but break the exact values downstream tools need. "خمسة صفر صفر..." is not a phone number. "ميتين وخمسين ريال" is not 250 SAR.
  - Users: Arabic voice-agent developers and small CX automation teams in Saudi, UAE and Egypt.
  - Thesis: Premove ITN (MIT, on Product Hunt 2026-09-14) showed that a generate-score-decode ITN layer helps voice agents, but it is English-only. Arabic needs its own rules for dialects, Arabic-Indic vs Western digits, gendered number words and code-switched English letters.
  - Web check: no packaged, MIT-licensed Arabic ITN library for voice agents turned up. NVIDIA's Arabic grammar ships under the Riva license. Soniox sells Arabic alphanumeric handling only inside its paid STT. A 2026 ACL paper still lists dialect, diacritics and gender polarity as open Arabic ITN failures.

## 3\. Competitors

  - Premove ITN: <https://github.com/premove-ai/premove-itn> (English-only contextual ITN, 435.6M params)
  - NVIDIA NeMo / Riva Arabic ITN: <https://docs.nvidia.com/nemo-framework/user-guide/24.12/nemotoolkit/nlp/text_normalization/wfst/wfst_text_normalization.html> and <https://catalog.ngc.nvidia.com/orgs/nvidia/riva/models/inverse_normalization_ar_ar/-> (heavy WFST stack, Riva license)
  - Soniox Arabic STT: <https://soniox.com/platform/arabic> (closed, paid, tied to its own ASR)
  - CUNY Arabic TN/ITN thesis: <https://academicworks.cuny.edu/gc_etds/5888> (research, not a package)

  

Why different: zero-dependency, MIT, works on any ASR's text, and built for voice-agent values (Gulf phones, SAR/AED, order IDs, code-switching), with a public test set.

## 4\. Money model

**Fully free** (MIT). It is a small library that runs inside the user's process; local-only is the privacy pitch. Paid country packs or a hosted endpoint can be revisited only after real adoption.

## 5\. MVP scope

**In v1:**

  

  - Arabic number words to digits (MSA plus common Gulf/Egyptian/Levantine forms, masculine/feminine, hundreds/thousands), and Arabic-Indic or Persian digits to Western digits.
  - Phone numbers: digit-by-digit speech, "double" forms, and Saudi (+966/05) and UAE (+971/05) shapes, output as E.164.
  - Money: SAR, AED, EGP, USD words ("ريال", "درهم", "جنيه", "دولار", "هللة", "فلس") to 250 SAR style output.
  - Dates and times: "الساعة تلاتة ونص" to 15:30/03:30, plus day/month names to ISO dates when the year is given.
  - Spelled emails and order IDs: spoken English and Arabic letter names plus "at"/"آت"/"dot"/"نقطة" to a.b@x.com or AB-1234.
  - normalize(text) -\> {text, spans:\[{type, raw, value}\]} API, a arabic-itn CLI (stdin to JSON), and a test set of 200 or more utterance/expected pairs run by python -m unittest.

  

**Not in v1:** a learned contextual scorer or model weights, audio input, HTTP server, Pipecat/LiveKit/Vapi plugins, address parsing, full dialect coverage, diacritics restoration, a hosted benchmark site, and paid packs.

## 6\. Tech choice

Python library plus CLI, standard library only (re, json, unicodedata), packaged with pyproject.toml. Python is where voice-agent stacks (Pipecat, LiveKit Agents) live, and having no dependencies keeps it easy to drop into any pipeline.

## 7\. Name

arabic-itn. GitHub check: not in STATE/repos.json. npm check: npm view arabic-itn returned 404 Not Found. Not in the pipeline's Proposed Name column.

## 8\. Promotion plan

  - Product Hunt launch with a before/after GIF of transcripts from real ASR.
  - GitHub topics: arabic, nlp, asr, inverse-text-normalization, voice-agents, speech-to-text, mena.
  - Mastering Product HQ Substack angle: "Your Arabic voice agent reads well and still books the wrong number": exact values as the hidden quality metric for voice AI.
  - Portfolio fit: it pairs with agent-pm (eval and production safety for agents) as a concrete eval fixture, and with strategy-mcp/founder-mode as part of the owner's MENA-focused builder story.

## 9\. Build size

Small. Yes, "In v1" fits in a 3-hour automated build: rule-based stdlib code plus a fixture-driven test set, with no model training.
