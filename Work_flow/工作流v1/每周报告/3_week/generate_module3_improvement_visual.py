from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 2048, 1152
OUTPUT = Path(__file__).with_name("Module3_current_problem_and_improvement.png")
FONT_REGULAR = r"C:\Windows\Fonts\segoeui.ttf"
FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


def wrap(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont, width: int):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if draw.textlength(candidate, font=face) <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        lines.append(current)
    return lines


def text_block(draw, xy, text, face, fill, width, spacing=8):
    x, y = xy
    lines = wrap(draw, text, face, width)
    bbox = draw.textbbox((0, 0), "Ag", font=face)
    line_height = bbox[3] - bbox[1]
    for line in lines:
        draw.text((x, y), line, font=face, fill=fill)
        y += line_height + spacing
    return y


def rounded(draw, box, fill, outline=None, radius=28, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(draw, x1, y1, x2, y2, color, width=6, head=15):
    draw.line((x1, y1, x2 - head, y2), fill=color, width=width)
    draw.polygon(
        [(x2, y2), (x2 - head, y2 - head // 2), (x2 - head, y2 + head // 2)],
        fill=color,
    )


def layer_card(draw, box, number, title, body, fill, accent):
    rounded(draw, box, fill=fill, outline=accent, radius=24, width=2)
    x1, y1, x2, _ = box
    cx, cy = x1 + 58, y1 + 62
    draw.ellipse((cx - 29, cy - 29, cx + 29, cy + 29), fill=accent)
    nfont = font(28, True)
    nb = draw.textbbox((0, 0), str(number), font=nfont)
    draw.text((cx - (nb[2] - nb[0]) / 2, cy - 20), str(number), font=nfont, fill="white")
    draw.text((x1 + 105, y1 + 24), title, font=font(28, True), fill="#172B42")
    text_block(draw, (x1 + 105, y1 + 70), body, font(22), "#42566C", x2 - x1 - 140, 5)


def main():
    image = Image.new("RGB", (WIDTH, HEIGHT), "#F5F7FA")
    draw = ImageDraw.Draw(image)

    # Header
    draw.text((70, 48), "Module 3: From Fixed Rules to Reusable Discovery Knowledge",
              font=font(49, True), fill="#14283F")
    draw.text((72, 116), "Current bottleneck and the proposed generalisation path",
              font=font(25), fill="#637286")
    draw.line((70, 158, WIDTH - 70, 158), fill="#DCE3EB", width=2)

    left = (70, 188, 770, 1080)
    right = (810, 188, 1978, 1080)
    rounded(draw, left, fill="#FFF8F6", outline="#EBC7C0", radius=32, width=3)
    rounded(draw, right, fill="#F7FBFF", outline="#BCD5EA", radius=32, width=3)

    # Left column
    lx = left[0] + 34
    draw.text((lx, 215), "CURRENT LIMITATION", font=font(24, True), fill="#B3483B")
    rounded(draw, (lx, 260, left[2] - 34, 362), fill="#FCE8E3", radius=20)
    draw.text((lx + 24, 274), "10 / 94", font=font(43, True), fill="#A83D31")
    draw.text((lx + 195, 285), "providers resolved in the bounded full run",
              font=font(22), fill="#6E3C36")

    text_block(
        draw,
        (lx, 398),
        "Existing IIIF discovery skills cannot retrieve Manifests from most candidate institutions.",
        font(27, True),
        "#263B50",
        left[2] - left[0] - 68,
        8,
    )
    draw.text((lx, 525), "SKILLS BEFORE IMPROVEMENT", font=font(21, True), fill="#7A514B")

    skills = [
        "Direct Manifest detection",
        "IIIF Collection traversal (Presentation 2/3 + pagination)",
        "Change Discovery Activity Stream traversal",
        "Explicit IIIF links exposed by JSON APIs",
        "HTML links, data attributes and embedded JSON-LD",
        "Bounded same-site crawl and curated endpoints",
    ]
    y = 568
    for item in skills:
        draw.ellipse((lx + 2, y + 8, lx + 16, y + 22), fill="#C95F50")
        y = text_block(draw, (lx + 32, y), item, font(21), "#334A60", left[2] - lx - 74, 4) + 13

    rounded(draw, (lx, 926, left[2] - 34, 1043), fill="#FFFFFF", outline="#E4B5AC", radius=18, width=2)
    draw.text((lx + 22, 944), "MAIN GAP", font=font(19, True), fill="#B3483B")
    text_block(
        draw,
        (lx + 22, 978),
        "Unknown institutional APIs, identifier enumeration and Manifest URL patterns.",
        font(20),
        "#4D5E70",
        left[2] - lx - 78,
        4,
    )

    # Right column
    rx = right[0] + 34
    draw.text((rx, 215), "PROPOSED IMPROVEMENT", font=font(24, True), fill="#1F6091")
    draw.text((right[2] - 365, 218), "THREE-LAYER MODULE 3", font=font(19, True), fill="#5E7690")

    layer_card(
        draw,
        (rx, 260, right[2] - 34, 406),
        1,
        "Investigation Playbook",
        "Analyse Module 2 evidence -> identify the platform/API -> consult official documentation -> verify one complete Manifest chain.",
        "#EAF3FF",
        "#377DB6",
    )
    layer_card(
        draw,
        (rx, 424, right[2] - 34, 570),
        2,
        "Reusable Generic Skills",
        "API pagination • identifier extraction • record filtering • URL-template expansion • deterministic IIIF validation.",
        "#EAF8F3",
        "#27836A",
    )
    layer_card(
        draw,
        (rx, 588, right[2] - 34, 734),
        3,
        "Provider Knowledge & Configuration",
        "Store verified API URLs, JSON paths, pagination rules, filters, Manifest templates and evidence for later reuse.",
        "#F1EDFF",
        "#7057B5",
    )

    draw.text((rx, 772), "AI-ASSISTED PROBLEM-SOLVING MEMORY", font=font(21, True), fill="#1F6091")
    node_y1, node_y2 = 817, 905
    node_w, gap = 235, 45
    node_xs = [rx + i * (node_w + gap) for i in range(4)]
    nodes = [
        ("UNKNOWN", "provider"),
        ("AI", "investigates"),
        ("VALIDATOR", "confirms"),
        ("KNOWLEDGE", "is retained"),
    ]
    colors = ["#E8EEF5", "#EAF3FF", "#EAF8F3", "#F1EDFF"]
    borders = ["#8495A8", "#377DB6", "#27836A", "#7057B5"]
    for i, (top, bottom) in enumerate(nodes):
        x = node_xs[i]
        rounded(draw, (x, node_y1, x + node_w, node_y2), fill=colors[i], outline=borders[i], radius=18, width=2)
        tw = draw.textlength(top, font=font(19, True))
        bw = draw.textlength(bottom, font=font(19))
        draw.text((x + (node_w - tw) / 2, node_y1 + 17), top, font=font(19, True), fill="#24384D")
        draw.text((x + (node_w - bw) / 2, node_y1 + 48), bottom, font=font(19), fill="#52667B")
        if i < 3:
            arrow(draw, x + node_w + 8, (node_y1 + node_y2) // 2,
                  node_xs[i + 1] - 8, (node_y1 + node_y2) // 2, "#7890A7", 5, 15)

    draw.text((rx + 5, 923), "The verified method becomes experience for the next unknown provider.",
              font=font(19), fill="#536B82")

    rounded(draw, (rx, 963, right[2] - 34, 1043), fill="#193D5C", radius=20)
    draw.text((rx + 24, 978), "FUTURE: CONNECT AI / SEARCH / DOCUMENTATION APIs",
              font=font(21, True), fill="white")
    draw.text((rx + 24, 1010), "AI proposes discovery recipes; deterministic checks validate every Manifest before reuse.",
              font=font(19), fill="#D8E8F6")

    image.save(OUTPUT, quality=96)
    print(OUTPUT.resolve())


if __name__ == "__main__":
    main()
