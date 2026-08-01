"""Generate the SVG figures used in the Mercato Blog.

    python tools/build_figures.py

Writes into assets/figures/. The output is generated: edit the specs at the
bottom of this file and re-run, don't touch the SVG.

Two reasons this exists rather than hand-drawn SVG or a diagram tool. Hand
placing coordinates means moving one box breaks its neighbours. Diagram tools
bake their own palette into the output, and these figures have to follow the
site theme, so every colour here is emitted as a CSS custom property.
"""

from __future__ import annotations

import xml.sax.saxutils as sax
from dataclasses import dataclass, field
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "figures"

# Figures are laid out to this width so they fill the article column at 1:1.
# Geometry stretches to reach it; type does not, so label size stays constant
# from figure to figure instead of depending on how wide the diagram happens
# to be.
TARGET_WIDTH = 1100

FONT = "Sora, sans-serif"
MONO = "JetBrains Mono, monospace"

TITLE_SIZE = 16
BODY_SIZE = 14.5
AXIS_SIZE = 13


def esc(text: str) -> str:
    return sax.escape(text)


# --------------------------------------------------------------------------
# Flow diagrams
# --------------------------------------------------------------------------


@dataclass
class Node:
    key: str
    title: str
    lines: tuple[str, ...] = ()
    col: int = 0
    row: float = 0
    accent: bool = False
    dashed: bool = False
    muted: bool = False


@dataclass
class Flow:
    name: str
    nodes: list[Node]
    edges: list[tuple[str, str]]
    dashed_edges: list[tuple[str, str]] = field(default_factory=list)
    col_widths: tuple[int, ...] = ()
    footnote: str = ""
    label: str = ""

    col_gap: int = 62
    row_pitch: int = 112
    pad_x: int = 12
    pad_y: int = 22

    def box_height(self, node: Node) -> int:
        return 46 + 18 * len(node.lines)

    def stretch(self) -> float:
        natural = sum(self.col_widths) + self.col_gap * (len(self.col_widths) - 1)
        return (TARGET_WIDTH - self.pad_x * 2) / natural

    def width_of(self, col: int) -> int:
        return round(self.col_widths[col] * self.stretch())

    def gap(self) -> int:
        return round(self.col_gap * self.stretch())

    def col_x(self, col: int) -> int:
        x = self.pad_x
        for i in range(col):
            x += self.width_of(i) + self.gap()
        return x

    def geometry(self) -> dict[str, tuple[int, float, int, int]]:
        """key -> (x, y, w, h), y being the box top."""
        out = {}
        for n in self.nodes:
            w = self.width_of(n.col)
            h = self.box_height(n)
            cy = self.pad_y + n.row * self.row_pitch + self.row_pitch / 2
            out[n.key] = (self.col_x(n.col), cy - h / 2, w, h)
        return out

    def render(self) -> str:
        geo = self.geometry()
        rows = max(n.row for n in self.nodes) + 1
        width = self.col_x(len(self.col_widths) - 1) + self.width_of(-1) + self.pad_x
        height = int(self.pad_y * 2 + rows * self.row_pitch) + (34 if self.footnote else 0)

        parts = [
            f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}"'
            f' role="img" aria-label="{esc(self.label)}" xmlns="http://www.w3.org/2000/svg">',
            '  <defs>',
            '    <marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="3.2" orient="auto">',
            '      <path d="M0 0 L8 3.2 L0 6.4 z" fill="currentColor" opacity="0.55"/>',
            '    </marker>',
            '  </defs>',
        ]

        def edge_path(a: str, b: str) -> str:
            ax, ay, aw, ah = geo[a]
            bx, by, bw, bh = geo[b]
            return f'M{ax + aw} {ay + ah / 2:.0f} L{bx - 4} {by + bh / 2:.0f}'

        if self.edges:
            parts.append(
                '  <g fill="none" stroke="currentColor" stroke-width="1.4" opacity="0.55"'
                ' marker-end="url(#arrow)">'
            )
            parts += [f'    <path d="{edge_path(a, b)}"/>' for a, b in self.edges]
            parts.append('  </g>')

        if self.dashed_edges:
            parts.append(
                '  <g fill="none" stroke="currentColor" stroke-width="1.3" opacity="0.4"'
                ' stroke-dasharray="4 3" marker-end="url(#arrow)">'
            )
            parts += [f'    <path d="{edge_path(a, b)}"/>' for a, b in self.dashed_edges]
            parts.append('  </g>')

        parts.append(f'  <g font-family="{FONT}" text-anchor="middle">')
        for n in self.nodes:
            x, y, w, h = geo[n.key]
            cx = x + w / 2

            if n.accent:
                fill, stroke, sw = "var(--accent-wash)", "var(--accent)", "1.4"
            elif n.muted:
                fill, stroke, sw = "var(--surface-raised)", "var(--border-strong)", "1.2"
            else:
                fill, stroke, sw = "var(--surface-card)", "var(--border-strong)", "1.2"
            dash = ' stroke-dasharray="4 3"' if n.dashed else ""
            if n.dashed:
                stroke = "var(--border)"

            parts.append(
                f'    <rect x="{x}" y="{y:.0f}" width="{w}" height="{h}" rx="7"'
                f' fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>'
            )

            ty = y + (h - 18 * len(n.lines)) / 2 + 5
            parts.append(
                f'    <text x="{cx:.0f}" y="{ty:.0f}" font-size="{TITLE_SIZE}"'
                f' font-weight="700" fill="var(--text-primary)">{esc(n.title)}</text>'
            )
            for i, line in enumerate(n.lines):
                parts.append(
                    f'    <text x="{cx:.0f}" y="{ty + 19 + i * 17:.0f}" font-size="{BODY_SIZE}"'
                    f' fill="var(--text-muted)">{esc(line)}</text>'
                )

        if self.footnote:
            parts.append(
                f'    <text x="{width / 2:.0f}" y="{height - 12}" font-size="{AXIS_SIZE}"'
                f' fill="var(--text-muted)">{esc(self.footnote)}</text>'
            )
        parts.append('  </g>')
        parts.append('</svg>')
        return "\n".join(parts)


