import re

path = r"F:\china project\src\web\templates\landing.html"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Replace any occurrence of 3 or more newlines with 2 newlines (standard clean formatting)
text = re.sub(r'\n{3,}', '\n\n', text)

# Now remove the status pill in the hero:
# <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-950/40 text-cyan-300 text-xs font-mono mb-6 shadow-sm shadow-cyan-950">
#     <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
#     <span>{{ _('landing.status_pill') }}</span>
# </div>
pattern = r'<!-- Status / Announcement Pill -->\s*<div class="inline-flex items-center[^>]*>.*?<span>\{\{\s*_\(\'landing\.status_pill\'\)\s*\}\}</span>\s*</div>'
text = re.sub(pattern, '', text, flags=re.DOTALL)

# In case comment is not there:
pattern2 = r'<div class="inline-flex items-center[^>]*>\s*<span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>\s*<span>\{\{\s*_\(\'landing\.status_pill\'\)\s*\}\}</span>\s*</div>'
text = re.sub(pattern2, '', text, flags=re.DOTALL)

# Title tag: replace with clean title
text = text.replace("{% block title %}SME Finance Copilot — {{ _('landing.status_pill') }}{% endblock %}", "{% block title %}SME Finance Copilot — Autonomous Financial Copilot{% endblock %}")
text = text.replace("{% block title %}SME Finance Copilot  {{ _('landing.status_pill') }}{% endblock %}", "{% block title %}SME Finance Copilot — Autonomous Financial Copilot{% endblock %}")

# Deduplicate any duplicate section if any
with open(path, "w", encoding="utf-8", newline='\n') as f:
    f.write(text)

print("Cleaned landing.html, lines:", len(text.splitlines()))
