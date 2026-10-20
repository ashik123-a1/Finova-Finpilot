import traceback

try:
    path = r"F:\china project\src\web\templates\landing.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Normalize CRLF to LF for reliable string searching
    c = content.replace('\r\n', '\n')

    # 1. Update #how-it-works-preview
    start_tag = '<!-- How It Works Showcase Section'
    end_tag = '</section>'
    p1 = c.find(start_tag)
    p2 = c.find(end_tag, p1) + len(end_tag)
    print("Found #how-it-works-preview:", p1, p2)

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

    c = c[:p1] + new_how_it_works + c[p2:]

    # 2. Update #sandbox
    start_sb = '<!-- Interactive Live Sandbox'
    p_sb = c.find(start_sb)
    p_sb_inner = c.find('<div class="max-w-5xl mx-auto', p_sb)
    print("Found #sandbox:", p_sb, p_sb_inner)

    new_sb_top = '''<!-- Interactive Live Sandbox (High-Visibility Bank Credit Index Backdrop) -->
<section id="sandbox" class="py-24 relative overflow-hidden">
    <!-- Edge-to-Edge High-Clarity Ambient Wallpaper (Bright & Vivid Candlesticks & Arrow) -->
    <div class="absolute inset-0 z-0 opacity-75 pointer-events-none">
        <img src="/static/images/bank_credit_index.jpg" alt="Bank Credit Index Ambient" class="w-full h-full object-cover object-center filter brightness-125 contrast-125">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712]/50 via-[#030712]/20 to-[#030712]/70"></div>
        <div class="absolute inset-0 bg-gradient-to-r from-[#030712]/40 via-transparent to-[#030712]/40"></div>
    </div>

    '''

    c = c[:p_sb] + new_sb_top + c[p_sb_inner:]

    # Write back with original CRLF
    c = c.replace('\n', '\r\n')
    with open(path, "w", encoding="utf-8") as f:
        f.write(c)
    print("Done safely!")
except Exception as e:
    traceback.print_exc()
