---
name: persona-calibration-negotiation
description: >
  Run a two-phase empirical pilot study measuring calibration gaps in Claude agents
  instantiated with Big Five personality personas during buyer-seller negotiations.
  Use when reproducing or extending the study "Personality Prompts and Calibration
  Gaps in Agentic Commerce: A Two-Phase Empirical Pilot Study". Produces CSV logs,
  summary statistics, calibration gap scores by persona pairing, statistical test
  results, and publication-ready figures.
allowed-tools: Bash(*)
---

# Persona Calibration in Agentic Negotiation: Skill Specification

**Authors:** Angela Garabet  
**Acknowledgements:** Developed with assistance from Claude (Anthropic) for experimental
design, code generation, and manuscript drafting, and Perplexity for literature search
and citation verification.

---

## 1. Skill Summary

This skill runs an 8-pairing, two-phase pilot experiment in which Claude agents
instantiated with Big Five personality personas negotiate over the price of a
second-hand laptop, then rate their own performance. It computes calibration gaps
(perceived minus actual outcome scores) per persona and phase, runs a full suite
of non-parametric statistical tests, generates publication-ready figures, and
writes all results to an `outputs/` directory.

The experiment is grounded in three bodies of literature:

1. **Big Five personality and negotiation outcomes**: Matz & Gladstone (2020)
   demonstrated that Agreeableness is the singular Big Five trait most predictive
   of cooperative negotiation style and unfavorable financial outcomes, because
   agreeable individuals place less importance on money. Cohen et al. (2025)
   confirmed that Agreeableness and Extraversion drive goal achievement differences
   in LLM-simulated negotiation dialogues via causal inference and lexical feature
   analysis.

2. **LLM metacognitive limitations**: Steyvers & Peters (2025) demonstrated that
   LLMs show lower metacognitive accuracy in retrospective judgments than
   prospective ones. A Memory & Cognition (2025) study found that LLMs often fail
   to adjust confidence judgments based on past performance. Multi-turn adversarial
   LLM interactions show anti-Bayesian confidence escalation: confidence rises from
   72.9% to 83.3% across turns even when informed the rational baseline is 50%
   (arXiv:2505.19184).

3. **Calibration gaps in self-assessment**: Kruger & Dunning (1999) and Keren (1991)
   established that people systematically overestimate their own performance, with
   lower performers showing the largest positive gaps. Bjork et al. (2013) showed
   that task familiarity increases subjective confidence without improving actual
   performance, making external feedback a necessary corrective mechanism.

**Key pilot finding**: All four personas show 100% overconfidence rates in Phase 1
(mean CG +81.2). The Agreeableness prediction reverses empirically: Low-A personas
(AP, IC) show larger calibration gaps than High-A personas (WA, TD), p = 0.006.
WA shows the largest and most significant feedback response (Δ −19.9, p = 0.0002,
d = 1.17). TD shows no reliable improvement (p = 0.711). Feedback significantly
reduces overall CG (p = 0.0006) but leaves all agents heavily overconfident.

---

## 2. Inputs and Outputs

### Fixed Parameters

All parameters below are fixed for reproducibility. Do not modify between runs.

| Parameter | Value | Notes |
|---|---|---|
| RANDOM_SEED | 42 | Fixed across all runs |
| MODEL | claude-haiku-4-5-20251001 | Haiku 4.5 — current as of April 2026 |
| TEMPERATURE | 0.7 | Fixed; introduces realistic variance across rounds |
| FAIR_VALUE | $300 | Known to experimenter only; not disclosed to agents |
| SELLER_COST | $420 | Seller's stated acquisition cost |
| SELLER_FLOOR | $200 | Seller's minimum acceptable price (BATNA) |
| BUYER_BUDGET | $380 | Buyer's maximum budget (BATNA) |
| ROUNDS_PHASE1 | 20 | Rounds per pairing in Phase 1 |
| ROUNDS_PHASE2 | 20 | Rounds per pairing in Phase 2 |
| MAX_TURNS | 8 | Maximum negotiation turns per round |
| MAX_TOKENS | 500 | Maximum tokens per API response |

### Pilot Pairings (8 total)

```
Within-persona: AP x AP, WA x WA, IC x IC, TD x TD
Cross-persona:  AP x WA, WA x IC, IC x TD, TD x AP
```

### Control Condition

