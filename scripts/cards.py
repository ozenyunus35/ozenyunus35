"""Render the animated SVG cards of the profile README.

Every card shares one visual language: a dark panel with a dot grid, a violet
to cyan accent and mono captions. The open-source card reads the GitHub API,
so it follows new merges. Run with GITHUB_TOKEN set; the workflow does it once
a day.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import random
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path

USER = "ozenyunus35"
# Organisations I work for: their repositories are a job, not a contribution.
EXCLUDED_OWNERS = {USER.lower(), "intellium-academy", "codify-soft"}

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"

# ---------------------------------------------------------------- content

NAME = "Yunus Ozen"
POSITIONING = "AI Product Engineer"
TAGLINE = ("I build AI-powered software products end to end,", "from the idea to production.")
LOCATION = "İzmir, Türkiye"
PILLARS = [
    ("spark", "AI", "LLM apps · agents · automation"),
    ("target", "Product", "strategy · requirements · UX"),
    ("code", "Engineering", "web · mobile · backend"),
]
@dataclass(frozen=True)
class Product:
    key: str
    name: str
    kind: str
    period: str
    summary: tuple[str, str]
    roles: tuple[str, ...]
    stack: tuple[str, ...]
    mockup: str
    file: str
    link: str = ""


# Selected work shows the first FEATURED products of profile.json, best first.
FEATURED = 4


def load_products(path: Path) -> list[Product]:
    data = json.loads(path.read_text(encoding="utf-8"))["products"]
    return [Product(p["key"], p["name"], p["kind"], p["period"], tuple(p["summary"]), tuple(p["roles"]),
                    tuple(p["stack"]), p["mockup"], p["file"], p.get("link", "")) for p in data]


TOOLBOX = [
    ("Product & design", ["figma"], ["Requirements", "User flows", "Agile"]),
    ("Frontend & mobile", ["ts", "react", "nextjs", "flutter"], []),
    ("Backend & data", ["nodejs", "dotnet", "postgres"], ["REST APIs"]),
    ("Languages & tools", ["rust", "go", "python", "git"], []),
]
ICON_NAMES = {
    "figma": "Figma", "ts": "TypeScript", "react": "React", "nextjs": "Next.js",
    "flutter": "Flutter", "nodejs": "Node.js", "dotnet": ".NET", "postgres": "PostgreSQL",
    "rust": "Rust", "go": "Go", "python": "Python", "git": "Git",
}

# ---------------------------------------------------------------- style

P = dict(bg="#0b0d12", panel="#11141b", raised="#161a23", line="#232733", fg="#e6e8ee", muted="#8a90a0",
         dim="#4b5263", off="#1a1e28", violet="#8b5cf6", cyan="#22d3ee", gold="#fbbf24")

CSS = (
    f".s{{font-family:{SANS}}}.m{{font-family:{MONO}}}"
    ".in{animation:in .8s cubic-bezier(.2,.7,.2,1) backwards}"
    "@keyframes in{from{opacity:0;transform:translateY(8px)}}"
    ".tw{animation:tw 3.5s ease-in-out infinite}@keyframes tw{0%,100%{opacity:.15}50%{opacity:1}}"
    ".blink{animation:blink 1.4s steps(1) infinite}@keyframes blink{50%{opacity:.2}}"
    ".grow{transform-box:fill-box;transform-origin:bottom;animation:grow 1.2s cubic-bezier(.2,.7,.2,1) backwards}"
    "@keyframes grow{from{transform:scaleY(0)}}"
    ".growx{transform-box:fill-box;transform-origin:left;animation:growx 1.2s cubic-bezier(.2,.7,.2,1) backwards}"
    "@keyframes growx{from{transform:scaleX(0)}}"
    ".led{animation:led .3s ease backwards}@keyframes led{from{opacity:0}}"
    ".pulse{animation:pulse 1.6s ease-in-out infinite}@keyframes pulse{50%{opacity:.35}}"
    ".spin{animation:spin 18s linear infinite}.spinr{animation:spin 30s linear infinite reverse}"
    "@keyframes spin{to{transform:rotate(360deg)}}"
    ".draw{animation:draw 2s cubic-bezier(.4,0,.2,1) backwards .3s}"
    "@keyframes draw{from{stroke-dashoffset:var(--len)}}"
    ".fade{animation:fade 1.2s ease backwards 1.4s}@keyframes fade{from{opacity:0}}"
    ".cur{animation:blink 1s steps(1) infinite}"
)


def mix(t: float) -> str:
    """A colour on the violet to cyan accent, t from 0 to 1."""
    a, b = P["violet"], P["cyan"]
    rgb = [round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t) for i in (1, 3, 5)]
    return "#" + "".join(f"{v:02x}" for v in rgb)


class Card:
    """One SVG card: background, dot grid, glow and border."""

    def __init__(self, w: int, h: int, label: str, css: str = "") -> None:
        self.w, self.h = w, h
        self.parts: list[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}">',
            f"<style>{CSS}{css}</style>",
            self._defs(),
            f'<g clip-path="url(#card)"><rect width="{w}" height="{h}" fill="{P["bg"]}"/>'
            f'<rect width="{w}" height="{h}" fill="url(#dots)"/>'
            f'<ellipse cx="{w}" cy="0" rx="{w * .45:.0f}" ry="{h * .9:.0f}" fill="url(#glow)"/>'
            f'<ellipse cx="0" cy="{h}" rx="{w * .3:.0f}" ry="{h * .6:.0f}" fill="url(#glow2)"/></g>',
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="16" fill="none" stroke="{P["line"]}"/>',
            f'<rect x="{w * .08:.0f}" y="0" width="{w * .5:.0f}" height="1.2" fill="url(#hair)"/>',
        ]

    def _defs(self) -> str:
        return (
            "<defs>"
            f'<linearGradient id="acc" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{P["violet"]}"/>'
            f'<stop offset="1" stop-color="{P["cyan"]}"/></linearGradient>'
            f'<linearGradient id="hair" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{P["violet"]}" '
            f'stop-opacity="0"/><stop offset=".45" stop-color="{P["violet"]}"/><stop offset=".7" '
            f'stop-color="{P["cyan"]}"/><stop offset="1" stop-color="{P["cyan"]}" stop-opacity="0"/></linearGradient>'
            f'<linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{P["violet"]}" '
            f'stop-opacity=".35"/><stop offset="1" stop-color="{P["violet"]}" stop-opacity="0"/></linearGradient>'
            f'<radialGradient id="glow"><stop offset="0" stop-color="{P["violet"]}" stop-opacity=".16"/>'
            f'<stop offset="1" stop-color="{P["violet"]}" stop-opacity="0"/></radialGradient>'
            f'<radialGradient id="glow2"><stop offset="0" stop-color="{P["cyan"]}" stop-opacity=".07"/>'
            f'<stop offset="1" stop-color="{P["cyan"]}" stop-opacity="0"/></radialGradient>'
            '<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
            '<circle cx="1" cy="1" r=".9" fill="#ffffff" fill-opacity=".045"/></pattern>'
            '<filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="8"/></filter>'
            f'<clipPath id="card"><rect width="{self.w}" height="{self.h}" rx="16"/></clipPath>'
            "</defs>"
        )

    def add(self, *parts: str) -> None:
        self.parts.extend(parts)

    def label(self, x: float, y: float, text: str, size: int = 13, fill: str | None = None,
              anchor: str = "start", delay: float | None = None) -> None:
        cls = "m in" if delay is not None else "m"
        style = f' style="animation-delay:{delay}s"' if delay is not None else ""
        self.add(f'<text class="{cls}" x="{x}" y="{y}" font-size="{size}" fill="{fill or P["muted"]}" '
                 f'letter-spacing=".5" text-anchor="{anchor}"{style}>{escape(text)}</text>')

    def header(self, title: str, meta: str = "", live: bool = False) -> None:
        """The caption row every card starts with."""
        self.label(48, 52, f"// {title}")
        if meta:
            dot = f'<tspan class="blink" fill="{P["cyan"]}"> ●</tspan>' if live else ""
            self.add(f'<text class="m" x="{self.w - 48}" y="52" font-size="12" letter-spacing=".5" '
                     f'text-anchor="end" fill="{P["dim"]}">{escape(meta)}{dot}</text>')

    def svg(self) -> str:
        return "".join(self.parts) + "</svg>"


def window(c: Card, x: float, y: float, w: float, h: float, title: str) -> None:
    """An editor or browser window: the frame every mockup sits in."""
    c.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{P["panel"]}" stroke="{P["line"]}"/>',
          f'<line x1="{x}" y1="{y + 30}" x2="{x + w}" y2="{y + 30}" stroke="{P["line"]}"/>')
    for i, color in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        c.add(f'<circle cx="{x + 18 + i * 15}" cy="{y + 15}" r="4.5" fill="{color}" fill-opacity=".75"/>')
    c.label(x + w / 2, y + 19, title, 11, P["dim"], "middle")


def _k(n: int) -> str:
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def _width(text: str, size: float, mono: bool = False) -> float:
    return len(text) * size * (0.61 if mono else 0.55)


GLYPHS = {
    "trophy": "M5 2h6v4a3 3 0 0 1-6 0zM5 3H2.5C2.5 5 3.5 6 5 6M11 3h2.5c0 2-1 3-2.5 3M8 9v3M5 14h6",
    "layers": "M8 2l6 3-6 3-6-3zM2 8.5l6 3 6-3M2 11.5l6 3 6-3",
    "merge": "M4 5v9M4 6c0 4 8 3 8 6",
    "user": "M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM2.5 14.5c.8-3 3-4.5 5.5-4.5s4.7 1.5 5.5 4.5",
    "briefcase": "M2 5h12v8H2zM6 5V3h4v2M2 9h12",
    "code": "M5 4L1 8l4 4M11 4l4 4-4 4M9.5 2.5l-3 11",
    "target": "M8 14.5A6.5 6.5 0 1 0 8 1.5a6.5 6.5 0 0 0 0 13zM8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM8 8.01V8",
    "spark": "M8 1.5l1.6 4.9 4.9 1.6-4.9 1.6L8 14.5 6.4 9.6 1.5 8l4.9-1.6zM13 1.5v3M11.5 3h3",
}


def glyph(c: Card, name: str, x: float, y: float, color: str, scale: float = 1) -> None:
    """A 16 px line icon with its top left corner at (x, y)."""
    c.add(f'<g transform="translate({x} {y}) scale({scale})" fill="none" stroke="{color}" stroke-width="1.6" '
          f'stroke-linecap="round" stroke-linejoin="round"><path d="{GLYPHS[name]}"/>')
    if name == "merge":
        c.add('<circle cx="4" cy="3" r="2"/><circle cx="12" cy="13.5" r="2"/>')
    c.add("</g>")


# ---------------------------------------------------------------- data


def _request(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": "profile-cards"})
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read(), resp.headers.get_content_type()


def _get(url: str) -> dict:
    return json.loads(_request(url)[0])


@dataclass(frozen=True)
class PR:
    repo: str
    number: int
    title: str
    closed: datetime


def merged_prs() -> list[PR]:
    """Every merged public PR outside my own and my employers' repos, newest first."""
    query = f"author:{USER} type:pr is:merged is:public"
    prs = []
    for page in range(1, 11):
        params = urllib.parse.urlencode({"q": query, "per_page": 100, "page": page})
        items = _get(f"https://api.github.com/search/issues?{params}")["items"]
        for item in items:
            repo = item["repository_url"].removeprefix("https://api.github.com/repos/")
            if repo.split("/")[0].lower() not in EXCLUDED_OWNERS:
                closed = datetime.fromisoformat(item["closed_at"].replace("Z", "+00:00"))
                prs.append(PR(repo, item["number"], item["title"], closed))
        if len(items) < 100:
            break
    return sorted(prs, key=lambda pr: pr.closed, reverse=True)


