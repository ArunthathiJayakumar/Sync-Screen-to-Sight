"""
Convert `architecture.svg` to `architecture.jpg` using cairosvg.
Run with the project's working venv (Python 3.11) e.g.: 

& "C:\\venv311a\\Scripts\\python.exe" vision_django_app/docs/convert_svg_to_jpg.py

If cairosvg is not installed, install it into the venv:
& "C:\\venv311a\\Scripts\\python.exe" -m pip install cairosvg
"""
import os
from cairosvg import svg2png

BASE = os.path.dirname(__file__)
SVG = os.path.join(BASE, 'architecture.svg')
OUT_JPG = os.path.join(BASE, 'architecture.jpg')
OUT_PNG = os.path.join(BASE, 'architecture.png')

if not os.path.exists(SVG):
    print('SVG file not found:', SVG)
    raise SystemExit(1)

print('Converting', SVG, '→', OUT_PNG)
# Convert SVG to PNG first (cairosvg outputs PNG/PNG bytes)
svg2png(url=SVG, write_to=OUT_PNG, dpi=150)
print('PNG written to', OUT_PNG)

# Convert PNG to JPG using Pillow (if available) to get smaller JPG file
try:
    from PIL import Image
    im = Image.open(OUT_PNG).convert('RGB')
    im.save(OUT_JPG, quality=90)
    print('JPG written to', OUT_JPG)
except Exception as e:
    print('Pillow not available or conversion failed:', e)
    print('You can convert PNG to JPG manually. PNG saved at', OUT_PNG)