# --------------------------------------------------------------------------
# Bar charts
# --------------------------------------------------------------------------


@dataclass
class Bar:
    label: str
    value: float
    highlight: bool = False


@dataclass
class BarChart:
    name: str
    bars: list[Bar]
    ticks: tuple[float, ...]
    label_width: int
    caption: str = ""
    label: str = ""
    decimals: int = 4

    bar_height: int = 26
    bar_gap: int = 18
    pad_top: int = 14
    plot_width: int = 620
    value_gap: int = 12

    def render(self) -> str:
        axis_min, axis_max = self.ticks[0], self.ticks[-1]
        x0 = self.label_width + 14
        plot_width = TARGET_WIDTH - x0 - 74
        width = x0 + plot_width + 74
        rows = len(self.bars)
        plot_h = rows * self.bar_height + (rows - 1) * self.bar_gap
        baseline = self.pad_top + plot_h + 10
        height = baseline + 26 + (22 if self.caption else 0)

        def bx(value: float) -> float:
            span = axis_max - axis_min
            return max(0.0, (value - axis_min) / span) * plot_width

        parts = [
            f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}"'
            f' role="img" aria-label="{esc(self.label)}" xmlns="http://www.w3.org/2000/svg">',
            f'  <g font-family="{FONT}">',
            '    <g stroke="currentColor" opacity="0.16" stroke-width="1">',
            f'      <path d="M{x0} {self.pad_top} V{baseline}"/>',
            f'      <path d="M{x0} {baseline} H{x0 + plot_width}"/>',
            '    </g>',
            f'    <g font-family="{MONO}" font-size="{AXIS_SIZE}" fill="var(--text-muted)"'
            ' text-anchor="middle">',
        ]
        for t in self.ticks:
            parts.append(
                f'      <text x="{x0 + bx(t):.0f}" y="{baseline + 18}">{t:.2f}</text>'
            )
        parts.append('    </g>')

        for i, bar in enumerate(self.bars):
            y = self.pad_top + i * (self.bar_height + self.bar_gap)
            w = bx(bar.value)
            fill = "var(--accent)" if bar.highlight else "var(--text-secondary)"
            opacity = "0.9" if bar.highlight else "0.85"
            parts.append(
                f'    <text x="{self.label_width}" y="{y + self.bar_height / 2 + 4:.0f}"'
                f' font-size="{BODY_SIZE}" text-anchor="end"'
                f' fill="var(--text-primary)">{esc(bar.label)}</text>'
            )
            parts.append(
                f'    <rect x="{x0}" y="{y}" width="{w:.0f}" height="{self.bar_height}"'
                f' rx="3" fill="{fill}" opacity="{opacity}"/>'
            )
            parts.append(
                f'    <text x="{x0 + w + self.value_gap:.0f}"'
                f' y="{y + self.bar_height / 2 + 4:.0f}" font-family="{MONO}"'
                f' font-size="{BODY_SIZE}" font-weight="500"'
                f' fill="var(--text-primary)">{bar.value:.{self.decimals}f}</text>'
            )

        if self.caption:
            parts.append(
                f'    <text x="{x0 + plot_width / 2:.0f}" y="{height - 8}"'
                f' font-size="{BODY_SIZE}" fill="var(--text-muted)"'
                f' text-anchor="middle">{esc(self.caption)}</text>'
            )
        parts += ['  </g>', '</svg>']
        return "\n".join(parts)