def avatar(owner: str) -> str:
    """The owner's avatar as a data URI, so the card needs no network."""
    image, mime = _request(f"https://github.com/{owner}.png?size=64")
    return f"data:{mime};base64," + base64.b64encode(image).decode()


def icons() -> dict[str, str]:
    out = {}
    for key in ICON_NAMES:
        data, _ = _request(f"https://skillicons.dev/icons?i={key}")
        out[key] = "data:image/svg+xml;base64," + base64.b64encode(data).decode()
    return out


# ---------------------------------------------------------------- hero


def hero(products: int) -> str:
    """The first card: who I am, what I work on and the proof, with the network on the right."""
    css = (".node{animation:node 3s ease-in-out infinite}@keyframes node{0%,100%{opacity:.55}50%{opacity:1}}"
           ".ring{transform-box:fill-box;transform-origin:center;animation:ring 2.4s ease-out infinite}"
           "@keyframes ring{from{transform:scale(.6);opacity:.8}to{transform:scale(2.2);opacity:0}}")
    c = Card(1200, 560, f"{NAME}, {POSITIONING}: AI, product and engineering", css)

    # the network: what goes in on the left becomes a product on the right
    rnd = random.Random(5)
    inputs = [("users", "user", 118), ("business", "briefcase", 188), ("code", "code", 258)]
    layers = [(830, 5, 48), (930, 6, 44), (1020, 5, 48)]
    hidden = [[(x, 200 + (i - (n - 1) / 2) * gap) for i in range(n)] for x, n, gap in layers]
    ox, oy = 1112, 200
    ports = [(752, cy) for _, _, cy in inputs]
    columns = [ports] + hidden + [[(ox, oy)]]
    c.add(f'<circle cx="{ox}" cy="{oy}" r="56" fill="{P["violet"]}" opacity=".35" filter="url(#blur)"/>',
          f'<circle cx="930" cy="200" r="120" fill="{P["violet"]}" opacity=".06" filter="url(#blur)"/>')
    for a, b in zip(columns, columns[1:]):
        for x1, y1 in a:
            for x2, y2 in b:
                mx = (x1 + x2) / 2
                c.add(f'<path d="M{x1} {y1:.0f} C{mx:.0f} {y1:.0f} {mx:.0f} {y2:.0f} {x2} {y2:.0f}" fill="none" '
                      'stroke="#252a38" stroke-width="1"/>')
    for k in range(18):
        chain = [rnd.choice(col) for col in columns]
        d = f"M{chain[0][0]} {chain[0][1]:.0f}"
        for (x1, y1), (x2, y2) in zip(chain, chain[1:]):
            mx = (x1 + x2) / 2
            d += f" C{mx:.0f} {y1:.0f} {mx:.0f} {y2:.0f} {x2} {y2:.0f}"
        dur, begin = rnd.uniform(2.6, 3.6), k * 0.3
        color = mix(rnd.random())
        c.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" '
              f'stroke-dasharray="26 600" stroke-dashoffset="26" opacity=".85">'
              f'<animate attributeName="stroke-dashoffset" values="26;-560" dur="{dur:.1f}s" begin="{begin:.2f}s" '
              'repeatCount="indefinite"/></path>')
    for li, col in enumerate(hidden):
        for ni, (x, y) in enumerate(col):
            t = (li + ni / len(col)) / 3
            c.add(f'<circle cx="{x}" cy="{y:.0f}" r="8" fill="{P["panel"]}" stroke="{mix(t)}" stroke-width="2"/>',
                  f'<circle cx="{x}" cy="{y:.0f}" r="3.5" fill="{mix(t)}" opacity=".2"><animate attributeName="opacity" '
                  f'values=".15;1;.15" dur="{rnd.uniform(1.8, 3):.1f}s" begin="{rnd.uniform(0, 2):.1f}s" '
                  'repeatCount="indefinite"/></circle>')
    for (text, icon, cy), (px_, py_) in zip(inputs, ports):
        c.add(f'<g class="in" style="animation-delay:.3s"><rect x="634" y="{cy - 19}" width="118" height="38" rx="19" '
              f'fill="{P["panel"]}" stroke="{P["line"]}"/>'
              f'<circle cx="{px_}" cy="{py_}" r="4" fill="{P["bg"]}" stroke="{P["violet"]}" stroke-width="2"/></g>')
        glyph(c, icon, 650, cy - 8, P["violet"])
        c.add(f'<text class="m" x="676" y="{cy + 4.5}" font-size="13" fill="{P["fg"]}">{text}</text>')
    c.add(f'<g class="spin" style="transform-origin:{ox}px {oy}px"><circle cx="{ox}" cy="{oy}" r="38" fill="none" '
          f'stroke="url(#acc)" stroke-width="1.5" stroke-dasharray="4 8"/></g>',
          f'<circle class="ring" cx="{ox}" cy="{oy}" r="26" fill="none" stroke="{P["cyan"]}"/>',
          f'<circle cx="{ox}" cy="{oy}" r="26" fill="{P["raised"]}" stroke="url(#acc)" stroke-width="2.5"/>')
    glyph(c, "layers", ox - 8, oy - 8.5, P["cyan"])
    c.add(f'<text class="m" x="{ox}" y="{oy + 62}" font-size="13" fill="{P["cyan"]}" text-anchor="middle">product</text>')

    # who I am: the first thing a visitor reads
    c.add(f'<text class="m in" x="64" y="72" font-size="15" fill="{P["cyan"]}">~ $ whoami'
          '<tspan class="cur"> ▍</tspan></text>')
    chip_w = _width(LOCATION, 12, True) + 40
    c.add(f'<g class="in"><rect x="{1136 - chip_w:.0f}" y="40" width="{chip_w:.0f}" height="26" rx="13" '
          f'fill="{P["panel"]}" stroke="{P["line"]}"/>'
          f'<circle cx="{1136 - chip_w + 16:.0f}" cy="53" r="3.5" fill="none" stroke="{P["cyan"]}" stroke-width="1.5"/>'
          f'<text class="m" x="{1136 - chip_w + 28:.0f}" y="57" font-size="12" fill="{P["muted"]}">'
          f"{escape(LOCATION)}</text></g>")
    c.add(f'<text class="s in" x="61" y="146" font-size="68" font-weight="700" letter-spacing="-2" '
          f'fill="{P["fg"]}">{NAME}</text>',
          f'<text class="s in" x="64" y="190" font-size="26" font-weight="600" fill="url(#acc)" '
          f'style="animation-delay:.15s">{POSITIONING}</text>')
    for i, line in enumerate(TAGLINE):
        c.add(f'<text class="s in" x="64" y="{226 + i * 26}" font-size="18" fill="{P["muted"]}" '
              f'style="animation-delay:{0.3 + i * 0.08:.2f}s">{escape(line)}</text>')

    gap, y = 16, 344
    w = (1072 - 2 * gap) / 3
    for i, (icon, title, desc) in enumerate(PILLARS):
        bx = 64 + i * (w + gap)
        color = mix(i / 2)
        c.add(f'<g class="in" style="animation-delay:{0.45 + i * 0.12:.2f}s">'
              f'<rect x="{bx:.0f}" y="{y}" width="{w:.0f}" height="88" rx="14" fill="{P["panel"]}" '
              f'fill-opacity=".92" stroke="{P["line"]}"/>'
              f'<rect x="{bx + 24:.0f}" y="{y}" width="{w - 48:.0f}" height="1.5" fill="url(#hair)"/>'
              f'<rect x="{bx + 20:.0f}" y="{y + 20}" width="48" height="48" rx="12" fill="{color}" '
              f'fill-opacity=".1" stroke="{color}" stroke-opacity=".55"/>')
        glyph(c, icon, bx + 32, y + 32, color, 1.5)
        c.add(f'<text class="s" x="{bx + 86:.0f}" y="{y + 41}" font-size="19" font-weight="600" '
              f'fill="{P["fg"]}">{title}</text>'
              f'<text class="m" x="{bx + 86:.0f}" y="{y + 63}" font-size="12.5" fill="{P["muted"]}">'
              f"{escape(desc)}</text></g>")

    c.add(f'<line x1="64" y1="{y + 124}" x2="1136" y2="{y + 124}" stroke="{P["line"]}"/>')
    proof = [("trophy", "1st place", "NASA Space Apps 2022"),
             ("layers", f"{products} products", "built and shipped"),
             ("code", "Full-stack", "React · TypeScript · Node.js · Flutter")]
    x, py = 64, y + 166
    for i, (icon, strong, rest) in enumerate(proof):
        color = P["gold"] if i == 0 else P["fg"]
        c.add(f'<g class="in" style="animation-delay:{0.8 + i * 0.1:.1f}s">')
        glyph(c, icon, x, py - 13, P["gold"] if i == 0 else P["cyan"])
        c.add(f'<text class="s" x="{x + 26}" y="{py}" font-size="16"><tspan font-weight="600" fill="{color}">'
              f'{strong}</tspan><tspan fill="{P["muted"]}">  {escape(rest)}</tspan></text></g>')
        x += 26 + _width(strong, 16) + _width(rest, 16) + 52
    return c.svg()


