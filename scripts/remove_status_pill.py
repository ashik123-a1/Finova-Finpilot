path = r"F:\china project\src\web\templates\landing.html"
with open(path, "r", encoding="utf-8") as f:
    c = f.read()

target = '''            <!-- Status / Announcement Pill -->
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-950/40 text-cyan-300 text-xs font-mono mb-6 shadow-sm shadow-cyan-950">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>{{ _('landing.status_pill') }}</span>
            </div>\n\n'''

if target not in c:
    target = target.replace('\n', '\r\n')

if target not in c:
    # Try without the trailing double newline
    target = '''            <!-- Status / Announcement Pill -->
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-950/40 text-cyan-300 text-xs font-mono mb-6 shadow-sm shadow-cyan-950">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>{{ _('landing.status_pill') }}</span>
            </div>'''
    if target not in c:
        target = target.replace('\n', '\r\n')

assert target in c, "Could not find status pill in landing.html"
c = c.replace(target, '')

with open(path, "w", encoding="utf-8") as f:
    f.write(c)

print("Successfully removed status pill from landing.html")