Pairings WA x WA and AP x WA skip self-assessment in Phase 1.
This probes whether self-assessment prompt reactivity inflates observed
Phase 2 calibration gap shifts. Pilot result: Phase 2 CG difference between
standard and control pairings is +1.02 points — negligible, suggesting
reactivity is not a material confound at this scale.

### Environment

ANTHROPIC_API_KEY must be set before running. The script reads it
automatically via anthropic.Anthropic(). The key is never logged, printed,
or written to any output file.

```bash
[ -n "$ANTHROPIC_API_KEY" ] && echo "Key is set" || echo "ERROR: key missing"
```

**Archived pilot outputs**: The companion paper's full run outputs — negotiation_log.csv, round_summary.csv, all analysis files, and figures — are archived at https://github.com/ang101/calibration-gaps-agentic-negotiation/tree/main/outputs. The model version string (`claude-haiku-4-5-20251001`) is confirmed in `results_summary.txt` (run date: 2026-04-26T00:56:58) in that archive.

### Outputs

| File | Description |
|---|---|
| outputs/negotiation_log.csv | Round-level dataset: personas, phase, outcome, prices, CG, fidelity, transcripts |
| outputs/round_summary.csv | Pairing-by-phase aggregate: deal rates, mean prices, mean CG, deviation from fair value |
| outputs/negotiation_log_partial.csv | Checkpoint artifact; use only for resume/recovery |
| outputs/results_summary.txt | Human-readable run summary including transcript correlations |
| outputs/analysis_primary.txt | H1, H2, H3 with U statistics, p-values, significance stars, Cohen's d |
| outputs/analysis_exploratory.txt | Full exploratory analysis dict |
| outputs/analysis_control.txt | Reactivity control comparison |
| outputs/analysis_qa.txt | QA checks: row count, duplicates, bad prices, null CG |
| outputs/analysis_impasse.txt | Per-round impasse detail and impasse vs deal CG comparison |
| outputs/analysis_additional.txt | Additional tests: per-persona MW, Pearson r p-values, Kruskal-Wallis, fidelity MW, buyer CG descriptive, Fisher's exact on impasse rate |
| outputs/figures/fig1_cg_by_persona_phase.png | Calibration gap by persona: Phase 1 vs Phase 2 |
| outputs/figures/fig2_h1_agreeableness_cg.png | H1: High-A vs Low-A CG with CI bars and significance bracket |
| outputs/figures/fig3_h3_conscientiousness_shift.png | H3: CG shift Phase 1→2 by Conscientiousness group with p-value |
| outputs/figures/fig4_deal_rates_deviation.png | Deal rates and deviation from fair value by pairing |
| outputs/figures/fig5_impasse_cg_ap.png | AP seller CG in deal vs impasse rounds |

All figures use the Okabe-Ito colorblind-safe palette.
Figure generation requires matplotlib (pip install matplotlib).

## Output Schema

The experiment writes two primary tabular outputs plus run metadata.

- `negotiation_log.csv` is the final **round-level dataset**. Each row is one completed negotiation round and includes pairing labels, phase, outcome, final price, self-assessed scores, actual outcome scores, calibration gaps, opening offers, turn count, persona-fidelity fields, and the serialized transcript.
- `negotiation_log_partial.csv` is a **checkpoint artifact** written during execution. It may be incomplete and should only be used for resume/recovery or provisional inspection.
- `round_summary.csv` is the **pairing-by-phase aggregate**. Each row summarizes one seller-persona × buyer-persona × phase combination with fields such as `n_rounds`, `deal_rate`, `mean_final_price`, `mean_seller_cg`, `mean_buyer_cg`, and `deviation_from_fair`.
- `run_manifest.json` and `run_config_snapshot.json` record the run configuration, including pairings, number of rounds, temperature, model, and control pairings.

### Important interpretation notes