# ---------------------------------------------------------------- products


def _steps(n: int, dur: float, i: int, off: str, on: str, attr: str = "fill") -> str:
    """A SMIL animation that switches a step on at its turn of an n-step loop."""
    t = i / n
    return (f'<animate attributeName="{attr}" values="{off};{on};{on}" keyTimes="0;{t:.3f};1" calcMode="discrete" '
            f'dur="{dur}s" repeatCount="indefinite"/>')


def _mock_route(c: Card, x: float, y: float, w: float, h: float) -> None:
    """Bi-Sevk: a tracked load crosses the city while its shipment card moves through the steps."""
    mw, dur, arrive = 316, 7, 0.82
    timing = f'dur="{dur}s" repeatCount="indefinite"'
    c.add(f'<defs><clipPath id="map"><rect x="{x}" y="{y}" width="{mw}" height="{h}" rx="8"/></clipPath>'
          f'<filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3"/></filter>'
          '</defs>',
          f'<g clip-path="url(#map)"><rect x="{x}" y="{y}" width="{mw}" height="{h}" fill="#0e1118"/>')
    # city blocks with the streets between them, and a river
    for col in range(9):
        for row in range(5):
            bw = 30 if (col + row) % 3 else 22
            c.add(f'<rect x="{x + 6 + col * 36}" y="{y + 6 + row * 30}" width="{bw}" height="22" rx="3" '
                  f'fill="#151a25"/>')
    c.add(f'<path d="M{x + 196} {y - 6} C{x + 186} {y + 40} {x + 236} {y + 80} {x + 220} {y + h + 6}" fill="none" '
          f'stroke="{P["cyan"]}" stroke-opacity=".08" stroke-width="16"/>')
    ax, ay, bx, by = x + 40, y + h - 26, x + mw - 50, y + 42
    route = (f"M{ax} {ay} H{ax + 68} C{ax + 98} {ay} {ax + 104} {ay - 14} {ax + 104} {ay - 30} "
             f"V{by + 40} C{ax + 104} {by + 20} {ax + 120} {by + 14} {ax + 140} {by + 14} H{bx - 10} "
             f"C{bx - 4} {by + 14} {bx} {by + 8} {bx} {by}")
    travel = (f'values="100;0;0" keyTimes="0;{arrive};1" {timing}')
    c.add(f'<path d="{route}" fill="none" stroke="{P["dim"]}" stroke-width="2" stroke-dasharray="2 5" '
          'stroke-linecap="round"/>',
          f'<path d="{route}" pathLength="100" fill="none" stroke="{P["violet"]}" stroke-width="8" '
          f'stroke-dasharray="100" filter="url(#soft)" opacity=".7">'
          f'<animate attributeName="stroke-dashoffset" {travel}/></path>',
          f'<path d="{route}" pathLength="100" fill="none" stroke="url(#acc)" stroke-width="3.5" '
          f'stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="100">'
          f'<animate attributeName="stroke-dashoffset" {travel}/></path>')
    # pickup and drop-off
    c.add(f'<circle cx="{ax}" cy="{ay}" r="9" fill="{P["violet"]}" fill-opacity=".2"/>',
          f'<circle cx="{ax}" cy="{ay}" r="5" fill="{P["bg"]}" stroke="{P["violet"]}" stroke-width="2.5"/>',
          f'<circle cx="{bx}" cy="{by}" r="6" fill="none" stroke="{P["gold"]}">'
          f'<animate attributeName="r" values="6;18" dur="1.8s" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" values=".9;0" dur="1.8s" repeatCount="indefinite"/></circle>',
          f'<path d="M{bx} {by} c-6 -7 -9 -11 -9 -15.5 a9 9 0 0 1 18 0 c0 4.5 -3 8.5 -9 15.5z" fill="{P["gold"]}"/>',
          f'<circle cx="{bx}" cy="{by - 15.5}" r="3.2" fill="{P["bg"]}"/>')
    # the tracked vehicle with its live chip
    c.add(f'<g><animateMotion path="{route}" keyPoints="0;1;1" keyTimes="0;{arrive};1" calcMode="linear" {timing}/>'
          f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;{arrive - .02};{arrive + .03};1" {timing}/>'
          f'<circle r="10" fill="{P["cyan"]}" opacity=".25"><animate attributeName="r" values="9;15;9" '
          'dur="1.6s" repeatCount="indefinite"/></circle>'
          f'<circle r="6.5" fill="{P["bg"]}" stroke="{P["cyan"]}" stroke-width="2.5"/>'
          f'<circle r="2.5" fill="{P["cyan"]}"/>'
          f'<rect x="-26" y="-36" width="52" height="20" rx="10" fill="{P["panel"]}" stroke="{P["cyan"]}" '
          'stroke-opacity=".6"/>'
          f'<circle cx="-15" cy="-26" r="2.5" fill="#34d399"><animate attributeName="opacity" values="1;.3;1" '
          'dur="1.2s" repeatCount="indefinite"/></circle>'
          f'<text class="m" x="-8" y="-22.5" font-size="9.5" fill="{P["fg"]}">LIVE</text></g></g>')

    # shipment card, in step with the vehicle
    px_, pw_ = x + mw + 12, w - mw - 12
    c.add(f'<rect x="{px_}" y="{y}" width="{pw_}" height="{h}" rx="8" fill="{P["raised"]}"/>')
    c.label(px_ + 14, y + 22, "LOAD #2481", 10.5, P["dim"])
    c.add(f'<text class="s" x="{px_ + 14}" y="{y + 42}" font-size="14" font-weight="600" fill="{P["fg"]}">'
          "Pickup → Drop-off</text>")
    steps = ["Posted", "Carrier matched", "In transit", "Delivered"]
    sy, gap = y + 66, 23
    c.add(f'<line x1="{px_ + 20}" y1="{sy}" x2="{px_ + 20}" y2="{sy + gap * 3}" stroke="{P["off"]}" stroke-width="2"/>',
          f'<line x1="{px_ + 20}" y1="{sy}" x2="{px_ + 20}" y2="{sy}" stroke="url(#acc)" stroke-width="2">'
          f'<animate attributeName="y2" values="{sy};{sy + gap * 3};{sy + gap * 3}" keyTimes="0;{arrive};1" '
          f'{timing}/></line>')
    for i, step in enumerate(steps):
        cy = sy + i * gap
        on = P["gold"] if i == 3 else P["cyan"]
        t = max(i / 3 * arrive, 0.001)
        c.add(f'<circle cx="{px_ + 20}" cy="{cy}" r="5" fill="{P["off"]}" stroke="{P["raised"]}" stroke-width="2">'
              f'<animate attributeName="fill" values="{P["off"]};{on};{on}" keyTimes="0;{t:.3f};1" '
              f'calcMode="discrete" {timing}/></circle>',
              f'<text class="s" x="{px_ + 34}" y="{cy + 4.5}" font-size="12.5" fill="{P["dim"]}">{step}'
              f'<animate attributeName="fill" values="{P["dim"]};{P["fg"]};{P["fg"]}" keyTimes="0;{t:.3f};1" '
              f'calcMode="discrete" {timing}/></text>')


