"""Generate the SVG figures used in the Mercato write-up.

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

FONT = "Sora, sans-serif"
MONO = "JetBrains Mono, monospace"

TITLE_SIZE = 13.5
BODY_SIZE = 11.5
AXIS_SIZE = 11


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

    def col_x(self, col: int) -> int:
        x = self.pad_x
        for i in range(col):
            x += self.col_widths[i] + self.col_gap
        return x

    def geometry(self) -> dict[str, tuple[int, float, int, int]]:
        """key -> (x, y, w, h), y being the box top."""
        out = {}
        for n in self.nodes:
            w = self.col_widths[n.col]
            h = self.box_height(n)
            cy = self.pad_y + n.row * self.row_pitch + self.row_pitch / 2
            out[n.key] = (self.col_x(n.col), cy - h / 2, w, h)
        return out

    def render(self) -> str:
        geo = self.geometry()
        rows = max(n.row for n in self.nodes) + 1
        width = self.col_x(len(self.col_widths) - 1) + self.col_widths[-1] + self.pad_x
        height = int(self.pad_y * 2 + rows * self.row_pitch) + (34 if self.footnote else 0)

        parts = [
            f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(self.label)}"'
            ' xmlns="http://www.w3.org/2000/svg">',
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
                f'    <text x="{width / 2:.0f}" y="{height - 12}" font-size="12"'
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
    plot_width: int = 470
    value_gap: int = 12

    def render(self) -> str:
        axis_max = self.ticks[-1]
        x0 = self.label_width + 14
        width = x0 + self.plot_width + 74
        rows = len(self.bars)
        plot_h = rows * self.bar_height + (rows - 1) * self.bar_gap
        baseline = self.pad_top + plot_h + 10
        height = baseline + 26 + (22 if self.caption else 0)

        def bx(value: float) -> float:
            return value / axis_max * self.plot_width

        parts = [
            f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(self.label)}"'
            ' xmlns="http://www.w3.org/2000/svg">',
            f'  <g font-family="{FONT}">',
            '    <g stroke="currentColor" opacity="0.16" stroke-width="1">',
            f'      <path d="M{x0} {self.pad_top} V{baseline}"/>',
            f'      <path d="M{x0} {baseline} H{x0 + self.plot_width}"/>',
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
                f' font-size="12.5" text-anchor="end"'
                f' fill="var(--text-primary)">{esc(bar.label)}</text>'
            )
            parts.append(
                f'    <rect x="{x0}" y="{y}" width="{w:.0f}" height="{self.bar_height}"'
                f' rx="3" fill="{fill}" opacity="{opacity}"/>'
            )
            parts.append(
                f'    <text x="{x0 + w + self.value_gap:.0f}"'
                f' y="{y + self.bar_height / 2 + 4:.0f}" font-family="{MONO}"'
                f' font-size="11.5" font-weight="500"'
                f' fill="var(--text-primary)">{bar.value:.{self.decimals}f}</text>'
            )

        if self.caption:
            parts.append(
                f'    <text x="{x0 + self.plot_width / 2:.0f}" y="{height - 8}"'
                f' font-size="11.5" fill="var(--text-muted)"'
                f' text-anchor="middle">{esc(self.caption)}</text>'
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


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for fig in (ARCHITECTURE, DEPLOYMENT, RETRIEVAL, LONGTAIL):
        path = OUT / f"{fig.name}.svg"
        path.write_text(fig.render() + "\n", encoding="utf-8")
        print(f"{path.relative_to(OUT.parent.parent)}  {path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