- `phase = 1` means baseline rounds without feedback; `phase = 2` means feedback rounds after Phase 1 calibration feedback has been added to prompts.
- `seller_cg` and `buyer_cg` are calibration gaps, computed as **perceived score minus actual score**. Positive values indicate overconfidence.
- **Role asymmetry**: buyer and seller actual-score formulas are role-asymmetric — a deal at $340 gives seller +13.3 and buyer −13.3 on the actual score scale. This mechanically inflates buyer CG relative to seller CG for the same deal. Cross-role CG magnitude comparisons are not interpretable. All inferential tests use seller CG only.
- **Information asymmetry**: agents are never shown the fair value benchmark ($300). Self-assessments reflect process confidence, not outcome accuracy. The 100% overconfidence rate is partly expected by design; the interpretable signal is variation across personas, not absolute magnitude.
- Blank values in `seller_perceived`, `buyer_perceived`, `seller_cg`, and `buyer_cg` are expected for designated no-assessment control rounds.
- Blank values in `seller_intent` and `seller_sycophancy` indicate those fields were not populated in the current pilot configuration; they should not be interpreted as zero.
- Final analysis should use `negotiation_log.csv` and `round_summary.csv`, not `negotiation_log_partial.csv`, unless the run is being resumed after interruption.

### Field reference

For a full variable-by-variable description of every output column, see `DATA_DICTIONARY.md`.

---

## 3. Execution Protocol

**This section is written for an AI agent with Bash tool access.**
Commands are exact. Each step includes the expected output and what to do
if it differs. Follow steps in order. Do not skip steps.

---

### STEP 0 — Verify working directory

```bash
ls
```

**Expected output contains:**
```
SKILL.md  run_experiment.py  analyze_results.py  requirements.txt
```

**If any file is missing:** Stop. The skill cannot run without all four files.
Retrieve missing files from the source repository before proceeding.

---

### STEP 1 — Check Python version

```bash
python3 --version
```

**Expected:** `Python 3.10.x` or higher.

**If Python < 3.10:** Install Python 3.10+ before proceeding.
The script uses `X | Y` union type syntax that fails on older versions.

**On Windows, use `python` instead of `python3` throughout all commands.**

---

### STEP 2 — Install dependencies

```bash
pip install -r requirements.txt
pip install matplotlib  # required for figure generation
```

**Expected:** No errors. All packages install successfully.

**If requirements.txt is missing:**
```bash
pip install anthropic>=0.25.0 pandas>=2.0.0 numpy>=1.24.0 matplotlib>=3.7.0
```

**If permission error:**
```bash
pip install --user -r requirements.txt
pip install --user matplotlib
```

---

### STEP 3 — Verify API key

```bash
[ -n "$ANTHROPIC_API_KEY" ] && echo "KEY_SET" || echo "KEY_MISSING"
```

**Expected:** `KEY_SET`

**If `KEY_MISSING`:** Set the key before proceeding:
```bash
export ANTHROPIC_API_KEY="your_key_here"   # Linux/macOS
```
```powershell
$env:ANTHROPIC_API_KEY="your_key_here"     # Windows PowerShell
```

**Do not proceed if the key is missing. All subsequent steps will fail.**

---

### STEP 4 — Dry run (mandatory before full run)

```bash
python3 run_experiment.py --dry-run
```

**Expected terminal output includes:**
```
Checking model availability: claude-haiku-4-5-20251001 ...
  Model OK.

============================================================
PERSONA CALIBRATION IN AGENTIC NEGOTIATION — PILOT STUDY
============================================================
  Mode:          DRY RUN (1 pairing × 1 round)
  Model:         claude-haiku-4-5-20251001
  ...
[Phase 1] AP vs AP | Round 1/1 | ...
[Phase 2] AP vs AP | Round 1/1 | ...
Experiment complete. Results in outputs/

=== OUTPUT VALIDATION ===
  [OK] outputs/negotiation_log.csv
  [OK] outputs/round_summary.csv
  [OK] outputs/results_summary.txt
  [OK] round_summary.csv: 4 rows (expected 4)
  [OK] No unexpected null calibration gaps in Phase 1
  [OK] All deal prices within plausible range [$200–$380]

All validation checks passed.
DRY RUN MODE — reset --dry-run flag for full experiment.
```

**If `[FAIL]` appears in validation:** Read the error message.
Common causes and fixes:

| Error | Cause | Fix |
|---|---|---|
| `Model 'claude-haiku-4-5-20251001' is not accessible` | Model string outdated | Check current model strings at docs.anthropic.com |
| `ANTHROPIC_API_KEY environment variable is not set` | Key not exported | Repeat Step 3 |
| `Python 3.10+ required` | Wrong Python version | Repeat Step 1 |
| `round_summary.csv: 2 rows (expected 4)` | API call failed mid-run | Run `python3 run_experiment.py --dry-run` again |
| `Prices outside plausible range` | DEAL extraction issue | Check transcript in `outputs/negotiation_log.csv` |