# --------------------------------------------------------------------------
# Coverage matrix
# --------------------------------------------------------------------------


@dataclass
class Matrix:
    """A rows-by-columns availability grid. Present, absent, or a plain value."""

    name: str
    columns: tuple[str, ...]
    rows: list[tuple[str, tuple[str, ...]]]
    label: str = ""
    caption: str = ""

    row_label_width: int = 300
    col_width: int = 210
    row_height: int = 44
    pad: int = 12

    def render(self) -> str:
        k = (TARGET_WIDTH - self.pad * 2) / (
            self.row_label_width + self.col_width * len(self.columns))
        row_label_width = round(self.row_label_width * k)
        col_width = round(self.col_width * k)
        width = self.pad * 2 + row_label_width + col_width * len(self.columns)
        header = 40
        height = self.pad * 2 + header + self.row_height * len(self.rows) + (26 if self.caption else 0)
        x0 = self.pad + row_label_width

        parts = [
            f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}"'
            f' role="img" aria-label="{esc(self.label)}" xmlns="http://www.w3.org/2000/svg">',
            f'  <g font-family="{FONT}">',
        ]

        for i, col in enumerate(self.columns):
            cx = x0 + col_width * i + col_width / 2
            parts.append(
                f'    <text x="{cx:.0f}" y="{self.pad + 24}" font-size="{TITLE_SIZE}" font-weight="700"'
                f' text-anchor="middle" fill="var(--text-primary)">{esc(col)}</text>'
            )

        for r, (label, cells) in enumerate(self.rows):
            y = self.pad + header + self.row_height * r
            mid = y + self.row_height / 2 + 4
            parts.append(
                f'    <path d="M{self.pad} {y} H{width - self.pad}" stroke="currentColor"'
                ' stroke-width="1" opacity="0.14" fill="none"/>'
            )
            parts.append(
                f'    <text x="{self.pad}" y="{mid:.0f}" font-size="{BODY_SIZE}"'
                f' fill="var(--text-secondary)">{esc(label)}</text>'
            )
            for c, cell in enumerate(cells):
                cx = x0 + col_width * c + col_width / 2
                if cell == "-":
                    # The one empty cell is the whole argument, so it is marked.
                    parts.append(
                        f'    <text x="{cx:.0f}" y="{mid:.0f}" font-family="{MONO}" font-size="{TITLE_SIZE}"'
                        f' font-weight="700" text-anchor="middle" fill="var(--accent)">none</text>'
                    )
                elif cell == "y":
                    parts.append(
                        f'    <path d="M{cx - 6:.0f} {y + self.row_height / 2:.0f}'
                        f' l4 4 l8 -9" fill="none" stroke="var(--text-secondary)"'
                        ' stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
                    )
                else:
                    parts.append(
                        f'    <text x="{cx:.0f}" y="{mid:.0f}" font-family="{MONO}" font-size="{AXIS_SIZE}"'
                        f' text-anchor="middle" fill="var(--text-primary)">{esc(cell)}</text>'
                    )

        last = self.pad + header + self.row_height * len(self.rows)
        parts.append(
            f'    <path d="M{self.pad} {last} H{width - self.pad}" stroke="currentColor"'
            ' stroke-width="1" opacity="0.14" fill="none"/>'
        )
        if self.caption:
            parts.append(
                f'    <text x="{width / 2:.0f}" y="{height - 8}" font-size="{BODY_SIZE}"'
                f' text-anchor="middle" fill="var(--text-muted)">{esc(self.caption)}</text>'
            )
        parts += ['  </g>', '</svg>']
        return "\n".join(parts)


