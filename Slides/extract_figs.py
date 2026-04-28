"""Extract figure regions from the original PDF page renders."""
from PIL import Image
import os

EXTRACT = "extracted"
OUT     = "figs_from_pdf"
os.makedirs(OUT, exist_ok=True)

def crop(page, box, out_name):
    src = Image.open(f"{EXTRACT}/page-{page:02d}.png")
    W, H = src.size
    left, top, right, bottom = box
    cropped = src.crop((int(left*W), int(top*H), int(right*W), int(bottom*H)))
    cropped.save(f"{OUT}/{out_name}")
    print(f"  saved {out_name}  ({cropped.size})")

# Page 4: MaxCut problem - the two diamond graphs
crop(4, (0.05, 0.20, 0.98, 0.95), "maxcut_problem.png")

# Page 12: Classical benchmarks bar chart (tight)
crop(12, (0.555, 0.30, 0.97, 0.93), "gw_bars.png")

# Page 26: 3-regular MaxCut=13 - just the right-side graph (no page#)
crop(26, (0.66, 0.55, 0.97, 0.93), "3reg_best.png")

# Page 27: 3-regular MaxCut=12 - just the right-side graph (no page#)
crop(27, (0.66, 0.55, 0.97, 0.93), "3reg_second_best.png")

# Page 6 portfolio graph (right side, tighter top to skip title bleed)
crop(6, (0.51, 0.27, 0.97, 0.92), "portfolio_setup.png")

# Page 7 colored partition graph (left side, tighter)
crop(7, (0.05, 0.27, 0.49, 0.92), "portfolio_solved.png")

# Page 7 investor results table (right side, tighter)
crop(7, (0.51, 0.27, 0.97, 0.92), "portfolio_table.png")

print("done")