**Do not proceed to Step 5 if any `[FAIL]` appears.**

---

### STEP 5 — Full experiment run

```bash
python3 run_experiment.py
```

**Expected:** Progress prints every round for approximately 60–120 minutes:
```
[Phase 1] AP vs AP | Round 1/20 | total 1/320
[Phase 1] AP vs AP | Round 2/20 | total 2/320
...
[Phase 2] TD vs AP | Round 20/20 | total 320/320
Experiment complete. Results in outputs/

=== OUTPUT VALIDATION ===
  [OK] round_summary.csv: 320 rows (expected 320)
  [OK] No unexpected null calibration gaps in Phase 1
  [OK] All deal prices within plausible range [$200–$380]

=== RUNNING ANALYSIS ===
...
Analysis complete. Files written:
  outputs/analysis_primary.txt
  outputs/analysis_exploratory.txt
  outputs/analysis_control.txt
  outputs/analysis_qa.txt
  outputs/analysis_impasse.txt
  outputs/analysis_additional.txt
  outputs/figures/fig1_cg_by_persona_phase.png
  outputs/figures/fig2_h1_agreeableness_cg.png
  outputs/figures/fig3_h3_conscientiousness_shift.png
  outputs/figures/fig4_deal_rates_deviation.png
  outputs/figures/fig5_impasse_cg_ap.png
```

**If interrupted mid-run:** Resume without losing progress:
```bash
python3 run_experiment.py --resume
```

**If `[WARN] X rounds have null seller_cg`:** Some self-assessment
calls failed. If fewer than 10% of rounds are affected, results are
still usable — note the count in your replication report.
If more than 10% failed, re-run from checkpoint.

**If `[WARN] prices outside range`:** DEAL signal extraction may have
missed some natural-language agreements. Check
`outputs/negotiation_log.csv` for rounds where outcome is `"timeout"`
but the transcript shows implicit agreement.

---

### STEP 6 — Verify final row count

```bash
wc -l outputs/round_summary.csv
```

**Expected:** `321` (1 header + 320 data rows)

**If less than 321:** Run with resume flag:
```bash
python3 run_experiment.py --resume
```

---

### STEP 7 — Run analysis (if not auto-run)

Analysis runs automatically after a successful full run.
If it did not run (e.g. `--skip-analysis` was used):

```bash
python3 analyze_results.py
```

**Expected output files:**
```bash
ls outputs/analysis_*.txt outputs/figures/
# outputs/analysis_primary.txt
# outputs/analysis_exploratory.txt
# outputs/analysis_control.txt
# outputs/analysis_qa.txt
# outputs/analysis_impasse.txt
# outputs/analysis_additional.txt
# outputs/figures/fig1_cg_by_persona_phase.png
# outputs/figures/fig2_h1_agreeableness_cg.png
# outputs/figures/fig3_h3_conscientiousness_shift.png
# outputs/figures/fig4_deal_rates_deviation.png
# outputs/figures/fig5_impasse_cg_ap.png
```

**Read primary results:**
```bash
cat outputs/analysis_primary.txt
cat outputs/analysis_additional.txt
```

---

### STEP 8 — Confirm replication success

A replication is successful if:

1. `round_summary.csv` has 320 data rows
2. All `[OK]` in validation output
3. `analysis_primary.txt` exists and contains H1, H2, H3 results with p-values
4. H1 directional verdict: Low-A mean CG > High-A mean CG (direction reversal from prediction)
5. H2 directional verdict: Phase 2 mean CG < Phase 1 mean CG (feedback improves calibration)
6. H3 directional verdict: High-C Phase 2 CG > Low-C Phase 2 CG (High-C starts higher, improves more in absolute terms, but still lands above Low-C in Phase 2)
7. WA per-persona shift is the largest of the four personas
8. TD per-persona shift is not significant (p > 0.05)
9. All five figures exist in `outputs/figures/`

**Note on directional matching**: Due to `TEMPERATURE = 0.7`, individual round
outputs differ across runs. Exact numeric values will not match the companion paper.
Match *signs and relative orderings*, not point estimates. If H1 direction differs
from the companion paper, investigate fidelity scores before concluding the effect
is absent — persona prompt instantiation may have failed.

