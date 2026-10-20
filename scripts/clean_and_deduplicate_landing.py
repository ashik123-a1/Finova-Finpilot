import re

path = r"F:\china project\src\web\templates\landing.html"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Look for '{% block content %}'
blocks = [m.start() for m in re.finditer(r'\{%\s*block\s+content\s*%\}', text)]
print("Block content positions:", blocks)

# If there are multiple, keep only the proper one
# Let's inspect text around blocks
for b in blocks:
    print("Block at", b, "starts with:", repr(text[b:b+80]))

# Also check {% endblock %}
endblocks = [m.start() for m in re.finditer(r'\{%\s*endblock\s*%\}', text)]
print("Endblock positions:", endblocks)