def _mock_dashboard(c: Card, x: float, y: float, w: float, h: float) -> None:
    """FMD: the panel's sidebar, tiles, trend chart and completion ring."""
    sw = 96
    c.add(f'<rect x="{x}" y="{y}" width="{sw}" height="{h}" rx="8" fill="{P["raised"]}"/>',
          f'<rect x="{x + 12}" y="{y + 12}" width="18" height="18" rx="5" fill="url(#acc)"/>',
          f'<text class="s" x="{x + 36}" y="{y + 26}" font-size="12" font-weight="700" fill="{P["fg"]}">FMD</text>')
    for i in range(5):
        iy = y + 46 + i * 20
        active = i == 1
        if active:
            c.add(f'<rect x="{x + 6}" y="{iy - 7}" width="{sw - 12}" height="18" rx="5" fill="{P["violet"]}" '
                  'fill-opacity=".16"/>')
        c.add(f'<rect x="{x + 14}" y="{iy - 2}" width="8" height="8" rx="2" fill="{P["cyan"] if active else P["dim"]}"/>',
              f'<rect x="{x + 28}" y="{iy}" width="{50 - (i % 3) * 8}" height="5" rx="2.5" '
              f'fill="{P["fg"] if active else P["dim"]}" opacity="{.9 if active else .6}"/>')
    mx, mw = x + sw + 12, w - sw - 12
    c.add(f'<rect x="{mx}" y="{y}" width="{mw - 34}" height="20" rx="6" fill="{P["raised"]}"/>',
          f'<circle cx="{mx + 12}" cy="{y + 10}" r="3.5" fill="none" stroke="{P["dim"]}" stroke-width="1.5"/>',
          f'<rect x="{mx + 22}" y="{y + 8}" width="60" height="4" rx="2" fill="{P["dim"]}"/>',
          f'<circle cx="{mx + mw - 10}" cy="{y + 10}" r="10" fill="url(#acc)"/>')
    tw = (mw - 2 * 10) / 3
    for i, label in enumerate(("students", "courses", "sessions")):
        tx, ty = mx + i * (tw + 10), y + 30
        c.add(f'<rect x="{tx:.0f}" y="{ty}" width="{tw:.0f}" height="40" rx="7" fill="{P["raised"]}"/>')
        c.label(tx + 10, ty + 15, label, 9.5, P["dim"])
        c.add(f'<rect class="growx" x="{tx + 10:.0f}" y="{ty + 23}" width="{38 + i * 6}" height="9" rx="3" '
              f'fill="{P["fg"]}" opacity=".85" style="animation-delay:{0.3 + i * 0.12:.2f}s"/>')
        spark = " ".join(f"{tx + tw - 50 + k * 8:.0f},{ty + 30 - v:.0f}"
                         for k, v in enumerate((3, 6, 4, 9, 7, 12, 14)[i:] + (15, 16, 18)[:i]))
        c.add(f'<polyline points="{spark}" fill="none" stroke="{mix(i / 2)}" stroke-width="1.6" '
              'stroke-linejoin="round"/>')
    cy0, ch = y + 80, h - 80
    cw = mw - 120
    c.add(f'<rect x="{mx}" y="{cy0}" width="{cw}" height="{ch}" rx="7" fill="{P["raised"]}"/>')
    vals = (0.25, 0.4, 0.32, 0.55, 0.5, 0.7, 0.62, 0.85, 0.8)
    pts = [(mx + 12 + k * (cw - 24) / (len(vals) - 1), cy0 + ch - 10 - v * (ch - 22)) for k, v in enumerate(vals)]
    line = "M" + " L".join(f"{px:.0f} {py:.0f}" for px, py in pts)
    c.add(f'<path class="fade" d="{line} L{pts[-1][0]:.0f} {cy0 + ch - 6} L{pts[0][0]:.0f} {cy0 + ch - 6} Z" '
          'fill="url(#area)"/>',
          f'<path class="draw" d="{line}" fill="none" stroke="url(#acc)" stroke-width="2.2" stroke-linejoin="round" '
          'stroke-dasharray="400" style="--len:400"/>',
          f'<circle r="3.5" fill="{P["cyan"]}" stroke="{P["bg"]}" stroke-width="1.5"><animateMotion dur="4s" '
          f'repeatCount="indefinite" path="{line}"/></circle>')
    rx_, ry_ = mx + cw + 10 + 55, cy0 + ch / 2
    c.add(f'<rect x="{mx + cw + 10}" y="{cy0}" width="110" height="{ch}" rx="7" fill="{P["raised"]}"/>',
          f'<circle cx="{rx_}" cy="{ry_}" r="22" fill="none" stroke="{P["off"]}" stroke-width="6"/>',
          f'<circle cx="{rx_}" cy="{ry_}" r="22" fill="none" stroke="url(#acc)" stroke-width="6" stroke-linecap="round" '
          f'stroke-dasharray="104 139" transform="rotate(-90 {rx_} {ry_})">'
          '<animate attributeName="stroke-dasharray" values="0 139;104 139;104 139;0 139" keyTimes="0;.35;.85;1" '
          'dur="5s" repeatCount="indefinite"/></circle>',
          f'<text class="m" x="{rx_}" y="{ry_ + 4}" font-size="11" text-anchor="middle" fill="{P["fg"]}">75%</text>')