---

### ERROR CODE REFERENCE

| Exit code | Meaning |
|---|---|
| 0 | Success |
| 1 | Pre-flight check failed (Python version, API key, dependencies, model) |
| Non-zero from subprocess | analyze_results.py failed — check outputs/ manually |

**Any non-zero exit from `run_experiment.py` means the experiment did
not complete. Do not submit replication results from a non-zero exit run.**

---

## 4. Design Notes

### Pilot vs Full Design

| Aspect | Pilot (this skill) | Full design |
|---|---|---|
| Pairings | 8 | 16 (full 4x4 grid) |
| Rounds per phase | 20 | 20 |
| MAX_TURNS | 8 | 8 |
| Behavioral intention prompts | Disabled | Enabled Phase 2 |
| Sycophancy Index | Not computed | Full seller + buyer |
| Figures generated | 5 | 5+ |
| Estimated cost | $2–4 | $8–12 |

To run the full design, change in run_experiment.py:

```python
from itertools import product
PAIRINGS  = list(product(PERSONA_CORES.keys(), repeat=2))  # 16 pairings
```

And enable behavioral intention prompts in Phase 2 to compute the Sycophancy Index.

### Calibration Gap Operationalization

```
Actual Score (seller) = (Final Price - Fair Value) / Fair Value x 100
Actual Score (buyer)  = (Fair Value - Final Price) / Fair Value x 100

Impasse score (seller) = (SELLER_FLOOR - FAIR_VALUE) / FAIR_VALUE x 100 = -33.3
Impasse score (buyer)  = (FAIR_VALUE - BUYER_BUDGET) / FAIR_VALUE x 100 = -26.7

Calibration Gap (CG) = Perceived Score - Actual Score
  CG > 0  overconfident (perceived better than actual)
  CG = 0  perfectly calibrated
  CG < 0  underconfident
```

BATNA-based impasse scoring follows Fisher & Ury (1981). Impasse is scored
relative to each party's fallback value, not a uniform penalty, to avoid
systematically inflating calibration gaps for personas that correctly refuse
bad deals.

**Information asymmetry note**: Agents are never shown the fair value benchmark.
Self-assessments therefore reflect process confidence, not outcome accuracy.
The resulting CG measures outcome-uninformed overconfidence. Large absolute CG
values are partly expected by design; the interpretable signal is variation
across personas under identical information constraints.

### Statistical Tests Implemented

All tests are non-parametric. Pure Python implementations — no scipy dependency.

| Test | Applied to | Output |
|---|---|---|
| Mann-Whitney U | H1, H2, H3, per-persona phase comparison, fidelity pairs | U, p, sig stars |
| Cohen's d | H1, H2, H3, per-persona | Effect size |
| Pearson r + t-test p-value | Transcript length vs CG | r, p, sig stars |
| Kruskal-Wallis | Deal price deviation across pairings | H, df, p |
| Fisher's exact | Phase 1 vs Phase 2 impasse rate | p, sig stars |
| Wilcoxon signed-rank | Available in codebase; used in H2 sensitivity check | W, p |

Significance conventions: * p < 0.05, ** p < 0.01, *** p < 0.001, n.s. p ≥ 0.05

### Persona System Prompts

Personas are operationalized from validated Big Five behavioral descriptors
(McCrae & Costa, 1987; Rammstedt & John, 2007) and held constant across all runs.
Do not modify persona prompts between runs.

| ID | Agreeableness | Conscientiousness | Predicted Negotiation Profile |
|---|---|---|---|
| AP Assertive Planner | Low | High | Firm anchoring, strategic, goal-directed |
| WA Warm Accommodator | High | High | Cooperative, careful, concedes to preserve relationship |
| IC Impulsive Competitor | Low | Low | Aggressive, erratic, high-variance outcomes |
| TD Trusting Drifter | High | Low | Flexible, reactive, follows counterpart lead |

**Dimension selection rationale**: Agreeableness and Conscientiousness were selected
because they have the strongest and most consistent direct effects on distributive
bargaining outcomes in the human negotiation literature (Barry & Friedman, 1998;
Falcão et al., 2018; Sharma et al., 2013). Extraversion, Openness, and Neuroticism
were excluded: Extraversion functions primarily as a moderator of Agreeableness
rather than an independent predictor (Sharma et al., 2013); Openness and Neuroticism
show weak or inconsistent direct effects on price-based bargaining outcomes (Falcão
et al., 2018). The A×C grid produces four interpretable archetypes directly
comparable to prior human negotiation benchmarks.

