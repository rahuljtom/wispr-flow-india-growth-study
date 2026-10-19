"""Build outputs/deck/deck.pptx from the ledger and processed tables (rules 11, 14).

Every number on a slide must exist in data/ledger/numbers_ledger.csv; footnotes are generated
from the ledger rows named for each slide. Wording: directional, scenario, not estimable,
reported by.
"""
import json
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt

from src.analysis.sizing import EXPERIMENTS, HEADLINE
from src.common.ledger import add_claim, read_ledger
from src.deck.layout import fit_pt, table_height_in

OUT = Path("outputs/deck/deck.pptx")
AS_OF = "2026-10-18"
W, H = Inches(13.333), Inches(7.5)


def ledger_once(cid, *a, **kw):
    if not any(r["claim_id"] == cid for r in read_ledger()):
        add_claim(cid, *a, **kw)


def upsert(cid, *a, **kw):
    """Deck-generated claims are refreshed when the underlying tables change."""
    import csv

    from src.common.ledger import COLS, LEDGER

    rows = [r for r in read_ledger() if r["claim_id"] != cid]
    with open(LEDGER, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    add_claim(cid, *a, **kw)


def foot(ids):
    rows = {r["claim_id"]: r for r in read_ledger()}
    parts = []
    for i in ids:
        r = rows.get(i)
        if not r:
            raise KeyError(f"claim {i} not in ledger")
        if r["source_url"]:
            src = urlparse(r["source_url"]).netloc.replace("www.", "")
            when = f", {r['source_date']}" if r["source_date"] else ""
            when += f", read {r['retrieved_on']}" if r["retrieved_on"] else ""
            origin = f"{src}{when}"
        else:
            origin = {"derived": "derived in project", "estimated": "estimated from project data",
                      "assumption": "assumption", "unknown": "unknown"}.get(r["status"], r["status"])
        parts.append(f"{i} {r['status']} ({origin})")
    return "Sources: " + "; ".join(parts)


class Deck:
    def __init__(self):
        self.p = Presentation()
        self.p.slide_width, self.p.slide_height = W, H

    def slide(self, title, bullets=(), image=None, table=None, ids=(), note="", image_w=7.4, small=False,
              col_w=None, tiles=()):
        assert len(bullets) <= 3, "max 3 bullets"
        s = self.p.slides.add_slide(self.p.slide_layouts[6])
        tb = s.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(1.3))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.text = title
        tpt = fit_pt([title], 12.2, 1.25, 24 if not small else 20, 14)
        tf.paragraphs[0].runs[0].font.size = Pt(tpt)
        tf.paragraphs[0].runs[0].font.bold = True
        top, bottom = 1.7, 6.45
        if tiles:
            from pptx.dml.color import RGBColor
            from pptx.enum.shapes import MSO_SHAPE
            from pptx.enum.text import PP_ALIGN

            tw = (12.3 - 0.4 * (len(tiles) - 1)) / len(tiles)
            for i, (big, cap, rgb) in enumerate(tiles):
                box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5 + i * (tw + 0.4)), Inches(top),
                                         Inches(tw), Inches(1.6))
                box.fill.solid()
                box.fill.fore_color.rgb = RGBColor(*rgb)
                box.line.fill.background()
                tf2 = box.text_frame
                tf2.word_wrap = True
                tf2.text = big
                tf2.paragraphs[0].alignment = PP_ALIGN.CENTER
                tf2.paragraphs[0].runs[0].font.size = Pt(40)
                tf2.paragraphs[0].runs[0].font.bold = True
                tf2.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
                p2 = tf2.add_paragraph()
                p2.text = cap
                p2.alignment = PP_ALIGN.CENTER
                p2.font.size = Pt(14)
                p2.font.color.rgb = RGBColor(255, 255, 255)
            top += 1.9
        left_w = 12.3
        if image:
            from PIL import Image

            w_px, h_px = Image.open(image).size
            image_w = min(image_w, (bottom - top) * w_px / h_px)
            s.shapes.add_picture(str(image), Inches(0.5), Inches(top), width=Inches(image_w))
            left_w = 12.3 - image_w - 0.3
        if bullets:
            x = 0.5 + (image_w + 0.3 if image else 0)
            texts = ["• " + t for t in bullets]
            bpt = fit_pt(texts, left_w - 0.2, bottom - top, 16, 10, space_after_pt=10)
            b = s.shapes.add_textbox(Inches(x), Inches(top), Inches(left_w), Inches(bottom - top)).text_frame
            b.word_wrap = True
            for k, t in enumerate(texts):
                para = b.paragraphs[0] if k == 0 else b.add_paragraph()
                para.text = t
                para.font.size = Pt(bpt)
                para.space_after = Pt(10)
        if table is not None:
            rows, cols = len(table), len(table[0])
            col_w = col_w or [12.3 / cols] * cols
            tpt2 = 14
            while tpt2 > 8 and table_height_in(table, col_w, tpt2) > bottom - top:
                tpt2 -= 1
            gshape = s.shapes.add_table(rows, cols, Inches(0.5), Inches(top), Inches(12.3), Inches(0.3 * rows))
            gt = gshape.table
            for c, w in enumerate(col_w):
                gt.columns[c].width = Inches(w)
            for r in range(rows):
                for c in range(cols):
                    cell = gt.cell(r, c)
                    cell.text = str(table[r][c])
                    for para in cell.text_frame.paragraphs:
                        para.font.size = Pt(tpt2)
                        para.font.bold = r == 0
        foot_text = (foot(ids) if ids else "") + (("  " + note) if note else "")
        ft = s.shapes.add_textbox(Inches(0.5), Inches(6.55), Inches(12.3), Inches(0.9)).text_frame
        ft.word_wrap = True
        ft.text = foot_text
        fpt = fit_pt([foot_text], 12.2, 0.85, 9, 6)
        for para in ft.paragraphs:
            para.font.size = Pt(fpt)
        return s

    def save(self):
        import datetime as dt

        cp = self.p.core_properties
        cp.title = "Wispr Flow India: public-signals growth diagnostic"
        cp.subject = "Public-source diagnostic; see the repository README for methods and limitations"
        cp.author = "wispr-flow-analytics"
        cp.last_modified_by = "wispr-flow-analytics"
        cp.comments = ""
        cp.keywords = ""
        cp.created = cp.modified = dt.datetime.now(dt.UTC).replace(tzinfo=None, microsecond=0)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        self.p.save(OUT)


