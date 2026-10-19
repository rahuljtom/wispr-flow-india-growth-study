"""Rough text-fit estimates for python-pptx shapes (no renderer is available in this environment).

Calibri-like average glyph width is about 0.5 em; line height 1.2 em. The estimate is deliberately
conservative so that shrinking fonts until it fits avoids clipping in PowerPoint.
"""
import math

CHAR_EM = 0.52
LINE_EM = 1.22


def lines_for(text, width_in, pt):
    cpl = max(1, int(width_in * 72 / (CHAR_EM * pt)))
    return sum(max(1, math.ceil(len(par) / cpl)) for par in str(text).split("\n"))


def block_height_in(paragraphs, width_in, pt, space_after_pt=0):
    lines = sum(lines_for(p, width_in, pt) for p in paragraphs)
    return (lines * pt * LINE_EM + space_after_pt * len(paragraphs)) / 72


def fit_pt(paragraphs, width_in, height_in, start, minimum, space_after_pt=0):
    pt = start
    while pt > minimum and block_height_in(paragraphs, width_in, pt, space_after_pt) > height_in:
        pt -= 1
    return pt


def table_height_in(rows, col_widths_in, pt):
    total = 0.0
    for r in rows:
        total += max(block_height_in([str(c)], max(w - 0.15, 0.3), pt) for c, w in zip(r, col_widths_in, strict=True)) + 0.1
    return total
