path = r"F:\china project\src\web\templates\landing.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update #how-it-works-preview so the background image covers the ENTIRE section edge-to-edge
old_how_it_works = '''<!-- How It Works Showcase Section (Photo 2: how_it_works_workspace.jpg) -->
<section id="how-it-works-preview" class="py-20 border-t border-white/5 relative bg-[#020611]">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="relative rounded-3xl overflow-hidden border border-cyan-500/30 shadow-2xl bg-slate-950/80">
            <!-- Background Image -->
            <div class="absolute inset-0 z-0">
                <img src="/static/images/global_market_gold.jpg" alt="How SME Finance Copilot Works" class="w-full h-full object-cover object-center filter brightness-[0.70] contrast-[1.1]">
                <div class="absolute inset-0 bg-gradient-to-r from-[#030712]/95 via-[#030712]/80 to-[#030712]/40"></div>
                <div class="absolute inset-0 bg-gradient-to-t from-[#030712] via-transparent to-transparent"></div>
            </div>

            <div class="relative z-10 p-8 sm:p-12 lg:p-16 max-w-2xl space-y-6">
                <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 text-xs font-mono">
                    <i data-lucide="compass" class="w-3.5 h-3.5"></i>
                    <span>Interactive 2nd Page Operator Guide</span>
                </div>
                <h2 class="text-2xl sm:text-4xl font-extrabold text-white leading-tight">
                    See How the Entire Financial AI Pipeline Works
                </h2>
                <p class="text-sm sm:text-base text-slate-300 leading-relaxed">
                    Explore the complete 6-stage operational flow: Ingesting paper receipts, running multilingual OCR, updating integer ledgers, predicting cash runways, and generating bank loan packets.
                </p>
                <div class="pt-2">
                    <a href="/how-it-works" class="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-xl bg-gradient-to-r from-cyan-400 via-teal-300 to-cyan-500 hover:brightness-110 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/30 transition-all">
                        <span>{{ _('landing.btn_explore_guide') }}</span>
                        <i data-lucide="arrow-right" class="w-4 h-4"></i>
                    </a>
                </div>
            </div>
        </div>
    </div>
</section>'''

new_how_it_works = '''<!-- How It Works Showcase Section (Full-Bleed Panoramic Background) -->
<section id="how-it-works-preview" class="py-24 border-t border-white/5 relative overflow-hidden">
    <!-- Edge-to-Edge Panoramic Background Image (Spans Full Screen Width & Height) -->
    <div class="absolute inset-0 z-0 pointer-events-none">
        <img src="/static/images/how_it_works_workspace.jpg" alt="How SME Finance Copilot Works" class="w-full h-full object-cover object-center filter brightness-110 contrast-115">
        <div class="absolute inset-0 bg-gradient-to-r from-[#030712]/85 via-[#030712]/50 to-[#030712]/80"></div>
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712]/80 via-transparent to-[#030712]/80"></div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <!-- Floating High-Clarity Glass Card -->
        <div class="relative rounded-3xl overflow-hidden border border-cyan-500/50 shadow-2xl backdrop-blur-xl bg-slate-950/75 p-8 sm:p-12 lg:p-16 max-w-2xl space-y-6">
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 text-xs font-mono">
                <i data-lucide="compass" class="w-3.5 h-3.5"></i>
                <span>Interactive 2nd Page Operator Guide</span>
            </div>
            <h2 class="text-2xl sm:text-4xl font-extrabold text-white leading-tight">
                See How the Entire Financial AI Pipeline Works
            </h2>
            <p class="text-sm sm:text-base text-slate-300 leading-relaxed">
                Explore the complete 6-stage operational flow: Ingesting paper receipts, running multilingual OCR, updating integer ledgers, predicting cash runways, and generating bank loan packets.
            </p>
            <div class="pt-2">
                <a href="/how-it-works" class="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-xl bg-gradient-to-r from-cyan-400 via-teal-300 to-cyan-500 hover:brightness-110 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/30 transition-all">
                    <span>{{ _('landing.btn_explore_guide') }}</span>
                    <i data-lucide="arrow-right" class="w-4 h-4"></i>
                </a>
            </div>
        </div>
    </div>
</section>'''

if old_how_it_works not in content:
    old_how_it_works = old_how_it_works.replace('\n', '\r\n')
assert old_how_it_works in content, "Could not find old #how-it-works-preview block"
content = content.replace(old_how_it_works, new_how_it_works)

# 2. Update #sandbox so the background has vivid, clearly visible blue candlestick charts and arrow
old_sandbox = '''<!-- Interactive Live Sandbox (Photo 3: dscr_loans_chart.jpg as ambient texture) -->
<section id="sandbox" class="py-20 relative">
    <div class="absolute inset-0 z-0 opacity-15 pointer-events-none">
        <img src="/static/images/trading_terminal_depth.jpg" alt="DSCR Chart Ambient" class="w-full h-full object-cover object-center filter blur-sm">
        <div class="absolute inset-0 bg-[#030712]/90"></div>
    </div>'''

new_sandbox = '''<!-- Interactive Live Sandbox (High-Visibility Bank Credit Index Backdrop) -->
<section id="sandbox" class="py-24 relative overflow-hidden">
    <!-- Edge-to-Edge High-Clarity Ambient Wallpaper (Bright & Vivid Candlesticks & Arrow) -->
    <div class="absolute inset-0 z-0 opacity-70 pointer-events-none">
        <img src="/static/images/bank_credit_index.jpg" alt="Bank Credit Index Ambient" class="w-full h-full object-cover object-center filter brightness-125 contrast-125">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712]/60 via-[#030712]/25 to-[#030712]/75"></div>
        <div class="absolute inset-0 bg-gradient-to-r from-[#030712]/50 via-transparent to-[#030712]/50"></div>
    </div>'''

if old_sandbox not in content:
    old_sandbox = old_sandbox.replace('\n', '\r\n')
assert old_sandbox in content, "Could not find old #sandbox block"
content = content.replace(old_sandbox, new_sandbox)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Successfully updated #how-it-works-preview and #sandbox with edge-to-edge bright backgrounds!")