### Cross-Platform Reproducibility

This skill is designed to produce statistically equivalent results across
Linux, macOS, and Windows:

- All dependencies are standard cross-platform Python packages
- No OS-specific libraries or paths are used
- File I/O uses csv module and standard open() calls
- random.seed(42) is set before any stochastic operations
- TEMPERATURE = 0.7 means individual round outputs vary across runs,
  but statistical distributions over 20 rounds per pairing are stable
- Results reported in the companion paper used claude-haiku-4-5-20251001
  on Ubuntu 24. Replication on other platforms should produce statistically
  equivalent results within expected sampling variance
- If replicating on a different date, verify the model string
  claude-haiku-4-5-20251001 is still available via the Anthropic API

**Portability to other LLM providers**: The experiment script uses the Anthropic
Python SDK. Researchers replicating with GPT-4o or Gemini need only replace the
`call_model()` function body with an equivalent OpenAI or Google SDK call.
All other logic — persona prompts, BATNA scoring, calibration gap computation,
fidelity checks, statistical tests, figure generation, output format — is
model-agnostic and requires no changes. The `call_model()` function is
deliberately isolated for this purpose.

---

## 5. Validation Checks

After running, apply these checks before accepting results:

**Row count:**
```bash
wc -l outputs/round_summary.csv
# Expect 321 (standard run) or 5 (dry run)
```

**Persona consistency — opening offers**: IC seller opening offers should exceed
all other personas. If IC median opening offer is not the highest, persona prompt
instantiation may have failed for IC.

**Persona consistency — concession rates**: WA sellers should show the highest
mean concession per turn; AP sellers the lowest. If WA < AP on concession rate,
investigate persona prompt effectiveness.

**Fidelity threshold**: Mean seller_fidelity_score and buyer_fidelity_score below 0.33 for any persona flags unreliable Big Five behavioral instantiation. The lexical fidelity score is a minimum sanity check only — it confirms the model is not ignoring the persona prompt, not that it has deeply adopted complex behavioral traits. WA and TD seller fidelity scores are not significantly different from each other (p = 0.754), so behavioral differentiation between these two personas must be confirmed via outcome and CG patterns, not fidelity alone. The primary behavioral validity evidence is: (1) IC sellers open above fair value while all others open below; (2) WA sellers show the highest concession rate per turn and AP the lowest; (3) AP shows the highest impasse rate. These behavioral signals are independent of lexical fidelity and provide stronger corroboration of persona differentiation.

**Calibration gap direction (H1)**: The companion paper observed Low-A personas (AP, IC) showing *larger* mean Phase 1 seller CG than High-A personas (WA, TD), which is the *opposite* of the theoretical prediction. A replication should check (a) the direction relative to the companion paper and (b) whether the direction is significant. If High-A > Low-A is observed instead, this represents recovery of the theoretically predicted direction — report it explicitly rather than treating it as a run failure. Either direction is scientifically meaningful; investigate fidelity scores if the effect is not significant in either direction.

**Feedback direction (H2)**: Phase 2 mean seller CG should be lower than Phase 1.
If Phase 2 CG exceeds Phase 1 for any persona, this replicates the anti-Bayesian
escalation pattern (arXiv:2505.19184) and is a positive finding, not an anomaly.

**Per-persona feedback response**: WA should show the largest Phase 1→2 shift;
TD should show the smallest. If this ordering does not hold, investigate whether
High-C and High-A persona prompts are functioning as intended.

**Impasse rate**: Phase 2 impasse rate should exceed Phase 1 rate. AP pairings
should account for the majority of impasses in both phases.

**Figure generation**: All five figures should exist in outputs/figures/ after
analysis completes. If figures are missing, install matplotlib and re-run
analyze_results.py.

**Context window correlation**: analysis_additional.txt reports Pearson r between
transcript turn count and CG per phase. Seller correlations of r ≈ +0.15 to +0.21
(p ≈ 0.02–0.05) are expected and consistent with the companion paper. Substantially
larger correlations (r > 0.4) would indicate the lost-in-the-middle effect
(Liu et al., 2023) is materially confounding results.

