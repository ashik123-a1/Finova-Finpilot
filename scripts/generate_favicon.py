from PIL import Image, ImageDraw

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" fill="none">
  <defs>
    <linearGradient id="smeBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#080e1e"/>
      <stop offset="50%" stop-color="#030712"/>
      <stop offset="100%" stop-color="#0a192f"/>
    </linearGradient>
    <linearGradient id="smeCyan" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="100%" stop-color="#06b6d4"/>
    </linearGradient>
    <linearGradient id="smeEmerald" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#34d399"/>
      <stop offset="100%" stop-color="#059669"/>
    </linearGradient>
  </defs>

  <!-- Cyber Badge Base -->
  <rect x="4" y="4" width="56" height="56" rx="16" fill="url(#smeBg)" stroke="url(#smeCyan)" stroke-width="2"/>

  <!-- Subtle Financial Grid -->
  <line x1="14" y1="44" x2="50" y2="44" stroke="#1e293b" stroke-width="1.5" stroke-dasharray="2 2"/>
  <line x1="14" y1="32" x2="50" y2="32" stroke="#1e293b" stroke-width="1.5" stroke-dasharray="2 2"/>

  <!-- Growth Bars -->
  <rect x="16" y="34" width="6" height="10" rx="2" fill="#0284c7" opacity="0.7"/>
  <rect x="26" y="26" width="6" height="18" rx="2" fill="url(#smeCyan)"/>
  <rect x="36" y="18" width="6" height="26" rx="2" fill="url(#smeEmerald)"/>

  <!-- Upward AI Trend Indicator Line -->
  <polyline points="18,32 29,24 39,16 48,13" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="48" cy="13" r="3.5" fill="#34d399" stroke="#064e3b" stroke-width="1.5"/>
  <circle cx="48" cy="13" r="1.5" fill="#ffffff"/>
</svg>
"""

with open("src/web/static/images/favicon.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)

# Draw high-res icon in Pillow
size = 256
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Rounded rectangle background
draw.rounded_rectangle([16, 16, 240, 240], radius=50, fill=(8, 14, 30, 255), outline=(34, 211, 238, 255), width=8)

# Grid lines
for y in [128, 176]:
    draw.line([(50, y), (206, y)], fill=(30, 41, 59, 200), width=4)

# Bars
draw.rounded_rectangle([60, 140, 88, 185], radius=6, fill=(2, 132, 199, 220))
draw.rounded_rectangle([105, 105, 133, 185], radius=6, fill=(34, 211, 238, 255))
draw.rounded_rectangle([150, 70, 178, 185], radius=6, fill=(52, 211, 153, 255))

# Upward Trend line
draw.line([(74, 135), (119, 100), (164, 65), (195, 52)], fill=(56, 189, 248, 255), width=10)

# Peak glowing node
draw.ellipse([185, 42, 205, 62], fill=(52, 211, 153, 255), outline=(6, 78, 59, 255), width=4)
draw.ellipse([191, 48, 199, 56], fill=(255, 255, 255, 255))

# Save PNG and ICO
img.resize((64, 64), Image.Resampling.LANCZOS).save("src/web/static/images/favicon.png")
img.resize((32, 32), Image.Resampling.LANCZOS).save("src/web/static/images/favicon.ico", format="ICO", sizes=[(16,16), (32,32), (48,48), (64,64)])

print("Generated clean financial favicon.svg, favicon.png, favicon.ico successfully!")
