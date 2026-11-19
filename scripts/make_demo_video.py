"""Render the project's demo video (MP4) for the website from real project material (no API calls).

The video walks through the problem, the method, the architecture, a replay of the recorded output of
scripts/demo_compare.py (docs/demo_output_base-6.txt, typed out line by line, labelled as a replay, not a
live screen capture), and the main results with the saved figures. Every number shown is taken from the
result files used in the thesis.

Output: paper/figures/demo_video.mp4 (1280x720, 24 fps) and a poster frame demo_video_poster.png.

Run from the Temporal-GraphRAG folder:
    python scripts/make_demo_video.py
"""
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "paper" / "figures"
OUT = FIG / "demo_video.mp4"
W, H, FPS = 1280, 720, 24
FONTS = Path(r"C:\Windows\Fonts")

INK, MUTED, BLUE, MAROON, GREY = (27, 27, 27), (90, 90, 90), (42, 120, 214), (164, 18, 63), (138, 137, 132)
TERM_BG, TERM_FG, TERM_DIM, GREEN, RED = (30, 31, 34), (225, 225, 225), (150, 150, 150), (120, 200, 120), (230, 120, 110)


def font(name: str, size: int):
    """Load a Windows font, falling back to the next candidate if one is missing."""
    for n in name.split("|"):
        p = FONTS / n
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


F_TITLE = font("segoeuib.ttf|arialbd.ttf", 44)
F_H = font("segoeuib.ttf|arialbd.ttf", 34)
F_B = font("segoeui.ttf|arial.ttf", 26)
F_S = font("segoeui.ttf|arial.ttf", 20)
F_MONO = font("consola.ttf|cour.ttf", 15)
F_MONO_B = font("consolab.ttf|consola.ttf", 15)


