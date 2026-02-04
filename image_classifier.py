"""
image_classifier.py  —  two-stage image classification

Stage 1: Pillow heuristics  (instant, CPU, no network)
         Catches the obvious 80 %: product-on-white, swatch, infographic …
         Returns confidence 65-90.

Stage 2: Claude Haiku vision API  (only for the uncertain 20 %)
         Sends the image as base64 → gets back a label.
         Returns confidence 92.

No heavy models.  No GPU.  Works on any CPU server.
"""

from __future__ import annotations

import base64, io, traceback
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageFilter

# ---------------------------------------------------------------------------
# Labels  (match Belami mediatype values exactly)
# ---------------------------------------------------------------------------
LABELS = ("main_product_image", "lifestyle", "informational",
          "dimension", "swatch", "detail")

CONFIDENCE_THRESHOLD = 65   # below this → route to Claude


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------
@dataclass
class ClassificationResult:
    label:      str                             # one of LABELS
    confidence: int                             # 0-100
    stage:      str                             # "heuristic" | "claude_api" | "error"
    details:    dict = field(default_factory=dict)


# ===========================================================================
# STAGE 1 — PILLOW HEURISTICS
# ===========================================================================

def _analyze(img: Image.Image) -> dict:
    """Seven numeric signals extracted at 200x200."""
    if img.mode != "RGB":
        img = img.convert("RGB")

    sm     = img.resize((200, 200), Image.LANCZOS)
    pixels = list(sm.getdata())          # 40 000 x (R,G,B)
    N      = len(pixels)

    # --- background lightness ---
    white_pct = sum(1 for r,g,b in pixels if r>230 and g>230 and b>230) / N * 100
    light_pct = sum(1 for r,g,b in pixels if r>210 and g>210 and b>210) / N * 100

    # --- colour buckets  (8 bins/channel -> max 512) ---
    uc = len(set((r//32, g//32, b//32) for r,g,b in pixels))

    # --- edges ---
    gray  = sm.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edata = list(edges.getdata())
    edge_pct = sum(1 for p in edata if p > 30) / N * 100

    # --- text-block grid  (10x10 = 100 blocks) ---
    tb = 0
    for row in range(0, 200, 20):
        for col in range(0, 200, 20):
            blk = edges.crop((col, row, col+20, row+20))
            if sum(1 for p in blk.getdata() if p > 30) > 40:
                tb += 1

    # --- centre brightness (inner 50 %) ---
    ctr  = list(sm.crop((50,50,150,150)).getdata())
    c_lp = sum(1 for r,g,b in ctr if r>210 and g>210 and b>210) / len(ctr) * 100

    # --- grayscale std  (overall contrast / complexity) ---
    glist  = list(gray.getdata())
    mean_g = sum(glist) / N
    gs     = (sum((p - mean_g)**2 for p in glist) / N) ** 0.5

    return dict(
        white_pct=round(white_pct, 1),
        light_pct=round(light_pct, 1),
        unique_colors=uc,
        edge_pct=round(edge_pct, 1),
        text_blocks=tb,
        center_light=round(c_lp, 1),
        gray_std=round(gs, 1),
    )


def _classify_signals(s: dict) -> tuple[str, int]:
    """Decision tree -> (label, confidence).  conf < 65 = uncertain."""
    lp  = s["light_pct"]
    cl  = s["center_light"]
    uc  = s["unique_colors"]
    ep  = s["edge_pct"]
    tb  = s["text_blocks"]
    gs  = s["gray_std"]
    wp  = s["white_pct"]

    # 1  swatch  -- almost no detail, <=4 colours, not white
    if uc <= 4 and gs < 20 and wp < 75:
        return ("swatch", 90)

    # 2  main product  -- light surround, darker centre (the object), few text blocks
    if lp > 55 and cl < 45 and tb < 25:
        return ("main_product_image", 88)

    # 3  dimension  -- nearly-white bg, limited palette, geometric edges
    #    checked BEFORE informational because dimension diagrams also have text blocks
    if lp > 75 and uc < 18 and ep > 6 and tb > 10:
        return ("dimension", 75)

    # 4  informational  -- many text blocks on light bg, colour-rich
    if tb > 35 and lp > 40:
        return ("informational", 82)

    # 5  lifestyle  -- dark colourful scene with real-photo complexity
    if lp < 30 and uc > 15 and gs > 30:
        return ("lifestyle", 78)

    # 6  uncertain  -> Claude will decide
    return ("detail", 55)


def classify_pil(img: Image.Image) -> ClassificationResult:
    """Heuristic-only.  Fast.  Call this first."""
    try:
        sig        = _analyze(img)
        label, conf = _classify_signals(sig)
        return ClassificationResult(label=label, confidence=conf,
                                    stage="heuristic", details=sig)
    except Exception as exc:
        return ClassificationResult(label="detail", confidence=0,
                                    stage="error", details={"error": str(exc)})


# ===========================================================================
# STAGE 2 — CLAUDE HAIKU VISION  (sync, called only when heuristic < 65 %)
# ===========================================================================

_PROMPT = """You are classifying a product image for an e-commerce asset library.

Look at this image and pick EXACTLY ONE label:

  main_product_image   -- single product on white or very light background
  lifestyle            -- product shown in a room or real-world scene
  informational        -- infographic with text, icons, charts
  dimension            -- technical drawing showing measurements
  swatch               -- a colour or material sample block
  detail               -- close-up, angle shot, or anything that does not fit above

Respond with ONLY the label, nothing else."""


def _call_claude(jpeg_bytes: bytes) -> str:
    """POST image to Anthropic, return raw text label."""
    import requests                         # sync -- fine for Streamlit

    b64 = base64.b64encode(jpeg_bytes).decode()
    body = {
        "model": "claude-haiku-4-5-20251001",   # fast + cheap
        "max_tokens": 10,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image",
                 "source": {"type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64}},
                {"type": "text", "text": _PROMPT},
            ],
        }],
    }
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        json=body,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["content"][0]["text"].strip().lower()


def _sanitise(raw: str) -> str:
    """Map Claude free-text answer back to a canonical label."""
    raw = raw.strip().lower().replace("_", " ").replace("-", " ")
    hits = {
        "main product image": "main_product_image",
        "main product":       "main_product_image",
        "product image":      "main_product_image",
        "lifestyle":          "lifestyle",
        "informational":      "informational",
        "infographic":        "informational",
        "dimension":          "dimension",
        "dimensions":         "dimension",
        "technical":          "dimension",
        "diagram":            "dimension",
        "swatch":             "swatch",
        "color swatch":       "swatch",
        "colour swatch":      "swatch",
        "detail":             "detail",
        "angle":              "detail",
        "close up":           "detail",
    }
    if raw in hits:
        return hits[raw]
    for key, label in hits.items():
        if key in raw:
            return label
    return "detail"


# ===========================================================================
# PUBLIC  -- main entry points used by asset_generator
# ===========================================================================

def classify_from_url(url: str) -> ClassificationResult:
    """Download image at *url* -> heuristic -> Claude if uncertain."""
    import requests

    try:
        resp  = requests.get(url, timeout=15)
        resp.raise_for_status()
        raw   = resp.content
        ctype = resp.headers.get("content-type", "")

        # PDF -> no vision analysis possible
        if "pdf" in ctype or url.lower().endswith(".pdf"):
            return ClassificationResult(
                label="spec_sheet", confidence=95, stage="heuristic",
                details={"note": "PDF detected from Content-Type / extension"})

        # Video -> flag directly
        if any(url.lower().endswith(ext) for ext in (".mp4", ".mov", ".avi", ".wmv", ".webm")):
            return ClassificationResult(
                label="video", confidence=95, stage="heuristic",
                details={"note": "Video detected from extension"})

        return classify_from_bytes(raw)

    except Exception as exc:
        return ClassificationResult(
            label="detail", confidence=0, stage="error",
            details={"error": str(exc), "url": url})


def classify_from_bytes(img_bytes: bytes) -> ClassificationResult:
    """Classify raw image bytes.  Heuristic first; Claude if uncertain."""
    try:
        img = Image.open(io.BytesIO(img_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")

        # --- Stage 1 ---
        result = classify_pil(img)
        if result.confidence >= CONFIDENCE_THRESHOLD:
            return result                   # confident enough -- done

        # --- Stage 2: re-encode as small JPEG, send to Claude ---
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        jpeg_bytes = buf.getvalue()

        raw_label = _call_claude(jpeg_bytes)
        label     = _sanitise(raw_label)

        return ClassificationResult(
            label=label, confidence=92, stage="claude_api",
            details={**result.details, "claude_raw": raw_label})

    except Exception as exc:
        return ClassificationResult(
            label="detail", confidence=0, stage="error",
            details={"error": str(exc), "traceback": traceback.format_exc()})