def _mock_pipeline(c: Card, x: float, y: float, w: float, h: float) -> None:
    """Eyfel: an order card travels across the board, from a new order to a delivered one."""
    cols = [("New", P["violet"]), ("Kitchen", mix(.4)), ("On the way", P["cyan"]), ("Delivered", P["gold"])]
    gap = 10
    cw = (w - gap * 3) / 4
    platforms = ("#f472b6", "#fb923c", "#34d399")
    for i, (title, color) in enumerate(cols):
        cx = x + i * (cw + gap)
        c.add(f'<rect x="{cx:.0f}" y="{y}" width="{cw:.0f}" height="{h}" rx="8" fill="{P["raised"]}"/>',
              f'<circle cx="{cx + 12:.0f}" cy="{y + 14}" r="3.5" fill="{color}"/>',
              f'<text class="s" x="{cx + 21:.0f}" y="{y + 18}" font-size="11.5" font-weight="600" '
              f'fill="{P["fg"]}">{title}</text>')
        sy = y + 86
        c.add(f'<rect x="{cx + 7:.0f}" y="{sy}" width="{cw - 14:.0f}" height="52" rx="6" fill="{P["panel"]}" '
              f'stroke="{P["line"]}"/>',
              f'<rect x="{cx + 15:.0f}" y="{sy + 10}" width="10" height="10" rx="3" '
              f'fill="{platforms[(i + 1) % 3]}" opacity=".8"/>',
              f'<rect x="{cx + 31:.0f}" y="{sy + 12}" width="{cw - 60:.0f}" height="6" rx="3" fill="{P["dim"]}"/>',
              f'<rect x="{cx + 15:.0f}" y="{sy + 30}" width="{cw - 50:.0f}" height="5" rx="2.5" fill="{P["off"]}"/>',
              f'<rect x="{cx + 15:.0f}" y="{sy + 40}" width="{cw - 70:.0f}" height="5" rx="2.5" fill="{P["off"]}"/>')
    step = cw + gap
    dur = 8
    xs = [0, 0, step, step, 2 * step, 2 * step, 3 * step, 3 * step]
    vals = ";".join(f"{v:.1f} 0" for v in xs)
    c.add(f'<g><animateTransform attributeName="transform" type="translate" values="{vals}" '
          f'keyTimes="0;.18;.26;.44;.52;.7;.78;1" dur="{dur}s" repeatCount="indefinite" calcMode="spline" '
          'keySplines="0 0 1 1;.5 0 .2 1;0 0 1 1;.5 0 .2 1;0 0 1 1;.5 0 .2 1;0 0 1 1"/>'
          f'<rect x="{x + 7:.0f}" y="{y + 26}" width="{cw - 14:.0f}" height="52" rx="6" fill="{P["panel"]}" '
          'stroke="url(#acc)" stroke-width="1.5"/>'
          f'<rect x="{x + 15:.0f}" y="{y + 36}" width="10" height="10" rx="3" fill="{platforms[0]}"/>'
          f'<text class="m" x="{x + 31:.0f}" y="{y + 45}" font-size="10" fill="{P["fg"]}">#1042</text>'
          f'<rect x="{x + 15:.0f}" y="{y + 56}" width="{cw - 44:.0f}" height="5" rx="2.5" fill="{P["dim"]}"/>'
          f'<rect x="{x + 15:.0f}" y="{y + 66}" width="{cw - 64:.0f}" height="5" rx="2.5" fill="{P["off"]}"/>'
          f'<circle cx="{x + cw - 18:.0f}" cy="{y + 41}" r="4" fill="{P["gold"]}">'
          '<animate attributeName="opacity" values="1;.3;1" dur="1.2s" repeatCount="indefinite"/></circle></g>')


