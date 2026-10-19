"""Side-by-side dev comparison of prompt versions (reads data/interim/eval_dev_dev_*.json)."""
import json
import sys
from pathlib import Path


def fmt(x):
    return "-" if x is None else f"{x:.2f}"


def main(versions=("v1", "v2", "v3")):
    ev = {v: json.loads(Path(f"data/interim/eval_dev_dev_{v}.json").read_text())
          for v in versions if Path(f"data/interim/eval_dev_dev_{v}.json").exists()}
    out = ["| prompt | n | micro-F1 (95% CI) | sentiment kappa (95% CI) |", "|---|---|---|---|"]
    for v, r in ev.items():
        out.append(f"| {v} | {r['n']} | {r['micro_f1']:.3f} ({r['micro_f1_ci95'][0]:.2f}-"
                   f"{r['micro_f1_ci95'][1]:.2f}) | {r['sentiment_kappa']:.3f} "
                   f"({r['sentiment_kappa_ci95'][0]:.2f}-{r['sentiment_kappa_ci95'][1]:.2f}) |")
    out += ["", ("Per-theme on dev (diagnostic; formal threshold is 5 gold examples). "
            "cells: precision / recall / F1."), "",
            "| theme | support | " + " | ".join(ev) + " |", "|---|---|" + "---|" * len(ev)]
    first = next(iter(ev.values()))
    for t, m in first["all_themes_dev_diagnostic"].items():
        cells = [f"{fmt(r['all_themes_dev_diagnostic'][t]['precision'])} / "
                 f"{fmt(r['all_themes_dev_diagnostic'][t]['recall'])} / "
                 f"{fmt(r['all_themes_dev_diagnostic'][t]['f1'])}" for r in ev.values()]
        if m["support"] or any(r["all_themes_dev_diagnostic"][t]["fp"] for r in ev.values()):
            out.append(f"| {t} | {m['support']} | " + " | ".join(cells) + " |")
    out += ["", "Sentiment confusion (rows gold, columns predicted; neg/neu/pos):", ""]
    for v, r in ev.items():
        cm = r["sentiment_confusion"]
        out.append(f"- {v}: " + "; ".join(f"{g}: " + "/".join(str(cm[g][p]) for p in cm) for g in cm))
    return "\n".join(out)


if __name__ == "__main__":
    print(main(tuple(sys.argv[1:]) or ("v1", "v2", "v3")))