def wrap(draw, text: str, f, width: int) -> list:
    """Split text into lines that fit `width` pixels."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=f) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def base_slide(title: str) -> tuple:
    """White slide with a title and a thin maroon rule at the top-left; returns (image, draw)."""
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([60, 52, 66, 98], fill=MAROON)
    d.text((84, 50), title, font=F_H, fill=INK)
    return img, d


def bullets(d, items: list, y: int, x: int = 90, width: int = 1100, f=F_B, gap: int = 14) -> int:
    """Draw bullet points; returns the y after the last one."""
    for it in items:
        lines = wrap(d, it, f, width - 30)
        d.ellipse([x, y + 14, x + 8, y + 22], fill=BLUE)
        for i, ln in enumerate(lines):
            d.text((x + 24, y + i * (f.size + 8)), ln, font=f, fill=INK)
        y += len(lines) * (f.size + 8) + gap
    return y


def caption(d, text: str) -> None:
    """Small grey caption at the bottom of the frame."""
    d.text((90, H - 52), text, font=F_S, fill=MUTED)


def fit_image(path: Path, box: tuple) -> Image.Image:
    """Load an image and scale it to fit inside box=(w, h), keeping its aspect ratio."""
    im = Image.open(path).convert("RGB")
    bw, bh = box
    s = min(bw / im.width, bh / im.height)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)


# ----------------------------------------------------------------------------------------------
# Scenes: each returns a function t -> frame (t in seconds since the scene started)
# ----------------------------------------------------------------------------------------------
def scene_title():
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 10], fill=MAROON)
    y = 210
    for ln in ["Soft Temporal Kernels and Hybrid Lexical Seeding", "for Graph Retrieval in Time-Sensitive Financial QA"]:
        d.text(((W - d.textlength(ln, font=F_TITLE)) / 2, y), ln, font=F_TITLE, fill=INK)
        y += 62
    for ln, f, col in [("Shashvath M  ·  M.Tech, Amrita School of Computing, Coimbatore", F_B, MUTED),
                       ("Supervisor: Dr. Ramraj T", F_B, MUTED),
                       ("Project walkthrough and a replay of the recorded demo run", F_S, BLUE)]:
        y += 22
        d.text(((W - d.textlength(ln, font=f)) / 2, y), ln, font=f, fill=col)
        y += f.size
    return lambda t: img


def scene_problem():
    img, d = base_slide("The problem")
    bullets(d, [
        "Questions about company results name a period: “EOG Resources’ free cash flow in 2021-Q4?”",
        "The base method (TG-RAG) keeps a stored fact only if its date lies inside the asked period: a hard 0/1 filter.",
        "Those dates are written by a language model while the graph is built. In our graph, 832 of 8,408 facts (9.9 %) carry a date that is not a valid calendar form, e.g. “2023 QQ3”, “Q1 2023”, “LAST YEAR”.",
        "When nothing matches exactly, retrieval starts from nothing and the model answers without evidence.",
    ], 140)
    caption(d, "Source: docs/hand_checks/malformed_timestamps.md (count over the project's own graph)")
    return lambda t: img


def scene_idea():
    img, d = base_slide("Our idea: a soft time weight")
    d.text((90, 135), "κ(τ) = max over asked periods t of exp(−λ · d(τ, t)),   keep a fact if κ ≥ 0.05,   λ = 1", font=F_B, fill=INK)
    d.text((90, 180), "d = steps between the fact's date and the asked period in a year → quarter → month → day tree.", font=F_S, fill=MUTED)
    rows = [("Stored date vs asked period", "d", "κ", "kept"),
            ("inside the asked period", "0", "1.000", "yes"),
            ("year fact, quarter of the same year asked", "1", "0.368", "yes"),
            ("neighbouring quarter, same year", "2", "0.135", "yes"),
            ("year fact, quarter of another year asked", "3", "0.050", "no"),
            ("neighbouring quarter across a year boundary", "4", "0.018", "no")]
    y, xs = 235, (110, 760, 880, 1020)
    for i, r in enumerate(rows):
        if i == 0:
            d.rectangle([100, y - 6, 1130, y + 34], fill=MAROON)
        elif i % 2 == 0:
            d.rectangle([100, y - 6, 1130, y + 34], fill=(244, 244, 242))
        for x, cell in zip(xs, r):
            d.text((x, y), cell, font=F_S, fill="white" if i == 0 else INK)
        y += 44
    d.text((90, y + 20), "As λ → ∞ the weight becomes the original 0/1 filter, so TG-RAG is a special case.", font=F_B, fill=BLUE)
    caption(d, "Kernel and distance as implemented in soft_time.py; λ = 1 was chosen on the development set, then locked.")
    return lambda t: img


def scene_figure(title: str, fig: str, cap: str):
    img, d = base_slide(title)
    im = fit_image(FIG / fig, (1120, 520))
    img.paste(im, ((W - im.width) // 2, 120))
    caption(d, cap)
    return lambda t: img


def demo_lines() -> list:
    """The recorded demo output, cut to the parts that fit on screen (all text taken from the file)."""
    raw = (ROOT / "docs" / "demo_output_base-6.txt").read_text(encoding="utf-8").splitlines()
    keep = []
    for ln in raw:
        s = ln.rstrip()
        if not s or set(s) == {"="}:
            continue
        keep.append(s[:128])
    return keep


def scene_demo():
    lines = ["$ python scripts/demo_compare.py --qid base-6"] + demo_lines()
    per_line = 0.42  # seconds per line while typing

    def frame(t):
        img = Image.new("RGB", (W, H), TERM_BG)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, W, 34], fill=(45, 46, 50))
        d.text((16, 8), "Replay of the recorded output of scripts/demo_compare.py  (docs/demo_output_base-6.txt)",
               font=F_MONO, fill=TERM_DIM)
        n = min(len(lines), int(t / per_line) + 1)
        shown = lines[:n]
        max_rows = 37
        shown = shown[-max_rows:]
        y = 46
        for ln in shown:
            col = TERM_FG
            f = F_MONO
            if ln.startswith("$"):
                col, f = GREEN, F_MONO_B
            elif "DROP" in ln and "0.1353" not in ln:
                col = TERM_DIM
            elif "0.1353" in ln:
                col = GREEN
            elif ln.startswith("ANSWER") or ln.startswith("QUESTION") or ln.startswith("CANDIDATE"):
                f = F_MONO_B
            elif "Facts kept" in ln or "Chunks sent" in ln or "Saved judge" in ln:
                col, f = (240, 200, 90), F_MONO_B
            d.text((16, y), ln, font=f, fill=col)
            y += 18
        return img
    return frame, len(lines) * per_line + 3.0


def scene_demo_summary():
    img, d = base_slide("What the demo shows")
    d.rounded_rectangle([90, 140, 620, 470], radius=14, fill=(244, 244, 242), outline=GREY, width=2)
    d.rounded_rectangle([660, 140, 1190, 470], radius=14, fill=(230, 240, 251), outline=BLUE, width=2)
    d.text((115, 160), "TG-RAG (hard filter)", font=F_H, fill=INK)
    d.text((685, 160), "Soft kernel (ours)", font=F_H, fill=BLUE)
    bullets(d, ["kept 0 of 60 candidate facts", "sent 0 chunks to the model", "answer: three invented figures", "judge score 0.00"], 225, x=110, width=500, f=F_B, gap=10)
    bullets(d, ["kept 13 of 60 (neighbouring quarters, κ = 0.135)", "sent 11 chunks", "answer: 2021-Q4 = $2 billion (correct)", "judge score 0.33"], 225, x=680, width=500, f=F_B, gap=10)
    d.text((90, 500), "An illustrative case: on the 152 test questions this zero-evidence situation", font=F_B, fill=INK)
    d.text((90, 538), "occurs on only 2 of 116 answerable questions.", font=F_B, fill=INK)
    caption(d, "Numbers from docs/demo_output_base-6.txt and results/seed_analysis.md")
    return lambda t: img


def scene_results():
    img, d = base_slide("Main result on 152 held-out test questions")
    rows = [("Method", "Correct (all)", "Answerable", "Unanswerable"),
            ("TG-RAG, reproduced", "0.599", "0.540", "0.792"),
            ("Naive RAG", "0.548", "0.426", "0.944"),
            ("Soft kernel, λ = 1 (ours)", "0.603", "0.554", "0.764"),
            ("Soft kernel + walk", "0.605", "0.555", "0.764"),
            ("Question-independent decay", "0.605", "0.547", "0.792")]
    y, xs = 135, (110, 600, 820, 1010)
    for i, r in enumerate(rows):
        fill = MAROON if i == 0 else ((230, 240, 251) if i == 3 else ((244, 244, 242) if i % 2 == 0 else None))
        if fill:
            d.rectangle([100, y - 6, 1180, y + 34], fill=fill)
        for x, cell in zip(xs, r):
            d.text((x, y), cell, font=F_S, fill="white" if i == 0 else INK)
        y += 46
    d.text((90, y + 25), "Soft kernel vs TG-RAG: +0.004, 95 % CI [−0.049, +0.059], p = 0.445.", font=F_B, fill=INK)
    d.text((90, y + 65), "The pre-registered main claim is not supported: the two tie on average.", font=F_B, fill=MAROON)
    caption(d, "Source: results_test/overall.csv and significance.csv (paired bootstrap, 1,000 resamples)")
    return lambda t: img


def scene_close():
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 10], fill=MAROON)
    y = 170
    for ln, f, col in [("What we found", F_H, INK),
                       ("The soft kernel changes the evidence on 110 of 116 answerable questions,", F_B, INK),
                       ("helping multi-period questions and hurting single-period, multi-company ones;", F_B, INK),
                       ("the effects cancel. When stored dates are noisy, the hard filter declines", F_B, INK),
                       ("and the soft kernel does not (0.627 vs 0.566 at 30 % shifted dates; a trend).", F_B, INK),
                       ("", F_B, INK),
                       ("Code, results and paper: github.com/Shashvath11/Soft-Temporal-Kernel-Graph-Retrieval", F_S, BLUE)]:
        d.text(((W - d.textlength(ln, font=f)) / 2, y), ln, font=f, fill=col)
        y += f.size + 18
    return lambda t: img


def main():
    demo, demo_len = scene_demo()
    scenes = [
        (scene_title(), 4.0),
        (scene_problem(), 8.0),
        (scene_idea(), 9.0),
        (scene_figure("System architecture", "architecture.png",
                      "Grey: the base method's released code, unchanged. Blue: our extension, swapped in at run time."), 7.0),
        (demo, demo_len),
        (scene_demo_summary(), 8.0),
        (scene_results(), 9.0),
        (scene_figure("Robustness to wrong stored dates", "robustness_test.png",
                      "Test set: Correct as the share of dates shifted by one quarter grows (results_test_noise*/)."), 8.0),
        (scene_figure("Where the methods differ", "per_type_test.png",
                      "Test set: Correct by question type, TG-RAG vs soft kernel (exploratory; results_test/by_type.csv)."), 7.0),
        (scene_close(), 7.0),
    ]
    fade = 0.4
    writer = imageio.get_writer(str(OUT), fps=FPS, codec="libx264", quality=7, pixelformat="yuv420p", macro_block_size=8)
    prev_last = None
    n_frames = 0
    for k, (fn, dur) in enumerate(scenes):
        frames = int(dur * FPS)
        for i in range(frames):
            t = i / FPS
            fr = np.asarray(fn(t), dtype=np.float32)
            if prev_last is not None and t < fade:  # cross-fade from the previous scene
                a = t / fade
                fr = prev_last * (1 - a) + fr * a
            writer.append_data(fr.astype(np.uint8))
            n_frames += 1
            if k == 6 and i == frames // 2:
                Image.fromarray(fr.astype(np.uint8)).save(FIG / "demo_video_poster.png")
        prev_last = np.asarray(fn((frames - 1) / FPS), dtype=np.float32)
    writer.close()
    print(f"wrote {OUT} ({n_frames / FPS:.0f} s, {OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