# --------------------------------------------------------------------------
# The figures
# --------------------------------------------------------------------------

ARCHITECTURE = Flow(
    name="architecture",
    label=(
        "Retrieval pipeline: a query is normalized, fanned out to BM25, dense and "
        "image retrievers in parallel, merged by reciprocal rank fusion, and reordered "
        "by a per-locale LambdaMART model"
    ),
    col_widths=(112, 132, 176, 96, 150),
    nodes=[
        Node("query", "Query", col=0, row=1, accent=True),
        Node("norm", "Normalize", ("NFKC, lowercase",), col=1, row=1, muted=True),
        Node("bm25", "BM25", ("sparse keyword match",), col=2, row=0),
        Node("dense", "bge-m3", ("FAISS HNSW, 1024-dim",), col=2, row=1),
        Node("clip", "CLIP image", ("English only",), col=2, row=2, dashed=True),
        Node("rrf", "RRF", ("fusion",), col=3, row=1, muted=True),
        Node("ltr", "LambdaMART", ("per locale", "top 20 returned"), col=4, row=1, accent=True),
    ],
    edges=[
        ("query", "norm"),
        ("norm", "bm25"),
        ("norm", "dense"),
        ("norm", "clip"),
        ("bm25", "rrf"),
        ("dense", "rrf"),
        ("clip", "rrf"),
        ("rrf", "ltr"),
    ],
)

DEPLOYMENT = Flow(
    name="deployment",
    label=(
        "Two images built from one source repository: a baked image built locally and "
        "deployed to Google Cloud Run, and a lean image built on Hugging Face servers "
        "that pulls its artifacts from a public dataset repository"
    ),
    col_widths=(140, 226, 232),
    col_gap=70,
    row_pitch=150,
    nodes=[
        Node("src", "Source repo", ("two Dockerfiles",), col=0, row=0.55, accent=True),
        Node("art", "mercato-artifacts", ("3.9 GB dataset",), col=0, row=1.55, muted=True),
        Node("baked", "Dockerfile.baked", ("built locally", "port 8000"), col=1, row=0),
        Node("lean", "Dockerfile.lean", ("built by Hugging Face", "port 7860"), col=1, row=1.55),
        Node("run", "Google Cloud Run", ("Tokyo, scales to zero",), col=2, row=0),
        Node("hf", "Hugging Face Space", ("free CPU tier",), col=2, row=1.55),
    ],
    edges=[("src", "baked"), ("src", "lean"), ("baked", "run"), ("lean", "hf")],
    dashed_edges=[("art", "lean")],
    footnote="Two images. Where the build runs decides where the data comes from.",
)

RETRIEVAL = BarChart(
    name="retrieval-comparison",
    label=(
        "NDCG at 10 for five English retrieval configurations, from 0.3898 for dense "
        "alone to 0.4821 for three-way fusion"
    ),
    label_width=132,
    ticks=(0.0, 0.15, 0.30, 0.45, 0.60),
    caption="English retrieval, NDCG@10 on the full corpus",
    bars=[
        Bar("Dense only", 0.3898),
        Bar("BM25 only", 0.4019),
        Bar("RRF hybrid", 0.4545),
        Bar("Weighted hybrid", 0.4563),
        Bar("Three-way RRF", 0.4821, highlight=True),
    ],
)

LONGTAIL = BarChart(
    name="longtail",
    label=(
        "NDCG at 10 of 0.5148 on richly judged queries against 0.4131 on the sparsest "
        "bucket"
    ),
    label_width=150,
    ticks=(0.0, 0.15, 0.30, 0.45, 0.60),
    caption="Weighted fusion, NDCG@10 by judgment density",
    bars=[
        Bar("Richly judged", 0.5148),
        Bar("Sparsest bucket", 0.4131, highlight=True),
    ],
)


COVERAGE = Matrix(
    name="esci-coverage",
    label=(
        "Coverage matrix comparing English and Japanese locales across queries, products, "
        "judgments, text index and image vectors. Japanese has more of everything except "
        "image vectors, which do not exist."
    ),
    columns=("English", "Japanese"),
    rows=[
        ("Queries", ("8,956", "10,407")),
        ("Products", ("164,900", "233,850")),
        ("Graded judgments", ("181,701", "297,883")),
        ("Text index", ("y", "y")),
        ("Public image vectors", ("y", "-")),
    ],
    caption="Japanese carries more of everything except the one thing that cannot be bought",
)

