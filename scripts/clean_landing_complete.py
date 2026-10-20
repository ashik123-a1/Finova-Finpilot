import re

path = r"F:\china project\src\web\templates\landing.html"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# The clean part ends at the first complete template end:
end_str = '{% endblock %}'
first_end = text.find(end_str, 50000)
if first_end != -1:
    first_part = text[:first_end + len(end_str)]
else:
    first_part = text

lines = first_part.splitlines()

# Collapse alternating blank lines
collapsed = []
i = 0
while i < len(lines):
    collapsed.append(lines[i])
    if i + 1 < len(lines) and lines[i+1].strip() == '':
        i += 2
    else:
        i += 1

result = '\n'.join(collapsed)

# Remove the status pill element
pill_snippet = '''            <!-- Status / Announcement Pill -->
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-950/40 text-cyan-300 text-xs font-mono mb-6 shadow-sm shadow-cyan-950">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>{{ _('landing.status_pill') }}</span>
            </div>'''

result = result.replace(pill_snippet, '')

# Also remove in case formatting differs slightly
pill_regex = r'<div class="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-950/40 text-cyan-300 text-xs font-mono mb-6 shadow-sm shadow-cyan-950">.*?</div>'
result = re.sub(pill_regex, '', result, flags=re.DOTALL)
result = result.replace('<!-- Status / Announcement Pill -->', '')

# Ensure title block is clean
result = re.sub(r'\{%\s*block title\s*%\}.*?\{%\s*endblock\s*%\}', "{% block title %}SME Finance Copilot — Autonomous Financial Copilot{% endblock %}", result, count=1)

# Write back
with open(path, "w", encoding="utf-8", newline='\n') as f:
    f.write(result)

print(f"Successfully cleaned landing.html. Total lines: {len(result.splitlines())}")
print(f"Contains status_pill: {'landing.status_pill' in result}")