def _mock_qr(c: Card, x: float, y: float, w: float, h: float) -> None:
    """Tavuk da Tavuk: a guest scans the table's QR code and the menu opens on the phone."""
    rnd = random.Random(4)
    cell, n = 6, 17
    side = n * cell
    tx, ty, tw = x + 24, y, side + 28
    c.add(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{h}" rx="10" fill="#f8fafc"/>',
          f'<rect x="{tx}" y="{ty}" width="{tw}" height="24" rx="10" fill="{P["gold"]}"/>',
          f'<rect x="{tx}" y="{ty + 14}" width="{tw}" height="10" fill="{P["gold"]}"/>',
          f'<text class="s" x="{tx + tw / 2}" y="{ty + 17}" font-size="11" font-weight="700" text-anchor="middle" '
          'fill="#1f2328">TABLE 7</text>')
    qx, qy = tx + 14, ty + 34
    for i in range(n):
        for j in range(n):
            if (i < 5 and j < 5) or (i < 5 and j >= n - 5) or (i >= n - 5 and j < 5):
                continue
            if rnd.random() < 0.48:
                c.add(f'<rect x="{qx + i * cell}" y="{qy + j * cell}" width="{cell}" height="{cell}" fill="#0f172a"/>')
    for fx, fy in ((0, 0), (n - 5, 0), (0, n - 5)):
        c.add(f'<rect x="{qx + fx * cell + 2}" y="{qy + fy * cell + 2}" width="{5 * cell - 4}" height="{5 * cell - 4}" '
              'rx="3" fill="none" stroke="#0f172a" stroke-width="4"/>',
              f'<rect x="{qx + fx * cell + 9}" y="{qy + fy * cell + 9}" width="{5 * cell - 18}" '
              f'height="{5 * cell - 18}" rx="1.5" fill="#0f172a"/>')
    c.add(f'<rect x="{qx - 6}" y="{qy}" width="{side + 12}" height="2.5" rx="1" fill="{P["cyan"]}">'
          f'<animate attributeName="y" values="{qy};{qy + side};{qy}" dur="2.4s" repeatCount="indefinite"/></rect>')

    px_, pw_ = x + w - 168, 150
    ay = y + h / 2
    c.add(f'<path d="M{tx + tw + 16} {ay} H{px_ - 16}" stroke="{P["dim"]}" stroke-width="2" stroke-dasharray="3 6"/>',
          f'<circle r="4" fill="{P["cyan"]}"><animateMotion dur="1.4s" repeatCount="indefinite" '
          f'path="M{tx + tw + 16} {ay} H{px_ - 16}"/></circle>')
    c.add(f'<rect x="{px_}" y="{y - 4}" width="{pw_}" height="{h + 8}" rx="18" fill="{P["bg"]}" '
          f'stroke="{P["dim"]}" stroke-width="2"/>',
          f'<rect x="{px_ + 55}" y="{y + 3}" width="40" height="5" rx="2.5" fill="{P["dim"]}"/>',
          f'<defs><clipPath id="screen"><rect x="{px_ + 7}" y="{y + 12}" width="{pw_ - 14}" height="{h - 18}" rx="10"/>'
          '</clipPath></defs><g clip-path="url(#screen)">',
          f'<rect x="{px_ + 7}" y="{y + 12}" width="{pw_ - 14}" height="34" fill="url(#acc)" opacity=".85"/>',
          f'<text class="s" x="{px_ + 16}" y="{y + 34}" font-size="12" font-weight="700" fill="#ffffff">Menu</text>')
    for i, (label, wid) in enumerate((("All", 26), ("Mains", 38), ("Drinks", 40))):
        cx = px_ + 12 + sum((26, 38, 40)[:i]) + i * 5
        c.add(f'<rect x="{cx}" y="{y + 52}" width="{wid}" height="15" rx="7.5" '
              f'fill="{P["gold"] if i == 0 else P["raised"]}"/>'
              f'<text class="s" x="{cx + wid / 2}" y="{y + 63}" font-size="8.5" text-anchor="middle" '
              f'fill="{"#1f2328" if i == 0 else P["muted"]}">{label}</text>')
    for i in range(3):
        ry = y + 74 + i * 22
        begin = f"{i * 0.25:.2f}s"
        c.add(f'<g opacity="0"><animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.12;.88;1" dur="4s" '
              f'begin="{begin}" repeatCount="indefinite"/>'
              f'<rect x="{px_ + 12}" y="{ry}" width="18" height="18" rx="5" fill="{mix(i / 2)}" opacity=".8"/>'
              f'<rect x="{px_ + 36}" y="{ry + 3}" width="{56 - i * 8}" height="5" rx="2.5" fill="{P["fg"]}" opacity=".85"/>'
              f'<rect x="{px_ + 36}" y="{ry + 11}" width="30" height="4" rx="2" fill="{P["dim"]}"/>'
              f'<text class="m" x="{px_ + pw_ - 14}" y="{ry + 12}" font-size="9" text-anchor="end" '
              f'fill="{P["gold"]}">₺{(i + 2) * 45}</text></g>')
    c.add("</g>")


def _mock_app(c: Card, x: float, y: float, w: float, h: float) -> None:
    """Any other product: a page that loads its header, hero and cards."""
    c.add(f'<rect x="{x}" y="{y}" width="{w}" height="22" rx="6" fill="{P["raised"]}"/>',
          f'<rect x="{x + 10}" y="{y + 6}" width="10" height="10" rx="3" fill="url(#acc)"/>')
    for i in range(3):
        c.add(f'<rect x="{x + w - 150 + i * 46}" y="{y + 9}" width="34" height="4" rx="2" fill="{P["dim"]}"/>')
    c.add(f'<rect class="in" x="{x}" y="{y + 30}" width="{w * .58:.0f}" height="{h - 30}" rx="8" fill="url(#acc)" '
          'fill-opacity=".14"/>',
          f'<rect class="growx" x="{x + 16}" y="{y + 52}" width="{w * .36:.0f}" height="12" rx="4" fill="{P["fg"]}" '
          'opacity=".85"/>',
          f'<rect class="growx" x="{x + 16}" y="{y + 74}" width="{w * .28:.0f}" height="7" rx="3" fill="{P["dim"]}" '
          'style="animation-delay:.15s"/>',
          f'<rect x="{x + 16}" y="{y + h - 40}" width="84" height="22" rx="11" fill="url(#acc)">'
          '<animate attributeName="opacity" values="1;.6;1" dur="2s" repeatCount="indefinite"/></rect>')
    cx, cw = x + w * .58 + 12, w * .42 - 12
    for i in range(3):
        cy = y + 30 + i * (h - 30) / 3
        c.add(f'<g class="in" style="animation-delay:{0.3 + i * 0.15:.2f}s">'
              f'<rect x="{cx:.0f}" y="{cy + 2:.0f}" width="{cw:.0f}" height="{(h - 30) / 3 - 6:.0f}" rx="7" '
              f'fill="{P["raised"]}"/>'
              f'<rect x="{cx + 10:.0f}" y="{cy + 8:.0f}" width="18" height="18" rx="5" fill="{mix(i / 2)}" '
              'opacity=".8"/>'
              f'<rect x="{cx + 36:.0f}" y="{cy + 10:.0f}" width="{cw - 60:.0f}" height="5" rx="2.5" fill="{P["fg"]}" '
              'opacity=".7"/>'
              f'<rect x="{cx + 36:.0f}" y="{cy + 20:.0f}" width="{cw - 90:.0f}" height="4" rx="2" fill="{P["dim"]}"/></g>')


MOCKUPS = {"app": _mock_app, "route": _mock_route, "dashboard": _mock_dashboard, "pipeline": _mock_pipeline, "qr": _mock_qr}


def product_card(index: int, prod: Product) -> str:
    c = Card(600, 420, f"{prod.name}: {prod.kind}")
    wx, wy, ww, wh = 24, 24, 552, 206
    window(c, wx, wy, ww, wh, prod.file)
    MOCKUPS.get(prod.mockup, _mock_app)(c, wx + 14, wy + 44, ww - 28, wh - 58)
    ty = wy + wh + 36
    c.add(f'<text class="m in" x="30" y="{ty}" font-size="12.5" letter-spacing=".5">'
          f'<tspan fill="{P["dim"]}">{index:02d}  </tspan><tspan fill="{P["cyan"]}">{escape(prod.kind)}</tspan>'
          f'<tspan fill="{P["dim"]}">  ·  {escape(prod.period)}</tspan></text>',
          f'<text class="s in" x="28" y="{ty + 38}" font-size="31" font-weight="700" letter-spacing="-.5" '
          f'fill="{P["fg"]}">{escape(prod.name)}</text>')
    for i, line in enumerate(prod.summary):
        c.add(f'<text class="s in" x="30" y="{ty + 70 + i * 25}" font-size="18" fill="{P["muted"]}" '
              f'style="animation-delay:{0.15 + i * 0.08:.2f}s">{escape(line)}</text>')
    cx = 28
    for i, tag in enumerate(prod.roles + prod.stack):
        is_role = i < len(prod.roles)
        tone = P["violet"] if is_role else P["cyan"]  # what I did, then what it is built with
        tw = _width(tag, 13.5) + 24
        if cx + tw > 572:
            break
        c.add(f'<g class="in" style="animation-delay:{0.35 + i * 0.05:.2f}s">'
              f'<rect x="{cx:.0f}" y="{ty + 112}" width="{tw:.0f}" height="28" rx="14" '
              f'fill="{tone}" fill-opacity=".1" stroke="{tone}" stroke-opacity=".55"/>'
              f'<text class="s" x="{cx + 12:.0f}" y="{ty + 131}" font-size="13.5" '
              f'fill="{P["fg"] if is_role else "#a5f3fc"}">{escape(tag)}</text></g>')
        cx += tw + 8
    return c.svg()