CHANNEL_COST = BarChart(
    name="esci-channel-cost",
    label=(
        "NDCG at 10 for English two-way fusion at 0.4545 against three-way fusion at 0.4821, "
        "a gain of 0.0276 from adding the image channel"
    ),
    label_width=170,
    ticks=(0.0, 0.15, 0.30, 0.45, 0.60),
    caption="English NDCG@10. The image channel is the largest single gain in the system.",
    bars=[
        Bar("Text only (2-way RRF)", 0.4545),
        Bar("With images (3-way)", 0.4821, highlight=True),
    ],
)

RERANKER_FEATURES = BarChart(
    name="esci-reranker-features",
    label="Reranker feature counts: ten for English, eight for Japanese",
    label_width=110,
    ticks=(0, 2, 4, 6, 8, 10),
    caption="Ranking features available per locale",
    decimals=0,
    bars=[
        Bar("English", 10),
        Bar("Japanese", 8, highlight=True),
    ],
)

DISTRIBUTION = Flow(
    name="esci-distribution",
    label=(
        "Distribution model: a source image is encoded to a CLIP vector, which is published "
        "with a reference back to the original. The image itself is never redistributed."
    ),
    col_widths=(168, 168, 200),
    col_gap=64,
    row_pitch=118,
    nodes=[
        Node("img", "Source image", ("stays with its owner",), col=0, row=0, dashed=True),
        Node("clip", "CLIP encoder", ("same space as Mercato",), col=1, row=0, muted=True),
        Node("rec", "Vector + reference", ("no pixels redistributed",), col=2, row=0, accent=True),
    ],
    edges=[("img", "clip"), ("clip", "rec")],
    footnote="Embeddings and references travel. Images do not.",
)

# --- Round Wall -----------------------------------------------------------
# Source: C_3_0_SHA256_Round_Wall.ipynb (MLP, seeds 0 and 1) unless noted.

RW_WALL = BarChart(
    name="rw-wall",
    label=(
        "Lift over the majority baseline by round. Rounds 1 to 4 show 0.078 to 0.096. "
        "From round 5 to round 16 lift sits at or below 0.0004, inside the noise margin."
    ),
    label_width=120,
    ticks=(0.0, 0.025, 0.05, 0.075, 0.10),
    caption="MLP lift over majority baseline. Dashed marker at 0.0008 is the 95% noise margin.",
    decimals=4,
    bars=[
        Bar("round 1", 0.0784), Bar("round 2", 0.0846),
        Bar("round 3", 0.0929), Bar("round 4", 0.0964, highlight=True),
        Bar("round 5", 0.0004), Bar("round 6", 0.0004),
        Bar("round 8", 0.0000), Bar("round 12", 0.0004),
        Bar("round 16", 0.0000),
    ],
)

RW_LEARNERS = Matrix(
    name="rw-learners",
    label=(
        "Per-round results for a linear probe and an MLP. Both collapse at round five, "
        "so the null result is not a capacity artifact."
    ),
    columns=("Linear probe", "MLP", "Seed spread"),
    row_label_width=200,
    col_width=170,
    rows=[
        ("Round 1", ("+0.0660", "+0.0784", "0.0007")),
        ("Round 2", ("+0.0660", "+0.0846", "0.0003")),
        ("Round 3", ("+0.0659", "+0.0929", "0.0001")),
        ("Round 4", ("+0.0658", "+0.0964", "0.0021")),
        ("Round 5", ("+0.0001", "+0.0004", "0.0002")),
        ("Round 6", ("+0.0002", "+0.0004", "0.0002")),
        ("Round 16", ("-0.0002", "-0.0002", "0.0001")),
    ],
    caption="Lift over baseline. Noise margin is 0.0008 on 1,536,000 bit-predictions per round.",
)

RW_REPRO = Matrix(
    name="rw-repro",
    label=(
        "Lift at round four and round five across four independent runs. The round-four "
        "value varies with setup; the round-five collapse does not."
    ),
    columns=("Round 4 lift", "Round 5 lift"),
    row_label_width=290,
    col_width=210,
    rows=[
        ("Round Wall sweep", ("+0.0964", "+0.0004")),
        ("Phase 3 MLP, run 1", ("+0.0893", "+0.0001")),
        ("Phase 3 MLP, run 2", ("+0.0677", "+0.0003")),
        ("Blueprint, bootstrapped", ("+0.0510", "+0.0002")),
    ],
    caption="Four configurations disagree on the size of the signal and agree on where it ends.",
)

