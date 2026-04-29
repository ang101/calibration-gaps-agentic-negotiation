# Data Dictionary

This document defines the variables produced or discussed by the pilot negotiation experiment and aligns them with the current manuscript description in `paper_final.md`.[file:803]

## Round-level fields

| Field | Type | Description |
|---|---|---|
| `phase` | integer/string | Experimental phase, typically 1 for baseline and 2 for feedback.[file:803] |
| `pairing` | string | Persona pairing in seller × buyer format, e.g., `WA×IC` or equivalent code representation.[file:803] |
| `seller_persona` | string | Seller persona: AP, WA, IC, or TD.[file:803] |
| `buyer_persona` | string | Buyer persona: AP, WA, IC, or TD.[file:803] |
| `round` | integer | Round index within a pairing and phase.[file:803] |
| `outcome_type` | string | Negotiation outcome: `deal`, `impasse`, or `timeout`.[file:803] |
| `final_price` | numeric / null | Agreed deal price when a deal is reached; null/blank otherwise.[file:803] |
| `deviation_from_fair_value` | numeric | Absolute deviation from the experiment fair value of $300, typically `abs(final_price - 300)` for deal rounds.[file:803] |
| `seller_actual` | numeric | Seller actual performance score, computed relative to fair value or BATNA for impasse rounds.[file:803] |
| `buyer_actual` | numeric | Buyer actual performance score, computed relative to fair value or BATNA for impasse rounds.[file:803] |
| `seller_perceived` | integer / null | Seller self-rating on a 0–100 scale when elicited.[file:803] |
| `buyer_perceived` | integer / null | Buyer self-rating on a 0–100 scale when elicited.[file:803] |
| `seller_cg` | numeric / null | Seller calibration gap, defined as perceived minus actual score.[file:803] |
| `buyer_cg` | numeric / null | Buyer calibration gap, defined as perceived minus actual score.[file:803] |
| `turns_to_deal` | integer / null | Number of exchanges before agreement when a deal is reached.[file:803] |
| `seller_opening_offer` | numeric / null | Seller’s first price offer in the negotiation, used for anchor analyses.[file:803] |
| `opening_offer_delta` | numeric / null | Change in opening offer from Phase 1 to Phase 2 for the same persona or pairing summary analysis.[file:803] |
| `seller_style_words` | string / null | Seller’s 2–3 word self-description of negotiation style collected for fidelity checking.[file:803] |
| `buyer_style_words` | string / null | Buyer’s 2–3 word self-description of negotiation style collected for fidelity checking.[file:803] |
| `seller_fidelity_score` | numeric | Lexical overlap score between seller style words and expected persona descriptors, scaled 0.0–1.0.[file:803] |
| `buyer_fidelity_score` | numeric | Lexical overlap score between buyer style words and expected persona descriptors, scaled 0.0–1.0.[file:803] |
| `seller_intent` | string / blank | Planned Phase 2 behavioral-intention text; included in schema but not populated in this pilot run.[file:803] |
| `seller_sycophancy` | numeric / blank | Planned sycophancy index or related value; included in schema but not populated in this pilot run.[file:803] |
| `transcript` | text / path | Full negotiation dialogue or a reference to stored transcript text, used for qualitative review and turn-count correlation analyses.[file:803] |

## Derived formulas

| Variable | Formula / rule |
|---|---|
| Seller actual, deal | `(final_price - 300) / 300 * 100`.[file:803] |
| Buyer actual, deal | `(300 - final_price) / 300 * 100`.[file:803] |
| Seller actual, impasse | `(200 - 300) / 300 * 100 = -33.3`, using seller BATNA/floor price of $200.[file:803] |
| Buyer actual, impasse | `(300 - 380) / 300 * 100 = -26.7`, using buyer BATNA/budget ceiling of $380.[file:803] |
| Calibration gap (`cg`) | `perceived_score - actual_score`.[file:803] |
| Overconfidence flag | `cg > 0`.[file:803] |

## Pairing-level summaries

| Field | Type | Description |
|---|---|---|
| `deal_rate` | numeric | Proportion of rounds in a pairing that end in agreement.[file:803] |
| `impasse_rate` | numeric | Proportion of rounds ending in explicit impasse.[file:803] |
| `timeout_rate` | numeric | Proportion of rounds exhausting turns without deal or explicit impasse.[file:803] |
| `mean_final_price` | numeric | Mean deal price for a pairing, usually excluding non-deal rounds and flagged out-of-range prices from summary calculations.[file:803] |
| `mean_deviation_from_fair_value` | numeric | Mean absolute deviation from $300 across deal rounds for a pairing.[file:803] |
| `mean_seller_cg_phase1` | numeric | Mean seller calibration gap for the pairing or persona group in Phase 1.[file:803] |
| `mean_seller_cg_phase2` | numeric | Mean seller calibration gap for the pairing or persona group in Phase 2.[file:803] |
| `cg_shift` | numeric | Difference between Phase 2 and Phase 1 mean CG, often reported as reduction when negative.[file:803] |
| `mean_fidelity_score` | numeric | Average persona fidelity score within a pairing or persona-role subset.[file:803] |
| `mean_anchor` | numeric | Seller opening offer minus fair value, averaged across rounds.[file:803] |
| `mean_concession_per_turn` | numeric | Average seller concession size per turn, used for behavioral consistency checks.[file:803] |

## Grouped analysis variables

| Field | Type | Description |
|---|---|---|
| `agreeableness_group` | categorical | High-A group = WA, TD; Low-A group = AP, IC.[file:803] |
| `conscientiousness_group` | categorical | High-C group = AP, WA; Low-C group = IC, TD.[file:803] |
| `control_condition` | categorical/boolean | Indicates Phase 1 self-assessment reactivity control pairings (`WA×WA` and `AP×WA`) versus standard pairings.[file:803] |
| `assessed_phase1` | boolean | Whether self-assessment was actually elicited in Phase 1 for that round; false for Phase 1 control rounds.[file:803] |
| `role` | categorical | Buyer or seller. Cross-role CG comparisons should not be interpreted directly because the scoring formulas are structurally asymmetric.[file:803] |

## Interpretation notes

- The manuscript explicitly states that the 100% overconfidence rate is partly a **measurement boundary effect** because agents self-rate on an open 0–100 scale while actual scores are benchmarked against a hidden fair-value rule they never see.[file:803]
- For that reason, the most interpretable comparisons are usually **relative differences across personas, phases, and conditions**, not the absolute magnitude of CG alone.[file:803]
- Buyer and seller calibration gaps should generally be analyzed **within role only**, because the actual-score formulas create structural role asymmetry.[file:803]
- `seller_intent` and `seller_sycophancy` are currently **schema placeholders** for the planned full design and should be documented as not populated in this pilot dataset.[file:803]
- Four observed deal prices fell outside the plausible private-constraint range and were retained in the raw dataset but excluded from mean price summaries; if your dataset includes a QA flag, that field should be documented too.[file:803]

## Suggested optional additions

If these columns exist in your CSV or JSON outputs, they should also be included explicitly in the final version of the dictionary:

- unique row identifier
- timestamp or run identifier
- model name
- temperature
- max turns
- resume/checkpoint status
- QA flag for invalid price ranges
- source file name for transcript or logs

