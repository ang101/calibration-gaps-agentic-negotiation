"""
analyze_results_research_grade.py
Research-grade analysis for persona calibration pilot study.
Aligned to outputs/negotiation_log.csv schema written by run_experiment_research_grade.py.
"""
import csv
import math
import os
import statistics
from collections import defaultdict

SCHEMA_VERSION = 3
FAIR_VALUE = 300
HIGH_A = {"WA", "TD"}
LOW_A = {"AP", "IC"}
HIGH_C = {"AP", "WA"}
LOW_C = {"IC", "TD"}
NO_ASSESSMENT_PAIRINGS = {("WA", "WA"), ("AP", "WA")}
INPUT_PATH = "outputs/negotiation_log.csv"
PRIMARY_PATH = "outputs/analysis_primary.txt"
EXPLORATORY_PATH = "outputs/analysis_exploratory.txt"
CONTROL_PATH = "outputs/analysis_control.txt"
QA_PATH = "outputs/analysis_qa.txt"
IMPASSE_PATH = "outputs/analysis_impasse.txt"


def atomic_write_text(path: str, text: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def load_results(path: str = INPUT_PATH) -> list[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found")
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            int_fields = ["schema_version", "round_index", "phase", "turns"]
            float_fields = [
                "final_price", "seller_actual", "buyer_actual", "seller_perceived", "buyer_perceived",
                "seller_cg", "buyer_cg", "opening_seller", "opening_buyer",
                "seller_fidelity_score", "buyer_fidelity_score", "seller_sycophancy"
            ]
            for fld in int_fields:
                try:
                    row[fld] = int(row[fld]) if row.get(fld) not in ("", "None", None) else None
                except Exception:
                    row[fld] = None
            for fld in float_fields:
                try:
                    row[fld] = float(row[fld]) if row.get(fld) not in ("", "None", None) else None
                except Exception:
                    row[fld] = None
            row["no_assessment_control"] = row.get("no_assessment_control", "False") == "True"
            row["turn_exhausted"] = row.get("turn_exhausted", "False") == "True"
            rows.append(row)
    return rows


def validate_input_schema(rows: list[dict]) -> None:
    if not rows:
        raise ValueError("No rows loaded from negotiation log")
    required = {
        "schema_version", "seller_persona", "buyer_persona", "phase", "round_index", "outcome",
        "seller_cg", "buyer_cg", "turns", "final_price", "seller_fidelity_score",
        "buyer_fidelity_score", "no_assessment_control"
    }
    missing = required - set(rows[0].keys())
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    bad_schema = sum(1 for r in rows if r.get("schema_version") != SCHEMA_VERSION)
    if bad_schema:
        raise ValueError(f"Found {bad_schema} rows with schema_version != {SCHEMA_VERSION}")


def logical_round_key(row: dict) -> tuple:
    return (row.get("seller_persona"), row.get("buyer_persona"), row.get("phase"), row.get("round_index"))


def cohens_d(group1: list[float], group2: list[float]) -> float:
    if len(group1) < 2 or len(group2) < 2:
        return float("nan")
    n1, n2 = len(group1), len(group2)
    m1, m2 = statistics.mean(group1), statistics.mean(group2)
    s1, s2 = statistics.stdev(group1), statistics.stdev(group2)
    pooled_s = math.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
    return float("nan") if pooled_s == 0 else (m1 - m2) / pooled_s


def mann_whitney_u(x: list[float], y: list[float]) -> tuple[float, float]:
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return float("nan"), float("nan")
    u = sum(1.0 if xi > yj else 0.5 if xi == yj else 0.0 for xi in x for yj in y)
    mean_u = nx * ny / 2
    std_u = math.sqrt(nx * ny * (nx + ny + 1) / 12)
    if std_u == 0:
        return u, float("nan")
    z = (u - mean_u) / std_u
    def phi(zv: float) -> float:
        t = 1 / (1 + 0.2316419 * abs(zv))
        poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
        return 1 - (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * zv**2) * poly
    p = 2 * (1 - phi(abs(z)))
    return u, min(p, 1.0)


def wilcoxon_signed_rank(x: list[float], y: list[float]) -> tuple[float, float]:
    """Wilcoxon signed-rank test for paired samples x vs y. Returns (W, p)."""
    diffs = [xi - yi for xi, yi in zip(x, y) if xi != yi]
    if len(diffs) < 4:
        return float("nan"), float("nan")
    abs_diffs = sorted(enumerate(diffs), key=lambda t: abs(t[1]))
    ranks, rank = {}, 1
    i = 0
    while i < len(abs_diffs):
        j = i
        while j < len(abs_diffs) and abs(abs_diffs[j][1]) == abs(abs_diffs[i][1]):
            j += 1
        avg_rank = (rank + rank + (j - i) - 1) / 2
        for k in range(i, j):
            ranks[abs_diffs[k][0]] = avg_rank
        rank += (j - i)
        i = j
    w_plus  = sum(ranks[i] for i, d in enumerate(diffs) if d > 0)
    w_minus = sum(ranks[i] for i, d in enumerate(diffs) if d < 0)
    w = min(w_plus, w_minus)
    n = len(diffs)
    mean_w = n * (n + 1) / 4
    std_w  = math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    if std_w == 0:
        return w, float("nan")
    z = (w - mean_w) / std_w
    def phi(zv: float) -> float:
        t = 1 / (1 + 0.2316419 * abs(zv))
        poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
        return 1 - (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * zv**2) * poly
    p = 2 * (1 - phi(abs(z)))
    return w, min(p, 1.0)


def sig_label(p: float) -> str:
    """Return significance stars for a p-value."""
    if math.isnan(p):   return "n.s."
    if p < 0.001:       return "***"
    if p < 0.01:        return "**"
    if p < 0.05:        return "*"
    return "n.s."


def pearson_r(x: list[float], y: list[float]) -> float:
    n = len(x)
    if n < 3:
        return float("nan")
    mx, my = sum(x) / n, sum(y) / n
    num  = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    denx = sum((xi - mx) ** 2 for xi in x) ** 0.5
    deny = sum((yi - my) ** 2 for yi in y) ** 0.5
    return float("nan") if denx == 0 or deny == 0 else num / (denx * deny)


def pearson_r_pvalue(r: float, n: int) -> float:
    """Two-tailed p-value for Pearson r using t-distribution approximation."""
    if math.isnan(r) or n < 3:
        return float("nan")
    if abs(r) >= 1.0:
        return 0.0
    t = r * math.sqrt((n - 2) / (1 - r ** 2))
    # t-distribution survival using normal approximation (adequate for n>=20)
    def phi(zv: float) -> float:
        t2 = 1 / (1 + 0.2316419 * abs(zv))
        poly = t2 * (0.319381530 + t2 * (-0.356563782 + t2 * (1.781477937 + t2 * (-1.821255978 + t2 * 1.330274429))))
        return 1 - (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * zv ** 2) * poly
    p = 2 * (1 - phi(abs(t)))
    return min(p, 1.0)


def kruskal_wallis(groups: list[list[float]]) -> tuple[float, float]:
    """Kruskal-Wallis H test. Returns (H, p)."""
    groups = [g for g in groups if len(g) >= 2]
    if len(groups) < 2:
        return float("nan"), float("nan")
    all_vals = []
    for i, g in enumerate(groups):
        for v in g:
            all_vals.append((v, i))
    all_vals.sort(key=lambda t: t[0])
    n = len(all_vals)
    ranks = {}
    i = 0
    while i < n:
        j = i
        while j < n and all_vals[j][0] == all_vals[i][0]:
            j += 1
        avg_rank = (i + 1 + j) / 2
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j
    group_rank_sums = [0.0] * len(groups)
    group_ns = [0] * len(groups)
    for idx, (_, gi) in enumerate(all_vals):
        group_rank_sums[gi] += ranks[idx]
        group_ns[gi] += 1
    h = (12 / (n * (n + 1))) * sum(rs ** 2 / ni for rs, ni in zip(group_rank_sums, group_ns)) - 3 * (n + 1)
    # chi-squared approximation with k-1 df
    k = len(groups)
    df = k - 1
    # chi2 survival via Wilson-Hilferty approximation
    def chi2_sf(x: float, df: int) -> float:
        if x <= 0:
            return 1.0
        z = ((x / df) ** (1/3) - (1 - 2 / (9 * df))) / math.sqrt(2 / (9 * df))
        def phi(zv):
            t = 1 / (1 + 0.2316419 * abs(zv))
            poly = t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
            return 1 - (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * zv ** 2) * poly
        return 1 - phi(z) if z >= 0 else phi(-z)
    p = chi2_sf(h, df)
    return h, min(p, 1.0)


def fisher_exact_2x2(a: int, b: int, c: int, d: int) -> float:
    """Two-tailed Fisher's exact test for 2x2 table [[a,b],[c,d]]. Returns p."""
    def log_factorial(n: int) -> float:
        return sum(math.log(i) for i in range(1, n + 1))
    def log_hypergeom(k, n1, n2, n):
        return (log_factorial(n1) + log_factorial(n2) +
                log_factorial(n - n1) + log_factorial(n - n2) -
                log_factorial(n) - log_factorial(k) -
                log_factorial(n1 - k) - log_factorial(n2 - k) -
                log_factorial(n - n1 - n2 + k))
    n1 = a + b  # row 1 total
    n2 = c + d  # row 2 total
    n  = a + b + c + d
    k_min = max(0, n1 + n2 - n)  # actually max(0, n1-(n-n2))
    k_max = min(n1, n2)           # actually min(n1, a+c)
    # re-derive correctly
    col1 = a + c
    k_min = max(0, n1 + col1 - n)
    k_max = min(n1, col1)
    if k_min > k_max:
        return float("nan")
    log_p_observed = log_hypergeom(a, n1, col1, n)
    p_total = 0.0
    for k in range(k_min, k_max + 1):
        lp = log_hypergeom(k, n1, col1, n)
        if lp <= log_p_observed + 1e-10:
            p_total += math.exp(lp)
    return min(p_total, 1.0)


def mean_or_nan(values: list[float]) -> float:
    return statistics.mean(values) if values else float("nan")

def mean_ci_95(values: list[float]) -> tuple[float, float, float]:
    if not values:
        return float("nan"), float("nan"), float("nan")
    n = len(values)
    m = statistics.mean(values)
    if n < 2:
        return m, float("nan"), float("nan")
    se = statistics.stdev(values) / math.sqrt(n)
    t_crit = 2.262 if n <= 10 else 2.093 if n <= 20 else 1.960
    return m, m - t_crit * se, m + t_crit * se


def qa_checks(rows: list[dict]) -> dict:
    duplicates = len(rows) - len({logical_round_key(r) for r in rows})
    bad_prices = [r["final_price"] for r in rows if r.get("outcome") == "deal" and r.get("final_price") is not None and not (200 <= r["final_price"] <= 380)]
    null_phase1_noncontrol = sum(1 for r in rows if r["phase"] == 1 and not r["no_assessment_control"] and r["seller_cg"] is None)
    return {
        "n_rows": len(rows),
        "duplicates": duplicates,
        "bad_price_count": len(bad_prices),
        "bad_prices_sample": bad_prices[:5],
        "null_phase1_noncontrol_seller_cg": null_phase1_noncontrol,
    }


def analyze(results: list[dict]) -> dict:
    out = {}

    def phase(p): return [r for r in results if r["phase"] == p]
    def p1(): return phase(1)
    def p2(): return phase(2)
    def assessed(rows): return [r for r in rows if not r["no_assessment_control"]]

    p1_assessed = assessed(p1())

        # === BEHAVIORAL METRICS ===
    # Opening-anchor distance and concession rate per deal (seller-side)
    beh = {}

    # Only use rounds with valid opening and final prices
    def valid_deals(rows):
        return [
            r for r in rows
            if r.get("outcome") == "deal"
            and r.get("final_price") is not None
            and r.get("opening_seller") is not None
            and r.get("turns") is not None
            and r["turns"] > 0
        ]

    deals_p1 = valid_deals(p1())
    deals_p2 = valid_deals(p2())

    for persona in ["AP", "WA", "IC", "TD"]:
        p1_rows = [r for r in deals_p1 if r["seller_persona"] == persona]
        p2_rows = [r for r in deals_p2 if r["seller_persona"] == persona]

        def summarize(rows):
            opening_anchor = [r["opening_seller"] - FAIR_VALUE for r in rows]
            concession_per_turn = [
                (r["opening_seller"] - r["final_price"]) / r["turns"] for r in rows
            ]
            return {
                "n_deals": len(rows),
                "mean_opening_anchor": mean_or_nan(opening_anchor),
                "mean_concession_per_turn": mean_or_nan(concession_per_turn),
            }

        beh[persona] = {
            "phase1": summarize(p1_rows),
            "phase2": summarize(p2_rows),
        }

    # Outcome-type distribution (deal / impasse / timeout) by seller persona, Phase 1
    outcome_dist = {}
    for persona in ["AP", "WA", "IC", "TD"]:
        rows = [r for r in p1() if r["seller_persona"] == persona]
        n = len(rows)
        deals = sum(1 for r in rows if r["outcome"] == "deal")
        impasses = sum(1 for r in rows if r["outcome"] == "impasse")
        timeouts = sum(1 for r in rows if r.get("turn_exhausted"))
        outcome_dist[persona] = {
            "n_rounds": n,
            "deal_rate": deals / n if n else float("nan"),
            "impasse_rate": impasses / n if n else float("nan"),
            "timeout_rate": timeouts / n if n else float("nan"),
        }

    out["behavioral"] = {
        "seller_opening_and_concession": beh,
        "phase1_outcome_distribution": outcome_dist,
    }

    high_a_cg = [r["seller_cg"] for r in p1_assessed if r["seller_persona"] in HIGH_A and r["seller_cg"] is not None]
    low_a_cg = [r["seller_cg"] for r in p1_assessed if r["seller_persona"] in LOW_A and r["seller_cg"] is not None]
    h1_high_m, h1_high_lo, h1_high_hi = mean_ci_95(high_a_cg)
    h1_low_m, h1_low_lo, h1_low_hi = mean_ci_95(low_a_cg)
    h1_d = cohens_d(high_a_cg, low_a_cg)
    h1_u, h1_p = mann_whitney_u(high_a_cg, low_a_cg)
    out["H1"] = {
        "high_A_mean_CG": h1_high_m,
        "high_A_CI": (h1_high_lo, h1_high_hi),
        "n_high": len(high_a_cg),
        "low_A_mean_CG": h1_low_m,
        "low_A_CI": (h1_low_lo, h1_low_hi),
        "n_low": len(low_a_cg),
        "cohens_d": h1_d,
        "mann_whitney_U": h1_u,
        "p_value": h1_p,
        "supported": (h1_high_m > h1_low_m) if not math.isnan(h1_high_m) else None,
    }

        # === ROBUSTNESS: SIMPLE IMPASSE=0 SCHEME FOR H1 (SELLER) ===
    # Recompute Phase 1 seller CG under alternative actual scoring where impasse=0.
    alt_high = []
    alt_low = []
    for r in p1_assessed:
        if r["seller_cg"] is None:
            continue
        if r["outcome"] == "impasse":
            # Under alternative scheme, actual score is 0, so CG_alt = perceived - 0
            if r.get("seller_perceived") is not None:
                cg_alt = r["seller_perceived"]  # perceived minus 0
            else:
                continue
        else:
            # For deal rounds, use existing actual score
            if r.get("seller_perceived") is not None and r.get("seller_actual") is not None:
                cg_alt = r["seller_perceived"] - r["seller_actual"]
            else:
                continue

        if r["seller_persona"] in HIGH_A:
            alt_high.append(cg_alt)
        elif r["seller_persona"] in LOW_A:
            alt_low.append(cg_alt)

    alt_high_m = mean_or_nan(alt_high)
    alt_low_m = mean_or_nan(alt_low)
    out["H1_impasse0_robustness"] = {
        "high_A_mean_CG_alt": alt_high_m,
        "low_A_mean_CG_alt": alt_low_m,
        "n_high_alt": len(alt_high),
        "n_low_alt": len(alt_low),
        "ordering_preserved": (alt_high_m > alt_low_m) if not math.isnan(alt_high_m) else None,
    }

    p1_cg = [r["seller_cg"] for r in p1_assessed if r["seller_cg"] is not None]
    p2_cg = [r["seller_cg"] for r in p2() if r["seller_cg"] is not None]
    p1_abs = [abs(v) for v in p1_cg]
    p2_abs = [abs(v) for v in p2_cg]
    h2_p1_m, _, _ = mean_ci_95(p1_abs)
    h2_p2_m, _, _ = mean_ci_95(p2_abs)

    # Wilcoxon signed-rank: match each persona's Phase1 CG to Phase2 CG
    # Use per-persona mean to create paired observations (one per persona)
    persona_p1 = {p: [r["seller_cg"] for r in p1_assessed if r["seller_persona"] == p and r["seller_cg"] is not None] for p in ["AP","WA","IC","TD"]}
    persona_p2 = {p: [r["seller_cg"] for r in p2()         if r["seller_persona"] == p and r["seller_cg"] is not None] for p in ["AP","WA","IC","TD"]}
    # Paired at the round level: match Phase1 and Phase2 rounds for same persona
    # Use all individual CG values paired by persona membership (unpaired Wilcoxon on abs CG)
    h2_w, h2_p = wilcoxon_signed_rank(
        sorted([r["seller_cg"] for r in p1_assessed if r["seller_cg"] is not None]),
        sorted([r["seller_cg"] for r in p2()         if r["seller_cg"] is not None])[:len(p1_abs)]
    )
    # Also run Mann-Whitney on Phase1 vs Phase2 abs CG (unpaired, more conservative)
    h2_u, h2_p_mw = mann_whitney_u(p1_abs, p2_abs)
    out["H2"] = {
        "phase1_mean_abs_CG": h2_p1_m,
        "n_phase1": len(p1_abs),
        "phase2_mean_abs_CG": h2_p2_m,
        "n_phase2": len(p2_abs),
        "escalation_observed": (h2_p2_m > h2_p1_m) if not math.isnan(h2_p1_m) else None,
        "shift": h2_p2_m - h2_p1_m if not math.isnan(h2_p1_m) else float("nan"),
        "mann_whitney_U": h2_u,
        "p_value_mw": h2_p_mw,
        "sig_mw": sig_label(h2_p_mw),
    }

    h3 = {}
    highc_shifts, lowc_shifts = [], []
    for p_group, label in [(HIGH_C, "High-C"), (LOW_C, "Low-C")]:
        cg1 = [r["seller_cg"] for r in p1_assessed if r["seller_persona"] in p_group and r["seller_cg"] is not None]
        cg2 = [r["seller_cg"] for r in p2()         if r["seller_persona"] in p_group and r["seller_cg"] is not None]
        m1  = statistics.mean(cg1) if cg1 else float("nan")
        m2  = statistics.mean(cg2) if cg2 else float("nan")
        # Per-persona shifts within this C group
        for persona in (HIGH_C if label == "High-C" else LOW_C):
            pp1 = [r["seller_cg"] for r in p1_assessed if r["seller_persona"] == persona and r["seller_cg"] is not None]
            pp2 = [r["seller_cg"] for r in p2()         if r["seller_persona"] == persona and r["seller_cg"] is not None]
            if pp1 and pp2:
                shift_val = statistics.mean(pp2) - statistics.mean(pp1)
                if label == "High-C":
                    highc_shifts.append(shift_val)
                else:
                    lowc_shifts.append(shift_val)
        h3[label] = {
            "phase1_mean": m1, "phase2_mean": m2,
            "shift": m2 - m1 if not math.isnan(m1) else float("nan"),
            "n1": len(cg1), "n2": len(cg2),
        }
    # Mann-Whitney on individual CG values: High-C Phase2 vs Low-C Phase2
    hc_p2 = [r["seller_cg"] for r in p2() if r["seller_persona"] in HIGH_C and r["seller_cg"] is not None]
    lc_p2 = [r["seller_cg"] for r in p2() if r["seller_persona"] in LOW_C  and r["seller_cg"] is not None]
    h3_u, h3_p = mann_whitney_u(hc_p2, lc_p2)
    # Also Mann-Whitney on Phase1→2 shift per round (persona-level)
    hc_p1 = [r["seller_cg"] for r in p1_assessed if r["seller_persona"] in HIGH_C and r["seller_cg"] is not None]
    lc_p1 = [r["seller_cg"] for r in p1_assessed if r["seller_persona"] in LOW_C  and r["seller_cg"] is not None]
    h3_shift_u, h3_shift_p = mann_whitney_u(hc_p1, lc_p1)
    h3["mann_whitney_p2_U"]       = h3_u
    h3["mann_whitney_p2_p"]       = h3_p
    h3["mann_whitney_p2_sig"]     = sig_label(h3_p)
    h3["mann_whitney_p1_U"]       = h3_shift_u
    h3["mann_whitney_p1_p"]       = h3_shift_p
    h3["mann_whitney_p1_sig"]     = sig_label(h3_shift_p)
    out["H3"] = h3

    cross_pairings = [("AP", "WA"), ("WA", "IC"), ("IC", "TD"), ("TD", "AP")]
    within_pairings = [("AP", "AP"), ("WA", "WA"), ("IC", "IC"), ("TD", "TD")]
    def mean_deviation(rows, pairings):
        deals = [r for r in rows if r["outcome"] == "deal" and r["final_price"] is not None and (r["seller_persona"], r["buyer_persona"]) in set(pairings)]
        devs = [abs(r["final_price"] - FAIR_VALUE) for r in deals]
        return statistics.mean(devs) if devs else float("nan"), len(devs)
    cross_dev, n_cross = mean_deviation(p1(), cross_pairings)
    within_dev, n_within = mean_deviation(p1(), within_pairings)
    out["H5"] = {
        "cross_persona_mean_deviation": cross_dev,
        "n_cross": n_cross,
        "within_persona_mean_deviation": within_dev,
        "n_within": n_within,
        "asymmetry_larger": (cross_dev > within_dev) if not math.isnan(cross_dev) else None,
    }

    fidelity = {}
    for persona in ["AP", "WA", "IC", "TD"]:
        seller_fid = [r["seller_fidelity_score"] for r in results if r["seller_persona"] == persona and r["seller_fidelity_score"] is not None]
        buyer_fid = [r["buyer_fidelity_score"] for r in results if r["buyer_persona"] == persona and r["buyer_fidelity_score"] is not None]
        fidelity[persona] = {
            "mean_seller": statistics.mean(seller_fid) if seller_fid else float("nan"),
            "mean_buyer": statistics.mean(buyer_fid) if buyer_fid else float("nan"),
            "flag_seller": (statistics.mean(seller_fid) < 0.33) if seller_fid else True,
            "flag_buyer": (statistics.mean(buyer_fid) < 0.33) if buyer_fid else True,
        }
    out["fidelity"] = fidelity

    deal_rates = defaultdict(lambda: {"deals": 0, "total": 0, "prices": []})
    for r in p1():
        key = (r["seller_persona"], r["buyer_persona"])
        deal_rates[key]["total"] += 1
        if r["outcome"] == "deal" and r["final_price"] is not None:
            deal_rates[key]["deals"] += 1
            deal_rates[key]["prices"].append(r["final_price"])
    out["deal_rates"] = {
        k: {
            "rate": v["deals"] / v["total"] if v["total"] else 0,
            "mean_price": statistics.mean(v["prices"]) if v["prices"] else None,
            "deviation": statistics.mean(abs(p - FAIR_VALUE) for p in v["prices"]) if v["prices"] else None,
        }
        for k, v in deal_rates.items()
    }

    corr = {}
    for ph in [1, 2]:
        seller_rows = [r for r in phase(ph) if r["seller_cg"] is not None and r["turns"] is not None]
        buyer_rows = [r for r in phase(ph) if r["buyer_cg"] is not None and r["turns"] is not None]
        corr[f"phase{ph}"] = {
            "r_seller": pearson_r([r["turns"] for r in seller_rows], [r["seller_cg"] for r in seller_rows]),
            "r_buyer": pearson_r([r["turns"] for r in buyer_rows], [r["buyer_cg"] for r in buyer_rows]),
            "n_seller": len(seller_rows),
            "n_buyer": len(buyer_rows),
        }
    out["transcript_correlation"] = corr
    # === CALIBRATION METRICS ===
    calib = {"phase1": {}, "phase2": {}}
    for ph, rows in [("phase1", p1()), ("phase2", p2())]:
        # Seller absolute CG and overconfidence rate by persona
        for persona in ["AP", "WA", "IC", "TD"]:
            prs = [
                r for r in rows
                if r["seller_persona"] == persona and r["seller_cg"] is not None
            ]
            cgs = [r["seller_cg"] for r in prs]
            abs_cg = [abs(v) for v in cgs]
            over = [1 for v in cgs if v > 0]
            calib[ph][persona] = {
                "n": len(cgs),
                "mean_CG": mean_or_nan(cgs),
                "mean_abs_CG": mean_or_nan(abs_cg),
                "overconfidence_rate": (sum(over) / len(cgs)) if cgs else float("nan"),
            }

        # Rank-order correlation between perceived and actual seller scores (all personas)
        prs_all = [
            r for r in rows
            if r.get("seller_actual") is not None
            and r.get("seller_perceived") is not None
        ]
        if len(prs_all) >= 3:
            actual = [r["seller_actual"] for r in prs_all]
            perceived = [r["seller_perceived"] for r in prs_all]
            calib[ph]["_global_rank_corr"] = {
                "pearson_r": pearson_r(actual, perceived),
                "n": len(actual),
            }
        else:
            calib[ph]["_global_rank_corr"] = {"pearson_r": float("nan"), "n": len(prs_all)}

    out["calibration_metrics"] = calib
    timeout_rates = {}
    for persona in ["AP", "WA", "IC", "TD"]:
        p1_rounds = [r for r in p1_assessed if r["seller_persona"] == persona]
        n_total = len(p1_rounds)
        n_timeout = sum(1 for r in p1_rounds if r.get("turn_exhausted") is True)
        n_impasse = sum(1 for r in p1_rounds if r["outcome"] == "impasse" and not r.get("turn_exhausted"))
        timeout_rates[persona] = {
            "timeout_rate": n_timeout / n_total if n_total else 0,
            "explicit_impasse_rate": n_impasse / n_total if n_total else 0,
            "n": n_total,
        }
    out["timeout_rates"] = timeout_rates

    std_p2_cgs = [r["seller_cg"] for r in p2() if (r["seller_persona"], r["buyer_persona"]) not in NO_ASSESSMENT_PAIRINGS and r["seller_cg"] is not None]
    ctrl_p2_cgs = [r["seller_cg"] for r in p2() if (r["seller_persona"], r["buyer_persona"]) in NO_ASSESSMENT_PAIRINGS and r["seller_cg"] is not None]
    out["reactivity_control"] = {
        "standard_mean_p2_cg": statistics.mean(std_p2_cgs) if std_p2_cgs else float("nan"),
        "control_mean_p2_cg": statistics.mean(ctrl_p2_cgs) if ctrl_p2_cgs else float("nan"),
        "n_standard": len(std_p2_cgs),
        "n_control": len(ctrl_p2_cgs),
    }

    # === ADDITIONAL STATISTICAL ANALYSES ===

    # 1. Pearson r p-values for transcript length correlations
    corr_with_p = {}
    for ph in [1, 2]:
        seller_rows = [r for r in phase(ph) if r["seller_cg"] is not None and r["turns"] is not None]
        buyer_rows  = [r for r in phase(ph) if r["buyer_cg"]  is not None and r["turns"] is not None]
        rs = pearson_r([r["turns"] for r in seller_rows], [r["seller_cg"] for r in seller_rows])
        rb = pearson_r([r["turns"] for r in buyer_rows],  [r["buyer_cg"]  for r in buyer_rows])
        ns, nb = len(seller_rows), len(buyer_rows)
        corr_with_p[f"phase{ph}"] = {
            "r_seller": rs, "p_seller": pearson_r_pvalue(rs, ns),
            "sig_seller": sig_label(pearson_r_pvalue(rs, ns)), "n_seller": ns,
            "r_buyer":  rb, "p_buyer":  pearson_r_pvalue(rb, nb),
            "sig_buyer":  sig_label(pearson_r_pvalue(rb, nb)),  "n_buyer":  nb,
        }
    out["transcript_correlation_with_p"] = corr_with_p

    # 2. Cohen's d for H2 (Phase1 vs Phase2 abs CG) and H3 (High-C vs Low-C Phase2)
    h2_d = cohens_d(p1_abs, p2_abs)
    out["H2"]["cohens_d"] = h2_d

    hc_p2_cg = [r["seller_cg"] for r in p2() if r["seller_persona"] in HIGH_C and r["seller_cg"] is not None]
    lc_p2_cg = [r["seller_cg"] for r in p2() if r["seller_persona"] in LOW_C  and r["seller_cg"] is not None]
    h3_d = cohens_d(hc_p2_cg, lc_p2_cg)
    out["H3"]["cohens_d_p2"] = h3_d

    # 3. Per-persona Mann-Whitney: Phase 1 vs Phase 2 seller CG (unpaired, independent samples)
    per_persona_phase_test = {}
    for persona in ["AP", "WA", "IC", "TD"]:
        cg1 = [r["seller_cg"] for r in p1_assessed if r["seller_persona"] == persona and r["seller_cg"] is not None]
        cg2 = [r["seller_cg"] for r in p2()         if r["seller_persona"] == persona and r["seller_cg"] is not None]
        u, p_val = mann_whitney_u(cg1, cg2)
        d = cohens_d(cg1, cg2)
        per_persona_phase_test[persona] = {
            "n_phase1": len(cg1), "mean_phase1": mean_or_nan(cg1),
            "n_phase2": len(cg2), "mean_phase2": mean_or_nan(cg2),
            "shift": mean_or_nan(cg2) - mean_or_nan(cg1),
            "mann_whitney_U": u, "p_value": p_val,
            "sig": sig_label(p_val), "cohens_d": d,
            "note": "unpaired Mann-Whitney; rounds are independent draws per phase",
        }
    out["per_persona_phase_test"] = per_persona_phase_test

    # 4. Kruskal-Wallis on deal price deviation across all pairings (Phase 1)
    all_pairings = [("AP","AP"),("WA","WA"),("IC","IC"),("TD","TD"),
                    ("AP","WA"),("WA","IC"),("IC","TD"),("TD","AP")]
    pairing_devs = []
    for s, b in all_pairings:
        devs = [abs(r["final_price"] - FAIR_VALUE)
                for r in p1()
                if r["outcome"] == "deal" and r["final_price"] is not None
                and r["seller_persona"] == s and r["buyer_persona"] == b]
        pairing_devs.append(devs)
    kw_h, kw_p = kruskal_wallis(pairing_devs)
    out["kruskal_wallis_deviation"] = {
        "H": kw_h, "p_value": kw_p, "sig": sig_label(kw_p),
        "df": len([g for g in pairing_devs if len(g) >= 2]) - 1,
        "note": "Kruskal-Wallis on deal price deviation across pairings. Pairwise follow-up underpowered at n=20/pairing.",
    }

    # 5. Fidelity score Mann-Whitney across personas (seller and buyer separately)
    fidelity_test = {}
    personas_pairs = [("AP","IC"), ("AP","WA"), ("AP","TD"), ("WA","IC"), ("WA","TD"), ("IC","TD")]
    for p_a, p_b in personas_pairs:
        sf_a = [r["seller_fidelity_score"] for r in results if r["seller_persona"] == p_a and r["seller_fidelity_score"] is not None]
        sf_b = [r["seller_fidelity_score"] for r in results if r["seller_persona"] == p_b and r["seller_fidelity_score"] is not None]
        u, pv = mann_whitney_u(sf_a, sf_b)
        fidelity_test[f"{p_a}_vs_{p_b}_seller"] = {
            "mean_a": mean_or_nan(sf_a), "mean_b": mean_or_nan(sf_b),
            "U": u, "p": pv, "sig": sig_label(pv),
        }
    out["fidelity_tests"] = fidelity_test

    # 6. Buyer CG descriptive (no inferential tests — role asymmetry confound)
    buyer_cg_descriptive = {}
    for persona in ["AP", "WA", "IC", "TD"]:
        b1 = [r["buyer_cg"] for r in p1() if r["buyer_persona"] == persona and r["buyer_cg"] is not None]
        b2 = [r["buyer_cg"] for r in p2() if r["buyer_persona"] == persona and r["buyer_cg"] is not None]
        buyer_cg_descriptive[persona] = {
            "phase1_mean": mean_or_nan(b1), "phase1_n": len(b1),
            "phase2_mean": mean_or_nan(b2), "phase2_n": len(b2),
            "note": "Descriptive only. Cross-role CG comparisons not valid due to role asymmetry in actual score computation.",
        }
    out["buyer_cg_descriptive"] = buyer_cg_descriptive

    # 7. Fisher's exact test: Phase 1 vs Phase 2 impasse rate
    p1_impasse = sum(1 for r in p1() if r["outcome"] == "impasse")
    p1_deal_or_other = len(p1()) - p1_impasse
    p2_impasse = sum(1 for r in p2() if r["outcome"] == "impasse")
    p2_deal_or_other = len(p2()) - p2_impasse
    fisher_p = fisher_exact_2x2(p1_impasse, p1_deal_or_other, p2_impasse, p2_deal_or_other)
    out["fisher_impasse_phase"] = {
        "phase1_impasse": p1_impasse, "phase1_total": len(p1()),
        "phase2_impasse": p2_impasse, "phase2_total": len(p2()),
        "phase1_rate": p1_impasse / len(p1()) if p1() else float("nan"),
        "phase2_rate": p2_impasse / len(p2()) if p2() else float("nan"),
        "fisher_p": fisher_p, "sig": sig_label(fisher_p),
        "note": "Preliminary — small cell counts (phase1 n=3). Interpret with caution.",
    }

    out["qa"] = qa_checks(results)

    # === IMPASSE ANALYSIS ===
    # Per-round detail for all impasse rounds (both phases)
    impasse_rounds = [
        r for r in results
        if r.get("outcome") == "impasse"
    ]
    impasse_detail = []
    for r in impasse_rounds:
        impasse_detail.append({
            "phase": r["phase"],
            "seller_persona": r["seller_persona"],
            "buyer_persona": r["buyer_persona"],
            "round_index": r["round_index"],
            "turns": r["turns"],
            "seller_cg": r.get("seller_cg"),
            "buyer_cg": r.get("buyer_cg"),
            "seller_perceived": r.get("seller_perceived"),
            "buyer_perceived": r.get("buyer_perceived"),
            "seller_actual": r.get("seller_actual"),
            "buyer_actual": r.get("buyer_actual"),
        })

    # Compare mean seller CG in impasse vs deal rounds per persona (Phase 1 assessed only)
    impasse_vs_deal = {}
    for persona in ["AP", "WA", "IC", "TD"]:
        persona_rows = [r for r in p1_assessed if r["seller_persona"] == persona]
        deal_cgs = [r["seller_cg"] for r in persona_rows if r["outcome"] == "deal" and r["seller_cg"] is not None]
        impasse_cgs = [r["seller_cg"] for r in persona_rows if r["outcome"] == "impasse" and r["seller_cg"] is not None]
        impasse_vs_deal[persona] = {
            "n_deal": len(deal_cgs),
            "mean_cg_deal": mean_or_nan(deal_cgs),
            "n_impasse": len(impasse_cgs),
            "mean_cg_impasse": mean_or_nan(impasse_cgs),
        }

    out["impasse_analysis"] = {
        "n_total_impasse": len(impasse_rounds),
        "per_round_detail": impasse_detail,
        "impasse_vs_deal_cg": impasse_vs_deal,
    }

    return out


def write_outputs(out: dict) -> None:
    h1 = out["H1"]
    h2 = out["H2"]
    primary = []
    primary.append("PRIMARY ENDPOINTS")
    primary.append("=" * 60)
    primary.append("Note: Treat as directional pilot signals, not definitive tests.")
    primary.append("")
    primary.append(f"H1 High-A mean CG = {h1['high_A_mean_CG']:+.2f}, Low-A mean CG = {h1['low_A_mean_CG']:+.2f}, d = {h1['cohens_d']:+.3f}, U = {h1['mann_whitney_U']:.1f}, p = {h1['p_value']:.4f}  {sig_label(h1['p_value'])}")
    primary.append(f"H2 Phase1 mean |CG| = {h2['phase1_mean_abs_CG']:.2f}, Phase2 mean |CG| = {h2['phase2_mean_abs_CG']:.2f}, shift = {h2['shift']:+.2f},  U = {h2['mann_whitney_U']:.1f}, p = {h2['p_value_mw']:.4f}  {h2['sig_mw']}")
    h3  = out["H3"]
    primary.append(f"H3 High-C Phase2 mean CG = {h3['High-C']['phase2_mean']:+.2f} (shift {h3['High-C']['shift']:+.2f}), Low-C Phase2 mean CG = {h3['Low-C']['phase2_mean']:+.2f} (shift {h3['Low-C']['shift']:+.2f}),  U = {h3['mann_whitney_p2_U']:.1f}, p = {h3['mann_whitney_p2_p']:.4f}  {h3['mann_whitney_p2_sig']}")
    atomic_write_text(PRIMARY_PATH, "\n".join(primary) + "\n")

    expl = []
    expl.append("EXPLORATORY ANALYSES")
    expl.append("=" * 60)
    expl.append(str(out))
    atomic_write_text(EXPLORATORY_PATH, "\n".join(expl) + "\n")

    ctrl = out["reactivity_control"]
    diff = ctrl["standard_mean_p2_cg"] - ctrl["control_mean_p2_cg"]
    control = []
    control.append("SELF-ASSESSMENT REACTIVITY CONTROL")
    control.append("=" * 60)
    control.append(f"Standard mean P2 CG: {ctrl['standard_mean_p2_cg']:+.2f} n={ctrl['n_standard']}")
    control.append(f"Control mean P2 CG: {ctrl['control_mean_p2_cg']:+.2f} n={ctrl['n_control']}")
    control.append(f"Difference: {diff:+.2f}")
    atomic_write_text(CONTROL_PATH, "\n".join(control) + "\n")

    qa = out["qa"]
    qa_lines = []
    qa_lines.append("ANALYSIS QA")
    qa_lines.append("=" * 60)
    qa_lines.append(f"Rows loaded: {qa['n_rows']}")
    qa_lines.append(f"Duplicate logical rounds: {qa['duplicates']}")
    qa_lines.append(f"Bad deal-price count: {qa['bad_price_count']}")
    qa_lines.append(f"Bad deal-price sample: {qa['bad_prices_sample']}")
    qa_lines.append(f"Null Phase-1 non-control seller CG rows: {qa['null_phase1_noncontrol_seller_cg']}")
    atomic_write_text(QA_PATH, "\n".join(qa_lines) + "\n")

    imp = out["impasse_analysis"]
    imp_lines = []
    imp_lines.append("IMPASSE ANALYSIS")
    imp_lines.append("=" * 60)
    imp_lines.append(f"Total impasse rounds: {imp['n_total_impasse']}")
    imp_lines.append("")
    imp_lines.append("Per-round detail:")
    imp_lines.append(f"  {'Phase':<6} {'Seller':<6} {'Buyer':<6} {'Rnd':<4} {'Turns':<6} {'Seller CG':<12} {'Buyer CG':<12} {'Seller Perceived':<18} {'Seller Actual'}")
    for r in imp["per_round_detail"]:
        scg = f"{r['seller_cg']:+.1f}" if r['seller_cg'] is not None else "N/A"
        bcg = f"{r['buyer_cg']:+.1f}" if r['buyer_cg'] is not None else "N/A"
        sp = f"{r['seller_perceived']:.0f}" if r['seller_perceived'] is not None else "N/A"
        sa = f"{r['seller_actual']:.1f}" if r['seller_actual'] is not None else "N/A"
        imp_lines.append(f"  {r['phase']:<6} {r['seller_persona']:<6} {r['buyer_persona']:<6} {r['round_index']:<4} {r['turns']:<6} {scg:<12} {bcg:<12} {sp:<18} {sa}")
    imp_lines.append("")
    imp_lines.append("Mean seller CG: impasse vs deal rounds (Phase 1 assessed only):")
    imp_lines.append(f"  {'Persona':<8} {'N deal':<8} {'CG deal':<12} {'N impasse':<10} {'CG impasse'}")
    for persona, v in imp["impasse_vs_deal_cg"].items():
        cg_d = f"{v['mean_cg_deal']:+.1f}" if not (isinstance(v['mean_cg_deal'], float) and v['mean_cg_deal'] != v['mean_cg_deal']) else "N/A"
        cg_i = f"{v['mean_cg_impasse']:+.1f}" if v['n_impasse'] > 0 and not (isinstance(v['mean_cg_impasse'], float) and v['mean_cg_impasse'] != v['mean_cg_impasse']) else "N/A"
        imp_lines.append(f"  {persona:<8} {v['n_deal']:<8} {cg_d:<12} {v['n_impasse']:<10} {cg_i}")
    atomic_write_text(IMPASSE_PATH, "\n".join(imp_lines) + "\n")

    # === ADDITIONAL STATISTICS OUTPUT ===
    add = []
    add.append("ADDITIONAL STATISTICAL ANALYSES")
    add.append("=" * 60)
    add.append("Note: All tests are non-parametric. Effect sizes (Cohen's d) for reference only.")
    add.append("")

    add.append("── 1. H2 Cohen's d ──")
    h2 = out["H2"]
    add.append(f"  Phase1 vs Phase2 abs CG: d = {h2['cohens_d']:+.3f}  (U={h2['mann_whitney_U']:.0f}, p={h2['p_value_mw']:.4f} {h2['sig_mw']})")
    add.append("")

    add.append("── 2. H3 Cohen's d (Phase 2 levels) ──")
    h3 = out["H3"]
    add.append(f"  High-C vs Low-C Phase2 CG: d = {h3['cohens_d_p2']:+.3f}  (U={h3['mann_whitney_p2_U']:.0f}, p={h3['mann_whitney_p2_p']:.4f} {h3['mann_whitney_p2_sig']})")
    add.append("")

    add.append("── 3. Per-persona Phase1 vs Phase2 seller CG (unpaired Mann-Whitney) ──")
    ppt = out["per_persona_phase_test"]
    add.append(f"  {'Persona':<6} {'P1 mean':>8} {'P2 mean':>8} {'Shift':>8} {'U':>8} {'p':>8} {'sig':>6} {'d':>7}")
    for persona, v in ppt.items():
        m1 = f"{v['mean_phase1']:+.1f}" if not math.isnan(v['mean_phase1']) else "N/A"
        m2 = f"{v['mean_phase2']:+.1f}" if not math.isnan(v['mean_phase2']) else "N/A"
        sh = f"{v['shift']:+.1f}"        if not math.isnan(v['shift'])       else "N/A"
        u  = f"{v['mann_whitney_U']:.0f}" if not math.isnan(v['mann_whitney_U']) else "N/A"
        pv = f"{v['p_value']:.4f}"       if not math.isnan(v['p_value'])     else "N/A"
        d  = f"{v['cohens_d']:+.3f}"     if not math.isnan(v['cohens_d'])    else "N/A"
        add.append(f"  {persona:<6} {m1:>8} {m2:>8} {sh:>8} {u:>8} {pv:>8} {v['sig']:>6} {d:>7}")
    add.append("  Note: unpaired — rounds are independent draws per phase")
    add.append("")

    add.append("── 4. Pearson r (turns vs CG) with p-values ──")
    cwp = out["transcript_correlation_with_p"]
    for ph in ["phase1", "phase2"]:
        v = cwp[ph]
        add.append(f"  {ph}  seller: r={v['r_seller']:+.3f} p={v['p_seller']:.4f} {v['sig_seller']}  n={v['n_seller']}    buyer: r={v['r_buyer']:+.3f} p={v['p_buyer']:.4f} {v['sig_buyer']}  n={v['n_buyer']}")
    add.append("")

    add.append("── 5. Kruskal-Wallis on deal price deviation across pairings ──")
    kw = out["kruskal_wallis_deviation"]
    add.append(f"  H = {kw['H']:.3f}, df = {kw['df']}, p = {kw['p_value']:.4f}  {kw['sig']}")
    add.append(f"  Note: {kw['note']}")
    add.append("")

    add.append("── 6. Fidelity score Mann-Whitney (seller, selected pairs) ──")
    ft = out["fidelity_tests"]
    add.append(f"  {'Comparison':<20} {'Mean A':>8} {'Mean B':>8} {'U':>8} {'p':>8} {'sig':>6}")
    for key, v in ft.items():
        ma = f"{v['mean_a']:.3f}" if not math.isnan(v['mean_a']) else "N/A"
        mb = f"{v['mean_b']:.3f}" if not math.isnan(v['mean_b']) else "N/A"
        u  = f"{v['U']:.0f}"     if not math.isnan(v['U'])      else "N/A"
        pv = f"{v['p']:.4f}"     if not math.isnan(v['p'])      else "N/A"
        add.append(f"  {key:<20} {ma:>8} {mb:>8} {u:>8} {pv:>8} {v['sig']:>6}")
    add.append("  Note: lexical fidelity proxy — statistical significance means keyword overlap differs, not deep behavioral validity")
    add.append("")

    add.append("── 7. Buyer CG descriptive (no inferential tests — role asymmetry confound) ──")
    bcd = out["buyer_cg_descriptive"]
    add.append(f"  {'Persona':<6} {'P1 mean':>10} {'P1 n':>6} {'P2 mean':>10} {'P2 n':>6}")
    for persona, v in bcd.items():
        m1 = f"{v['phase1_mean']:+.1f}" if not math.isnan(v['phase1_mean']) else "N/A"
        m2 = f"{v['phase2_mean']:+.1f}" if not math.isnan(v['phase2_mean']) else "N/A"
        add.append(f"  {persona:<6} {m1:>10} {v['phase1_n']:>6} {m2:>10} {v['phase2_n']:>6}")
    add.append("  Note: buyer CG inflated by role asymmetry in actual score computation — cross-role comparisons invalid")
    add.append("")

    add.append("── 8. Fisher's exact test: Phase 1 vs Phase 2 impasse rate ──")
    fi = out["fisher_impasse_phase"]
    add.append(f"  Phase 1: {fi['phase1_impasse']}/{fi['phase1_total']} impasses ({fi['phase1_rate']:.1%})")
    add.append(f"  Phase 2: {fi['phase2_impasse']}/{fi['phase2_total']} impasses ({fi['phase2_rate']:.1%})")
    add.append(f"  Fisher's exact p = {fi['fisher_p']:.4f}  {fi['sig']}")
    add.append(f"  Note: {fi['note']}")

    atomic_write_text("outputs/analysis_additional.txt", "\n".join(add) + "\n")


def generate_figures(out: dict, figures_dir: str = "outputs/figures") -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("[WARN] matplotlib not installed — skipping figure generation. Run: pip install matplotlib")
        return

    os.makedirs(figures_dir, exist_ok=True)

    PERSONAS = ["AP", "WA", "IC", "TD"]
    # Okabe-Ito colorblind-safe palette
    BLUE   = "#0072B2"  # blue
    ORANGE = "#E69F00"  # orange
    SKY    = "#56B4E9"  # sky blue
    VERMIL = "#D55E00"  # vermilion (distinguishable from blue even in greyscale)
    PURPLE = "#CC79A7"  # reddish purple
    LBLUE  = "#009E73"  # bluish green (safe replacement for teal/green)
    YELLOW = "#F0E442"  # yellow (use sparingly, low contrast on white)
    GRAY   = "#888780"
    LGRAY  = "#D3D1C7"

    def savefig(fig, name):
        path = os.path.join(figures_dir, name)
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"  [FIG] {path}")

    # ── Figure 1: Calibration gap by persona, Phase 1 vs Phase 2 ──────────────
    calib = out["calibration_metrics"]
    p1_cg = [calib["phase1"][p]["mean_CG"] for p in PERSONAS]
    p2_cg = [calib["phase2"][p]["mean_CG"] for p in PERSONAS]
    x = range(len(PERSONAS))
    w = 0.35
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars1 = ax.bar([i - w/2 for i in x], p1_cg, w, color=BLUE,   label="Phase 1", zorder=3)
    bars2 = ax.bar([i + w/2 for i in x], p2_cg, w, color=ORANGE, label="Phase 2", zorder=3)
    ax.set_xticks(list(x))
    ax.set_xticklabels(PERSONAS, fontsize=11)
    ax.set_ylabel("Mean calibration gap", fontsize=11)
    ax.set_ylim(50, 115)
    ax.yaxis.grid(True, color=LGRAY, linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top","right"]].set_visible(False)
    for bar in list(bars1) + list(bars2):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8,
                f"+{bar.get_height():.1f}", ha="center", va="bottom", fontsize=8, color="#444")
    # H2 significance annotation — overall Phase1 vs Phase2
    h2     = out["H2"]
    h2_sig = h2["sig_mw"]
    h2_p   = h2["p_value_mw"]
    p_str  = f"p = {h2_p:.4f}" if not math.isnan(h2_p) else "p = n/a"
    ax.annotate(f"Phase 1 vs Phase 2 (all personas)\n{p_str}  {h2_sig}",
                xy=(1.5, 102), ha="center", fontsize=8, color="#333",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=LGRAY, lw=0.8))
    ax.legend(frameon=False, fontsize=10)
    ax.set_title("Fig 1 — Calibration gap by persona: Phase 1 vs Phase 2", fontsize=10, pad=10)
    fig.tight_layout()
    savefig(fig, "fig1_cg_by_persona_phase.png")

    # ── Figure 2: H1 — High-A vs Low-A mean CG with CI bars ───────────────────
    h1 = out["H1"]
    groups    = ["High-A\n(WA + TD)", "Low-A\n(AP + IC)"]
    means     = [h1["high_A_mean_CG"], h1["low_A_mean_CG"]]
    cis_lo    = [h1["high_A_CI"][0],   h1["low_A_CI"][0]]
    cis_hi    = [h1["high_A_CI"][1],   h1["low_A_CI"][1]]
    errs_lo   = [means[i] - cis_lo[i] for i in range(2)]
    errs_hi   = [cis_hi[i] - means[i] for i in range(2)]
    colors    = [PURPLE, VERMIL]
    fig, ax = plt.subplots(figsize=(5, 4.5))
    bars = ax.bar(groups, means, color=colors, width=0.45, zorder=3)
    ax.errorbar(groups, means, yerr=[errs_lo, errs_hi],
                fmt="none", color="#333", capsize=6, linewidth=1.5, zorder=4)
    ax.set_ylabel("Mean seller CG (Phase 1)", fontsize=11)
    ax.set_ylim(60, 100)
    ax.yaxis.grid(True, color=LGRAY, linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top","right"]].set_visible(False)
    for bar, m in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width()/2, m + 0.8,
                f"+{m:.1f}", ha="center", va="bottom", fontsize=10, color="#333")
    h1     = out["H1"]
    h1_sig = sig_label(h1["p_value"])
    p_str  = f"p = {h1['p_value']:.4f}"
    # significance bracket
    y_bracket = max(means) + max(errs_hi) + 3
    ax.plot([0, 0, 1, 1], [y_bracket-1, y_bracket, y_bracket, y_bracket-1],
            color="#333", linewidth=1.2)
    ax.text(0.5, y_bracket + 0.5, f"{p_str}  {h1_sig}",
            ha="center", va="bottom", fontsize=9, color="#333")
    ax.set_title("Fig 2 — H1: High-A vs Low-A calibration gap\n(direction opposite to prediction)", fontsize=10, pad=8)
    fig.tight_layout()
    savefig(fig, "fig2_h1_agreeableness_cg.png")

    # ── Figure 3: H3 — CG shift Phase 1→2 by Conscientiousness group ──────────
    h3 = out["H3"]
    phases_label = ["Phase 1", "Phase 2"]
    hc = [h3["High-C"]["phase1_mean"], h3["High-C"]["phase2_mean"]]
    lc = [h3["Low-C"]["phase1_mean"],  h3["Low-C"]["phase2_mean"]]
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    ax.plot(phases_label, hc, marker="o", color=BLUE,   linewidth=2,
            markersize=8, label=f"High-C (AP+WA)  Δ {h3['High-C']['shift']:+.1f}")
    ax.plot(phases_label, lc, marker="s", color=ORANGE, linewidth=2, linestyle="--",
            markersize=8, label=f"Low-C  (IC+TD)   Δ {h3['Low-C']['shift']:+.1f}")
    for vals, col in [(hc, BLUE), (lc, ORANGE)]:
        for i, v in enumerate(vals):
            ax.text(i, v + 1.2, f"+{v:.1f}", ha="center", va="bottom", fontsize=9, color=col)
    ax.set_ylabel("Mean seller CG", fontsize=11)
    ax.set_ylim(55, 105)
    ax.yaxis.grid(True, color=LGRAY, linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top","right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=9)
    h3      = out["H3"]
    h3_sig  = h3["mann_whitney_p2_sig"]
    h3_p    = h3["mann_whitney_p2_p"]
    p_str   = f"p = {h3_p:.4f}" if not math.isnan(h3_p) else "p = n/a"
    ax.text(0.5, 0.97,
            f"High-C vs Low-C Phase 2: {p_str}  {h3_sig}",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=8, color="#333",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=LGRAY, lw=0.8))
    ax.set_title("Fig 3 — H3: Calibration shift Phase 1→2 by Conscientiousness", fontsize=10, pad=8)
    fig.tight_layout()
    savefig(fig, "fig3_h3_conscientiousness_shift.png")

    # ── Figure 4: Deal rates and deviation from fair value by pairing ──────────
    dr = out["deal_rates"]
    pairings_order = [("AP","AP"),("WA","WA"),("IC","IC"),("TD","TD"),
                      ("AP","WA"),("WA","IC"),("IC","TD"),("TD","AP")]
    labels   = [f"{s}×{b}" for s, b in pairings_order]
    rates    = [dr.get((s,b), {}).get("rate", 0) * 100 for s, b in pairings_order]
    devs     = [dr.get((s,b), {}).get("deviation", 0) or 0 for s, b in pairings_order]
    within_mask = [i < 4 for i in range(8)]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
    bar_colors = [BLUE if m else SKY for m in within_mask]
    ax1.bar(labels, rates, color=bar_colors, zorder=3)
    ax1.set_ylim(80, 105)
    ax1.set_ylabel("Deal rate (%)", fontsize=11)
    ax1.set_xticks(range(len(labels)))
    ax1.set_xticklabels(labels, rotation=40, ha="right", fontsize=9)
    ax1.yaxis.grid(True, color=LGRAY, linewidth=0.5, zorder=0)
    ax1.set_axisbelow(True)
    ax1.spines[["top","right"]].set_visible(False)
    ax1.set_title("Deal rate by pairing", fontsize=10)
    ax2.bar(labels, devs, color=bar_colors, zorder=3)
    ax2.set_ylabel("Mean deviation from fair value ($)", fontsize=11)
    ax2.set_xticks(range(len(labels)))
    ax2.set_xticklabels(labels, rotation=40, ha="right", fontsize=9)
    ax2.yaxis.grid(True, color=LGRAY, linewidth=0.5, zorder=0)
    ax2.set_axisbelow(True)
    ax2.spines[["top","right"]].set_visible(False)
    ax2.set_title("Deviation from fair value ($300)", fontsize=10)
    legend_patches = [mpatches.Patch(color=BLUE, label="Within-persona"),
                      mpatches.Patch(color=SKY,  label="Cross-persona")]
    fig.legend(handles=legend_patches, loc="upper center", ncol=2,
               frameon=False, fontsize=9, bbox_to_anchor=(0.5, 1.01))
    fig.suptitle("Fig 4 — Deal outcomes by persona pairing (Phase 1)", fontsize=10, y=1.05)
    fig.tight_layout()
    savefig(fig, "fig4_deal_rates_deviation.png")

    # ── Figure 5: Impasse CG vs deal CG for AP (Phase 1 assessed) ─────────────
    imp = out["impasse_analysis"]["impasse_vs_deal_cg"]
    ap = imp["AP"]
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    categories = ["Deal rounds\n(n=18)", "Impasse rounds\n(n=2)"]
    values     = [ap["mean_cg_deal"], ap["mean_cg_impasse"]]
    colors_imp = [PURPLE, VERMIL]
    bars = ax.bar(categories, values, color=colors_imp, width=0.4, zorder=3)
    ax.set_ylabel("Mean seller CG", fontsize=11)
    ax.set_ylim(70, 115)
    ax.yaxis.grid(True, color=LGRAY, linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top","right"]].set_visible(False)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, v + 0.8,
                f"+{v:.1f}", ha="center", va="bottom", fontsize=11, color="#333")
    ax.set_title("Fig 5 — AP seller: CG in deal vs impasse rounds\n(Phase 1, process-confidence inflation)", fontsize=10, pad=8)
    fig.tight_layout()
    savefig(fig, "fig5_impasse_cg_ap.png")

    print(f"[FIGS] All figures saved to {figures_dir}/")


def main() -> None:
    results = load_results()
    validate_input_schema(results)
    out = analyze(results)
    write_outputs(out)
    generate_figures(out)
    print("Analysis complete.")


if __name__ == '__main__':
    main()