# ---------------------------------------------------------------- toolbox


def toolbox(icon_data: dict[str, str]) -> str:
    c = Card(1200, 290, "Tools I work with, by area")
    c.header("toolbox", "by area")
    col_w = (1200 - 48 * 2 - 3 * 20) / 4
    for ci, (title, keys, tags) in enumerate(TOOLBOX):
        x, y, h = 48 + ci * (col_w + 20), 80, 170
        c.add(f'<g class="in" style="animation-delay:{0.1 + ci * 0.12:.2f}s">'
              f'<rect x="{x:.0f}" y="{y}" width="{col_w:.0f}" height="{h}" rx="14" fill="{P["panel"]}" '
              f'fill-opacity=".9" stroke="{P["line"]}"/>'
              f'<rect x="{x + 20:.0f}" y="{y}" width="{col_w - 40:.0f}" height="1.5" fill="url(#hair)"/>')
        c.label(x + 20, y + 32, title, 13, mix(ci / 3))
        c.label(x + col_w - 20, y + 32, f"{ci + 1:02d}", 12, P["dim"], "end")
        for i, key in enumerate(keys):
            c.add(f'<image x="{x + 20 + i * 56:.0f}" y="{y + 52}" width="44" height="44" href="{icon_data[key]}"/>')
        names = " · ".join(ICON_NAMES[k] for k in keys)
        c.add(f'<text class="s" x="{x + 20:.0f}" y="{y + 126}" font-size="14" fill="{P["fg"]}">{escape(names)}</text>')
        if tags:
            c.add(f'<text class="s" x="{x + 20:.0f}" y="{y + 148}" font-size="13" fill="{P["muted"]}">'
                  f'{escape(" · ".join(tags))}</text>')
        c.add("</g>")
    return c.svg()


# ---------------------------------------------------------------- recognition


def award() -> str:
    c = Card(1200, 300, "NASA International Space Apps Challenge 2022: 1st place, Elazığ")
    window(c, 32, 32, 760, 236, "award.json")
    rows = [("event", '"NASA International Space Apps Challenge"'), ("year", "2022"),
            ("result", '"1st place · Elazığ local winner"'), ("project", '"Wink to the Future"'),
            ("team", '"Innosoft"'), ("built_with", '"Flutter · 48 hours"')]
    lines = ["{"] + [None] * len(rows) + ["}"]
    for i, line in enumerate(lines):
        y = 92 + i * 22
        c.label(66, y, str(i + 1), 13, P["dim"], "end")
        delay = f"{0.2 + i * 0.15:.2f}s"
        if line is not None:
            c.add(f'<text class="m in" x="84" y="{y}" font-size="15" fill="#6b7280" '
                  f'style="animation-delay:{delay}">{line}</text>')
            continue
        k, v = rows[i - 1]
        comma = "," if i < len(rows) else ""
        c.add(f'<text class="m in" x="108" y="{y}" font-size="15" style="animation-delay:{delay}">'
              f'<tspan fill="#c4b5fd">"{k}"</tspan><tspan fill="#6b7280">: </tspan>'
              f'<tspan fill="{"#fde68a" if k == "result" else "#67e8f9"}">{escape(v)}</tspan>'
              f'<tspan fill="#6b7280">{comma}</tspan></text>')
    c.add(f'<rect class="cur" x="96" y="{92 + (len(lines) - 1) * 22 - 13}" width="8" height="16" fill="{P["cyan"]}"/>')

    mx, my = 1000, 150
    rnd = random.Random(9)
    for k in range(10):
        sx, sy = mx + rnd.uniform(-150, 150), my + rnd.uniform(-115, 115)
        if (sx - mx) ** 2 + (sy - my) ** 2 < 105 ** 2:
            continue
        c.add(f'<path class="tw" d="M{sx:.0f} {sy - 5:.0f}L{sx + 1.4:.1f} {sy - 1.4:.1f}L{sx + 5:.0f} {sy:.0f}'
              f'L{sx + 1.4:.1f} {sy + 1.4:.1f}L{sx:.0f} {sy + 5:.0f}L{sx - 1.4:.1f} {sy + 1.4:.1f}L{sx - 5:.0f} {sy:.0f}'
              f'L{sx - 1.4:.1f} {sy - 1.4:.1f}Z" fill="{P["gold"] if k % 3 == 0 else "#e6e8ee"}" '
              f'style="animation-delay:{k * 0.37:.2f}s"/>')
    c.add(f'<circle cx="{mx}" cy="{my}" r="70" fill="{P["violet"]}" opacity=".35" filter="url(#blur)"/>',
          f'<g class="spin" style="transform-origin:{mx}px {my}px"><circle cx="{mx}" cy="{my}" r="94" fill="none" '
          'stroke="url(#acc)" stroke-width="2" stroke-dasharray="6 10"/></g>',
          f'<g class="spinr" style="transform-origin:{mx}px {my}px"><circle cx="{mx}" cy="{my}" r="82" fill="none" '
          f'stroke="{P["gold"]}" stroke-opacity=".5" stroke-dasharray="40 120"/></g>',
          f'<circle cx="{mx}" cy="{my}" r="70" fill="{P["panel"]}" stroke="{P["line"]}"/>')
    glyph(c, "trophy", mx - 8, my - 52, P["gold"])
    c.add(f'<text class="s" x="{mx}" y="{my + 16}" font-size="48" font-weight="700" fill="url(#acc)" '
          'text-anchor="middle">1st</text>')
    c.label(mx, my + 40, "SPACE APPS 2022", 10, anchor="middle")
    return c.svg()


# ---------------------------------------------------------------- open source