---

## 6. References

All citations verified with live URLs. See companion paper Section 12.1 for full
citation audit and responses to any "hallucinated citation" objections.

Barry, B., & Friedman, R. A. (1998). Bargainer characteristics in distributive
  and integrative negotiation. Journal of Personality and Social Psychology,
  74(2), 345–359. https://doi.org/10.1037/0022-3514.74.2.345

Bjork, R. A., Dunlosky, J., & Kornell, N. (2013). Self-regulated learning.
  Annual Review of Psychology, 64, 417–444.
  https://doi.org/10.1146/annurev-psych-113011-143823

Cohen, M. C., Su, Z., Kao, H.-T., Nguyen, D., Lynch, S., Sap, M., & Volkova, S.
  (2025). Exploring Big Five personality and AI capability effects in
  LLM-simulated negotiation dialogues. KDD 2025 Workshop. arXiv:2506.15928.
  https://arxiv.org/abs/2506.15928  [VERIFIED LIVE]

Falcão, P. F., Saraiva, M., Santos, E., & Pina e Cunha, M. (2018). Big Five
  personality traits in simulated negotiation settings.
  EuroMed Journal of Business, 13(2), 201–213.
  https://doi.org/10.1108/EMJB-11-2017-0043

Fisher, R., & Ury, W. (1981). Getting to Yes. Houghton Mifflin.

Galinsky, A. D., & Mussweiler, T. (2001). First offers as anchors.
  Journal of Personality and Social Psychology, 81(4), 657–669.
  https://doi.org/10.1037/0022-3514.81.4.657

Hong, J., Byun, G., Kim, S., & Shu, K. (2025). Measuring sycophancy of language
  models in multi-turn dialogues. Findings of EMNLP 2025, 2239–2259.
  https://doi.org/10.18653/v1/2025.findings-emnlp.121  [VERIFIED LIVE]

Imas, A., Lee, K., & Misra, S. (2025). Agentic Interactions. SSRN 5875162.
  https://ssrn.com/abstract=5875162  [VERIFIED LIVE]

Keren, G. (1991). Calibration and probability judgements.
  Acta Psychologica, 77(3), 217–273.
  https://doi.org/10.1016/0001-6918(91)90036-Y

Kruger, J., & Dunning, D. (1999). Unskilled and unaware of it.
  Journal of Personality and Social Psychology, 77(6), 1121–1134.
  https://doi.org/10.1037/0022-3514.77.6.1121

Liu, N. F., et al. (2023). Lost in the middle. arXiv:2307.03172.
  https://arxiv.org/abs/2307.03172

Matz, S. C., & Gladstone, J. J. (2020). Nice guys finish last.
  Journal of Personality and Social Psychology, 118(6), 1279–1303.
  https://doi.org/10.1037/pspp0000279

McCrae, R. R., & Costa, P. T. (1987). Validation of the five-factor model.
  Journal of Personality and Social Psychology, 52(1), 81–90.
  https://doi.org/10.1037/0022-3514.52.1.81

Memory & Cognition. (2025). Quantifying uncert-AI-nty. Springer Nature.
  https://doi.org/10.3758/s13421-025-01704-3

Prasad, P. S., & Nguyen, M. N. (2025). When two LLMs debate, both think
  they will win. arXiv:2505.19184.
  https://arxiv.org/abs/2505.19184  [VERIFIED LIVE]

Rammstedt, B., & John, O. P. (2007). Measuring personality in one minute.
  Journal of Research in Personality, 41(1), 203–212.
  https://doi.org/10.1016/j.jrp.2006.02.001

Sharma, S., Bottom, W., & Elfenbein, H. A. (2013). On the role of personality,
  cognitive ability, and emotional intelligence in predicting negotiation outcomes.
  Organizational Psychology Review, 3(4), 293–336.
  https://doi.org/10.1177/2041386612462231

Steyvers, M., & Peters, M. A. K. (2025). Metacognition and uncertainty
  communication in humans and LLMs. Perspectives on Psychological Science,
  20(2), 312–327. https://doi.org/10.1177/17456916241268197

Anthropic. (2026). Project Deal: our Claude-run marketplace experiment.
  Published April 24, 2026.
  https://www.anthropic.com/features/project-deal  [VERIFIED LIVE]