RW_SPECK = BarChart(
    name="rw-speck",
    label=(
        "Speck32/64 distinguisher accuracy by round: 0.7742 at five rounds falling to "
        "0.5044 at eight rounds, against a 0.5 no-signal floor."
    ),
    label_width=150,
    ticks=(0.5, 0.6, 0.7, 0.8),
    caption="Speck32/64 distinguisher accuracy. 0.50 is no signal.",
    decimals=4,
    bars=[
        Bar("5 rounds", 0.7742, highlight=True), Bar("6 rounds", 0.5742),
        Bar("7 rounds", 0.4972), Bar("8 rounds", 0.5044),
    ],
)

# --- Kavel / Sign language / Symbolic regression --------------------------

KAVEL_PIPE = Flow(
    name="kv-pipeline",
    label=(
        "Intended Kavel pipeline: a seller photo is encoded, matched against comparable "
        "listings, and the retrieved comparables ground a generated title, description "
        "and attribute set."
    ),
    col_widths=(150, 150, 170, 170),
    col_gap=60,
    row_pitch=130,
    nodes=[
        Node("photo", "Seller photo", ("one image, no text",), col=0, row=0, dashed=True),
        Node("enc", "Vision encoder", ("image embedding",), col=1, row=0, muted=True),
        Node("ret", "Retrieve comparables", ("nearest sold listings",), col=2, row=0),
        Node("gen", "Grounded generation", ("title, description,", "attributes"), col=3, row=0, accent=True),
    ],
    edges=[("photo", "enc"), ("enc", "ret"), ("ret", "gen")],
    footnote="Retrieval first, generation second. The comparables are what keep the copy honest.",
)

SL_PIPE = Flow(
    name="sl-pipeline",
    label=(
        "Sign language pipeline: webcam frame, fixed region of interest, running-average "
        "background subtraction, threshold, largest contour, then a CNN over the 64 by 64 "
        "binary mask."
    ),
    col_widths=(140, 150, 170, 160),
    col_gap=56,
    row_pitch=130,
    nodes=[
        Node("cam", "Webcam frame", ("flipped, 1 ROI",), col=0, row=0, muted=True),
        Node("bg", "Background model", ("running average", "over 60 frames"), col=1, row=0),
        Node("seg", "Segment hand", ("abs-diff, threshold 25,", "largest contour"), col=2, row=0),
        Node("cnn", "CNN", ("64x64 mask,", "10 classes"), col=3, row=0, accent=True),
    ],
    edges=[("cam", "bg"), ("bg", "seg"), ("seg", "cnn")],
    footnote="The hand is never detected. It is whatever moved after the background settled.",
)

SR_PIPE = Flow(
    name="sr-pipeline",
    label=(
        "Symbolic regression approach: numeric data is encoded, a transformer proposes "
        "candidate expressions, and each candidate is scored by fitting its constants "
        "against the data."
    ),
    col_widths=(150, 170, 170, 150),
    col_gap=60,
    row_pitch=130,
    nodes=[
        Node("data", "(x, y) samples", ("real or synthetic",), col=0, row=0, muted=True),
        Node("enc", "Set encoder", ("permutation invariant",), col=1, row=0),
        Node("dec", "Transformer decoder", ("emits expression", "as a token sequence"), col=2, row=0),
        Node("fit", "Fit and score", ("constants by least", "squares"), col=3, row=0, accent=True),
    ],
    edges=[("data", "enc"), ("enc", "dec"), ("dec", "fit")],
    footnote="The model proposes a shape. Numerical fitting decides whether the shape was right.",
)

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for fig in (ARCHITECTURE, DEPLOYMENT, RETRIEVAL, LONGTAIL,
                COVERAGE, CHANNEL_COST, RERANKER_FEATURES, DISTRIBUTION,
                RW_WALL, RW_LEARNERS, RW_REPRO, RW_SPECK,
                KAVEL_PIPE, SL_PIPE, SR_PIPE):
        path = OUT / f"{fig.name}.svg"
        path.write_text(fig.render() + "\n", encoding="utf-8")
        print(f"{path.relative_to(OUT.parent.parent)}  {path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