def impact(prs: list[PR], star_of: dict[str, int], logos: dict[str, str]) -> str:
    """The open-source card: three numbers, the cumulative curve and the projects I merged most into."""
    per_repo = Counter(pr.repo for pr in prs)
    c = Card(1200, 520, f"{len(prs)} merged pull requests in {len(per_repo)} open-source projects")
    c.header("open-source contributions", "synced hourly", live=True)

    figures = [("merged pull requests", str(len(prs))), ("projects", str(len(per_repo))),
               ("stars across projects", _k(sum(star_of.values())))]
    for i, (label, value) in enumerate(figures):
        y = 116 + i * 70
        c.label(48, y - 26, label, 12, delay=0.1 + i * 0.12)
        c.add(f'<text class="s in" x="46" y="{y + 14}" font-size="40" font-weight="700" fill="url(#acc)" '
              f'style="animation-delay:{0.1 + i * 0.12:.2f}s">{value}</text>')

    gx, gy, gw, gh = 340, 76, 812, 212
    c.add(f'<rect x="{gx}" y="{gy}" width="{gw}" height="{gh}" rx="12" fill="{P["panel"]}" fill-opacity=".9" '
          f'stroke="{P["line"]}"/>')
    times = sorted(pr.closed.timestamp() for pr in prs)
    span = max(times[-1] - times[0], 1)
    px_, py_, pw_, ph_ = gx + 28, gy + 30, gw - 120, gh - 66
    pts = [(px_, py_ + ph_)] + [(px_ + pw_ * (t - times[0]) / span, py_ + ph_ - ph_ * (i + 1) / len(times))
                                for i, t in enumerate(times)]
    line = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    for g in range(1, 4):
        yy = py_ + ph_ * g / 4
        c.add(f'<line x1="{px_}" y1="{yy:.0f}" x2="{px_ + pw_}" y2="{yy:.0f}" stroke="{P["line"]}" '
              'stroke-dasharray="3 5"/>')
    ex, ey = pts[-1]
    c.add(f'<path class="fade" d="{line} L{ex:.1f} {py_ + ph_} Z" fill="url(#area)"/>',
          f'<path class="draw" style="--len:1500" stroke-dasharray="1500" d="{line}" fill="none" stroke="url(#acc)" '
          'stroke-width="3" stroke-linejoin="round"/>',
          f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="10" fill="{P["cyan"]}" opacity=".5" filter="url(#blur)"/>',
          f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="5" fill="{P["cyan"]}"><animate attributeName="r" '
          'values="5;8;5" dur="2s" repeatCount="indefinite"/></circle>',
          f'<g class="fade"><rect x="{ex + 16:.0f}" y="{ey - 14:.0f}" width="58" height="28" rx="14" '
          f'fill="{P["raised"]}" stroke="url(#acc)"/><text class="m" x="{ex + 45:.0f}" y="{ey + 5:.0f}" '
          f'font-size="13" text-anchor="middle" fill="{P["fg"]}">{len(prs)}</text></g>')
    c.label(px_, gy + gh - 14, "merged pull requests, cumulative", 12, P["dim"])

    c.label(48, 334, "most merged into", 12)
    c.add(f'<line x1="180" y1="330" x2="1152" y2="330" stroke="{P["line"]}"/>')
    rows = per_repo.most_common(6)
    c.add('<defs><clipPath id="av" clipPathUnits="objectBoundingBox"><rect width="1" height="1" rx=".28"/></clipPath></defs>')
    most = rows[0][1]
    col_w, leds = 532, 38
    for i, (repo, n) in enumerate(rows):
        x, y = 48 + (i % 2) * (col_w + 40), 372 + (i // 2) * 48
        owner, name = repo.split("/")
        c.add(f'<image x="{x}" y="{y - 14}" width="18" height="18" clip-path="url(#av)" href="{logos[owner]}"/>',
              f'<text class="m" x="{x + 26}" y="{y}" font-size="13"><tspan fill="{P["dim"]}">{escape(owner)}/</tspan>'
              f'<tspan fill="{P["fg"]}">{escape(name)}</tspan></text>',
              f'<text class="m" x="{x + col_w}" y="{y}" font-size="12" text-anchor="end" fill="{P["muted"]}">'
              f'{n} merged <tspan fill="{P["dim"]}">· ★ {_k(star_of[repo])}</tspan></text>')
        lit = max(1, round(leds * n / most))
        step = col_w / leds
        for j in range(leds):
            on = j < lit
            cls = "led pulse" if j == lit - 1 else "led" if on else ""
            anim = f' class="{cls}" style="animation-delay:{0.3 + i * 0.1 + j * 0.02:.2f}s"' if on else ""
            c.add(f'<rect{anim} x="{x + j * step:.1f}" y="{y + 10}" width="{step - 4:.1f}" height="12" rx="2" '
                  f'fill="{mix(j / (leds - 1)) if on else P["off"]}"/>')
    return c.svg()


def gitlog(prs: list[PR], star_of: dict[str, int]) -> str:
    """The latest merged PR in each of the most starred projects, as a git graph."""
    latest: dict[str, PR] = {}
    for pr in prs:
        latest.setdefault(pr.repo, pr)
    rows = sorted(latest.values(), key=lambda pr: -star_of[pr.repo])[:10]
    rows.sort(key=lambda pr: pr.closed, reverse=True)
    top, step = 104, 44
    c = Card(1200, top + len(rows) * step + 28, "Latest merged pull request in my most starred projects")
    lanes = ("#8b5cf6", "#38bdf8", "#34d399", "#fbbf24", "#f472b6", "#fb923c")
    c.header("git log --graph --merges", "HEAD → main")
    c.add(f'<line x1="72" y1="{top - 22}" x2="72" y2="{c.h - 28}" stroke="{P["line"]}" stroke-width="2"/>',
          f'<circle cx="72" cy="{top - 22}" r="6" fill="{P["cyan"]}"><animate attributeName="r" values="6;9;6" '
          'dur="2s" repeatCount="indefinite"/></circle>')
    title_x = 136 + max(len(f"{r.repo}#{r.number}") for r in rows) * 7.9 + 28
    fits = int((1152 - title_x) / 7.4)
    for i, pr in enumerate(rows):
        y = top + i * step + 14
        color = lanes[i % len(lanes)]
        delay = f"{0.15 + i * 0.09:.2f}s"
        title = pr.title if len(pr.title) <= fits else pr.title[: fits - 1] + "…"
        c.add(f'<path class="draw" style="--len:90;animation-delay:{delay}" stroke-dasharray="90" '
              f'd="M72 {y - 32} C72 {y - 22} 104 {y - 26} 104 {y - 16} C104 {y - 6} 72 {y - 10} 72 {y}" '
              f'fill="none" stroke="{color}" stroke-width="2"/>',
              f'<circle cx="104" cy="{y - 16}" r="3.5" fill="{color}"/>',
              f'<circle cx="72" cy="{y}" r="6" fill="{P["bg"]}" stroke="{color}" stroke-width="2.5"/>',
              f'<g class="in" style="animation-delay:{delay}"><text class="m" x="136" y="{y + 5}" font-size="13" '
              f'fill="{color}">{escape(pr.repo)}<tspan fill="{P["muted"]}">#{pr.number}</tspan></text>'
              f'<text class="s" x="{title_x:.0f}" y="{y + 5}" font-size="14" fill="{P["fg"]}">{escape(title)}</text></g>')
    return c.svg()


# ---------------------------------------------------------------- readme


def selected_work(products: list[Product]) -> str:
    """The Selected work block of the README: the featured products, two per row."""
    rows = []
    for i in range(0, len(products), 2):
        cells = []
        for prod in products[i:i + 2]:
            img = (f'<img src="assets/product-{prod.key}.svg" width="49%" '
                   f'alt="{escape(prod.name)}, {escape(prod.kind)}">')
            cells.append(f'<a href="{prod.link}">{img}</a>' if prod.link else img)
        rows.append("<p>\n" + "\n".join(cells) + "\n</p>")
    return "\n".join(rows)


def update_readme(path: Path, products: list[Product]) -> None:
    """Rewrite the README between the selected-work markers, so profile.json drives the section."""
    start, end = "<!-- selected-work:start -->", "<!-- selected-work:end -->"
    text = path.read_text(encoding="utf-8")
    head, rest = text.split(start, 1)
    _, tail = rest.split(end, 1)
    path.write_text(f"{head}{start}\n{selected_work(products)}\n{end}{tail}", encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=root / "profile.json")
    ap.add_argument("--readme", type=Path, default=root / "README.md")
    ap.add_argument("--out", type=Path, default=root / "assets")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    products = load_products(args.data)
    featured = products[:FEATURED]
    cards = {"hero": hero(len(products)), "toolbox": toolbox(icons()), "award": award()}
    for i, prod in enumerate(featured, 1):
        cards[f"product-{prod.key}"] = product_card(i, prod)
    for name, svg in cards.items():
        (args.out / f"{name}.svg").write_text(svg, encoding="utf-8")
    update_readme(args.readme, featured)
    print(f"{len(cards)} cards")


if __name__ == "__main__":
    main()