def themes():
    t = pd.read_csv("data/processed/themes_by_segment.csv")
    a = t[t.segment == "all tagged sample"]
    n = int(a.n_segment.iloc[0])
    top = a[~a.theme.isin(["other"])].sort_values("share", ascending=False).head(3)
    return t, n, top


def add_theme_claims(t, n, top, cov):
    partial = not cov["complete"]
    upsert("R-050", "slide 4", "Tagged review sample size", n, "reviews", "estimated", n=n,
           derivation="seeded stratified sample of non-gold reviews, frozen v3 tagger"
           + (f"; INTERIM: {n} of {cov['sample']} sampled reviews tagged (newest Play reviews only)" if partial else ""),
           caveat="sample of public store reviews, not all users" + ("; recency-biased interim subset" if partial else ""))
    upsert("R-057", "slide 4", "Selected bulk-tagging sample size", cov["sample"], "reviews", "assumption" if False else "estimated",
           n=cov["sample"], derivation="seed 20261018, proportional over store x rating, gold reviews excluded",
           caveat="selection size, not a measurement")
    for k, (_, r) in enumerate(top.iterrows()):
        upsert(f"R-05{k + 1}", "slide 4", f"Share of tagged reviews with theme {r.theme}",
               round(r.share * 100, 1), "%", "estimated", n=n,
               derivation=f"method: Wilson 95% CI {r.ci_lo * 100:.1f}-{r.ci_hi * 100:.1f}%; share of reviews carrying theme",
               caveat="directional; tagger test micro-F1 in R-040" + ("; interim recency-biased subset" if partial else ""))


