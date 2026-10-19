"""A7: experiment sizing (rule 7). Duration = 2n / (daily installs x android x eligible x exposed)."""
import itertools

import pandas as pd
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

DAILY_INSTALLS = 1650  # derived: 2.5M x 14% / 212 days (ASSUMPTIONS.md); window average, not today
ALPHA, POWER = 0.05, 0.8


def n_per_arm(p_base, p_alt, alpha=ALPHA, power=POWER):
    h = proportion_effectsize(p_alt, p_base)
    return float(NormalIndPower().solve_power(effect_size=abs(h), alpha=alpha, power=power,
                                              ratio=1.0, alternative="two-sided"))


def duration_days(n, android_share, eligible, exposed, daily_installs=DAILY_INSTALLS):
    return 2 * n / (daily_installs * android_share * eligible * exposed)


HEADLINE = {"E1": (0.3, 0.05), "E2": (0.02, 0.01), "E3": (0.2, 0.04)}  # illustrative baseline, MDE
EXPERIMENTS = {
    "E1 Android permission-flow redesign": {
        "short_name": "E1 Android permission flow",
        "short_rule": "Stop early on crash or D7-uninstall harm; roll out only if the lift's 95% interval excludes zero.",
        "metric": "first completed dictation within one day of install",
        "guardrails": "crash rate; D7 uninstall", "baselines": (0.2, 0.3, 0.4),
        "mdes": (0.03, 0.05, 0.08), "android": (0.3, 0.5, 0.7), "status": "sized",
        "follow_up_days": 7, "unit_note": "",
        "kill": "Stop early if crash rate or D7 uninstall is worse than a pre-registered limit; roll out only if "
                "the 95% interval of the lift excludes zero at full sample."},
    "E2 Android free-tier weekly cap level": {
        "short_name": "E2 Free-tier cap level",
        "short_rule": "Stop early if D7 retention falls below a floor; roll out only if the day-14 conversion lift is above zero.",
        "metric": "paid conversion by day 14", "guardrails": "D7 retention; support tickets",
        "baselines": (0.01, 0.02, 0.04), "mdes": (0.005, 0.01, 0.02), "android": (0.3, 0.5, 0.7),
        "status": "sized; premise changed: current docs cap the Android free tier (soft 1000, hard 1500 "
                  "shared with iOS), so E2 compares cap levels, not a cap against unlimited",
        "follow_up_days": 14, "unit_note": "",
        "kill": "Stop early if D7 retention in the stricter-cap arm falls below a pre-registered floor; roll out "
                "only if the 95% interval of the day-14 paid-conversion lift is above zero."},
    "E3 Family and WhatsApp invite loop": {
        "short_name": "E3 Invite loop",
        "short_rule": "Stop early on spam or opt-out spikes; scale only if the invite-to-dictation lift is above zero.",
        "metric": "invited users who complete a dictation", "guardrails": "invite opt-out; spam reports",
        "baselines": (0.1, 0.2, 0.3), "mdes": (0.02, 0.04, 0.06), "android": (1.0,),
        "status": "sized (platform-agnostic: android_share fixed at 1.0)",
        "follow_up_days": 7,
        "unit_note": "unit is invited users but traffic is installs per day; invitee volume is unknown, so "
                     "duration is a rough proxy, not an estimate",
        "kill": "Stop early if spam reports or invite opt-outs exceed a pre-registered limit; scale only if the "
                "95% interval of the invite-to-dictation lift is above zero."},
}


def sizing_table():
    rows = []
    for name, e in EXPERIMENTS.items():
        for base, mde, android, elig, expo in itertools.product(
                e["baselines"], e["mdes"], e["android"], (0.5, 0.8), (0.5, 1.0)):
            n = n_per_arm(base, base + mde)
            rows.append({"experiment": name, "primary_metric": e["metric"],
                         "guardrails": e["guardrails"], "baseline": base, "mde_abs": mde,
                         "n_per_arm": round(n), "android_share": android, "eligible_share": elig,
                         "exposed_share": expo, "daily_installs": DAILY_INSTALLS,
                         "duration_days": round(duration_days(n, android, elig, expo), 1),
                         "follow_up_days": e["follow_up_days"],
                         "total_days": round(duration_days(n, android, elig, expo) + e["follow_up_days"], 1),
                         "status": e["status"], "unit_note": e["unit_note"],
                         "guardrail_power": "guardrails are not separately powered; limits need internal baselines",
                         "kill_criterion": e["kill"]})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    t = sizing_table()
    t.to_csv("data/processed/experiment_sizing.csv", index=False)
    print(t.groupby("experiment").duration_days.agg(["min", "max"]))