def main():
    t, n, top = themes()
    cov = json.loads(Path("data/processed/a1_coverage.json").read_text())
    add_theme_claims(t, n, top, cov)
    low = t[(t.segment == "rating<=2 (low-rated)") & (t.n_with_theme > 0)]
    n_low = int(low.n_segment.iloc[0])
    upsert("R-058", "slide 3", "Low-rated (one or two stars) reviews in the tagged sample", n_low, "reviews",
           "estimated", n=n_low, derivation="subset of R-050 with rating at most two",
           caveat="interim, newest Play reviews only")
    d = Deck()
    # 1 summary
    d.slide("India is 14% of installs but 2% of in-app revenue (reported); public signals show where to look",
            ["Reported by Sensor Tower via TechCrunch, Oct 2025 to Apr 2026; in-app purchases only.",
             "Scenario, not causal: revenue per install is 0.143 of the global rate; price alone implies 0.283.",
             "Ask: internal activation, retention and price-test data to replace these public proxies."],
            tiles=[("14%", "of installs from India (reported)", (59, 110, 168)),
                   ("2%", "of in-app purchase revenue (reported)", (224, 123, 57)),
                   ("0.143", "revenue per install vs global (scenario)", (110, 110, 110))],
            ids=["R-002", "R-003", "R-011", "R-012"], note=f"Data as of {AS_OF}.")
    # 2 gap
    d.slide("Price alone would imply 0.283 of the global revenue per install against 0.143 observed; the 0.504 residual "
            "cannot be apportioned (range 0.22 to 1.22)",
            ["In-app purchases only. The company says India is its second-largest base by users and paying subscribers, yet web and desktop plans bill through Stripe, outside this measure (hypothesis: much India revenue sits outside the app stores).",
             "Index compares annual list prices at an implied FX; promotions, free tier and billing route are excluded.",
             "Install mix shifted inside the window (Android launch in February, India launch at the very end)."],
            image="outputs/charts/gap_decomposition.png", image_w=7.9, small=True,
            ids=["R-001", "R-002", "R-003", "R-010", "R-005", "R-011", "R-012", "R-013", "R-014", "R-085", "R-119"])
    # 3 themes
    d.slide(f"Most common review themes in an interim sample of {n} reviews: {', '.join(top.theme.str.replace('_', ' '))}; "
            "India-versus-US is not estimable",
            ["Pricing is higher and praise lower among the one- and two-star reviews (intervals do not overlap); other gaps are noise.",
             f"Interim: {n} of {cov['sample']} selected, newest Play reviews only; Play has no country split.",
             "'Other' is the largest bucket; no tagged review is in the roman-Hindi/Devanagari proxy."],
            image="outputs/charts/themes_overall_vs_low_rated.png", image_w=7.6, small=True,
            ids=["R-050", "R-057", "R-058", "R-051", "R-052", "R-053", "R-040"],
            note="Directional; tagger test results in appendix.")
    # 4 competitors and price
    d.slide("Gboard is the most dangerous free substitute; Superflow is the closest dedicated dictation rival (claims untested)",
            ["Gboard leads the matrix at 13 of 15 with every criterion sourced: free voice typing, Hindi, 10B+ global installs.",
             "Superflow (Android, March 2026; Bengaluru developer) scores 11 on four known criteria, ahead of Typeless 9 and Aqua Voice 7; its price is unknown (11 to 14 possible).",
             "Install bands are global, claims advertised, Play item prices lack billing periods; Wispr's own Play items run 400 to 3849 INR."],
            image="outputs/charts/price_ladder.png", image_w=7.4, small=True,
            ids=["R-070", "R-071", "R-114", "R-115", "R-116", "R-117", "R-118", "R-016"],
            note="Rubric and full matrix: data/processed/competitor_matrix.csv and the dashboard. Superwhisper and Apple list prices are unknown and not charted; Play item ranges are not compared with Flow's price.")
    # 5 checkout and offers
    rows = [["Item", "What is documented or advertised", "Status"],
            ["India price", "320 INR a month billed annually (3840 a year, derived) or 400 INR monthly", "Reported, India page"],
            ["Payment", ("UPI and cards (Visa, Mastercard, American Express, Discover) plus one unnamed option; Wispr-specific UPI on "
             "Google Play and net banking are unverified"), "Advertised, not tested"],
            ["Free plan", "Weekly caps per docs: mobile soft 1000 / hard 1500 words, desktop 2000 / 5000; India page says unlimited",
             "Docs vs marketing copy"],
            ["Partner offers", ("Zepto 3 months, CRED 10 months of Pro (CRED length set per code); browser claim, individual plans, card at "
             "checkout, renews unless cancelled"), "Documented; redeemable today unknown"],
            ["Students", "50% off Pro (India page); 3 months free for new Pro students (students page); help doc: terms set per account",
             "Sources disagree"],
            ["Android launch offer", "Free with no cap during early access at launch; not in current docs", "Launch only; current unknown"]]
    d.slide("Checkout, free tier and offers: what is documented, and where the sources disagree", table=rows,
            col_w=[1.9, 7.4, 3.0], small=True,
            ids=["R-070", "R-071", "R-072", "R-007", "R-008", "R-080", "R-081", "R-074", "R-075", "R-076", "R-077", "R-078"],
            note="No payment method or offer was tested; nothing here is universal.")
    # 6 trends
    d.slide("Search data cannot isolate the Bengaluru campaign (not estimable); a geo-split launch test could",
            ["Only 2 of 5 states had enough pre-period search activity; a comparison needs at least 2 controls.",
             "Interest rose in every state after the provisional date, so a Karnataka-specific change is not separable.",
             "Better: geo-split launch with install attribution, or a holdout city."],
            image="outputs/charts/trends_event_study.png", ids=["R-107", "R-091"], image_w=7.6,
            note="Directional Google Trends index; campaign date reported by Economic Times, exact start unverified.")
    # 7 experiments
    s7 = pd.read_csv("data/processed/experiment_sizing.csv")
    rule = {k[:2]: v["short_rule"] for k, v in EXPERIMENTS.items()}
    rows = [["Experiment", "Primary metric", "Baseline", "MDE", "n per arm", "Days incl. follow-up", "Decision rule"]]
    heads = HEADLINE
    for k, (name, g) in enumerate(s7.groupby("experiment")):
        base, mde = heads[name[:2]]
        c = g[(g.baseline == base) & (g.mde_abs == mde)]
        lo, hi = c.total_days.min(), c.total_days.max()
        n_arm = int(c.n_per_arm.iloc[0])
        fu = int(c.follow_up_days.iloc[0])
        upsert(f"R-06{k}", "slide 7", f"{name[:2]} headline sizing: baseline, MDE, n per arm, days low-high incl. follow-up",
               f"{base}; {mde}; {n_arm}; {lo}-{hi}; follow-up {fu}", "mixed", "estimated", n=n_arm,
               derivation="statsmodels NormalIndPower, alpha 0.05, power 0.8, two-sided; days = 2n/(1650 x android x eligible x "
               "exposed) plus follow-up window", caveat="baseline and MDE are illustrative assumptions; scenario grid and "
               "follow-up windows in ASSUMPTIONS.md" + ("; E3 duration is a rough proxy (unit mismatch)" if name.startswith("E3") else ""))
        rows.append([name, c.primary_metric.iloc[0], f"{base:.0%}" if False else base, mde, n_arm, f"{lo}-{hi}", rule[name[:2]]])
    d.slide("Three experiments sized to India traffic (illustrative baselines); 1650 installs a day is a window average",
            table=rows, small=True, col_w=[2.3, 2.1, 0.8, 0.7, 0.9, 1.4, 4.1],
            ids=["R-060", "R-061", "R-062", "R-100"],
            note=("Baselines and MDEs are assumptions; guardrail limits need internal baselines; E3 duration is a proxy; E2 tests a "
                  "cap level, not unlimited. Grid: data/processed/experiment_sizing.csv."))
    # 8 plan
    rows = [["Month one", "Months two and three", "Internal data to request"],
            ["Activation funnel by platform\nAndroid permission drop-off\nFree-tier cap behaviour",
             "Run E1 (permission flow)\nThen E3 (invite loop)\nE2 as a cap-level test",
             "Cohort retention\nPrice-test history\nPaid conversion by channel\nWeb versus store billing"]]
    d.slide("First three months, and the internal data I would ask for to replace these proxies", table=rows,
            col_w=[4.1, 4.1, 4.1], ids=[])
    # 9 appendix data and tagging
    rows = [["Topic", "Facts"],
            ["Play reviews", "3000 pulled, history from 2026-03; reviews are not split by country"],
            ["App Store", "RSS feed erratic and non-contiguous; India and US windows do not overlap"],
            ["Trends", "5 states, weekly; 2 with enough pre-period data; one rate-limit retry resolved"],
            ["Tagger, test", ("60 reviews scored once: micro-F1 0.784 (95% interval 0.72-0.85), sentiment kappa 0.830 (0.68-0.95); "
             "only 7 of 17 themes had enough examples")],
            ["Tagger, dev", "40 reviews after the label audit: micro-F1 0.752; the prompt was chosen on dev, so this is optimistic"],
            ["Gold labels", "One labeller; labels revised after the dev analysis; free-tier model processing"]]
    d.slide("Appendix: data coverage and tagging evaluation", table=rows, col_w=[2.0, 10.3], small=True,
            ids=["R-106", "R-107", "R-040", "R-041", "R-113", "R-103", "R-104", "R-105"])
    # 10 appendix assumptions and limitations
    rows = [["Topic", "Assumptions and limitations"],
            ["Scenario parameters", "Android share 30/50/70%, eligible 50/80%, exposed 50/100%; missed revenue 0 to 60%; baselines illustrative"],
            ["Revenue", "In-app purchases only, from one secondary article; FX implied by that article"],
            ["Reviews", "Not all users; Play has no country split; interim newest-reviews subset; small one-labeller gold set"],
            ["Trends", "Relative and state-level; sparse controls; campaign date reported, start unverified"],
            ["Competitors", "Scores rest on Play listings and developer claims; install bands are global, not India; Apple dictation and Eloquent unscored; competitor reviews not tagged"],
            ["Payments and offers", "Advertised or documented, not tested; no offer shown to be universal"]]
    d.slide("Appendix: assumptions and limitations", table=rows, col_w=[2.2, 10.1], small=True,
            ids=["R-108", "R-109", "R-110", "R-111"])
    d.save()
    print("saved", OUT, "slides:", len(d.p.slides))


if __name__ == "__main__":
    main()
