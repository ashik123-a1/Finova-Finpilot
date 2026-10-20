import os

def update_landing():
    path = r"F:\china project\src\web\templates\landing.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Remove "API Docs" link from top nav (Marking 1 in user's screenshot)
    api_docs_snippet = '''                <a href="/docs" target="_blank" class="px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-200 hover:text-white glass-panel hover:bg-slate-800/80 transition-all border border-slate-700/60 shadow-sm flex items-center gap-1.5 whitespace-nowrap shrink-0 font-mono">
                    <span>{{ _('landing.nav_docs') }}</span>
                    <i data-lucide="external-link" class="w-3 h-3 text-slate-400"></i>
                </a>\n'''
    if api_docs_snippet not in content:
        # Try CRLF
        api_docs_snippet = api_docs_snippet.replace('\n', '\r\n')
    assert api_docs_snippet in content, "Could not find API Docs button in landing.html"
    content = content.replace(api_docs_snippet, '')

    # 2. Remove "VIDEO ACTIVE" button from bottom right (Marking 2 in user's screenshot)
    video_btn_snippet = '''        <!-- Play/Pause Accessibility Control Pill -->
        <button type="button" id="hero-video-toggle-btn" onclick="toggleHeroVideo()"
                class="absolute bottom-4 right-4 z-20 px-3 py-1.5 rounded-full bg-slate-900/85 hover:bg-slate-800 border border-white/10 hover:border-cyan-500/40 text-slate-300 text-xs font-mono flex items-center gap-1.5 backdrop-blur-md transition-all cursor-pointer shadow-lg shadow-black/40"
                title="Toggle background video playback" aria-label="Toggle background video playback">
            <i id="hero-video-toggle-icon" data-lucide="pause" class="w-3.5 h-3.5 text-cyan-400"></i>
            <span id="hero-video-toggle-label" class="text-[10px] uppercase font-bold tracking-wider text-slate-300">{{ _('landing.video_active') }}</span>
        </button>\n'''
    if video_btn_snippet not in content:
        video_btn_snippet = video_btn_snippet.replace('\n', '\r\n')
    assert video_btn_snippet in content, "Could not find VIDEO ACTIVE button in landing.html"
    content = content.replace(video_btn_snippet, '')

    # 3. Remove "Antigravity Competition Build" from footer
    antigravity_str = '<span class="font-mono text-cyan-400">Version 0.1.0 • Antigravity Competition Build</span>'
    enterprise_str = '<span class="font-mono text-cyan-400">Version 1.0.0 • Enterprise Edition</span>'
    content = content.replace(antigravity_str, enterprise_str)

    # 4. Make all backgrounds bright, crisp, high quality (NO blur, much higher opacity, lighter overlays)
    # 4a. #features
    old_feat_bg = '''    <!-- Ambient Telemetry Grid Wallpaper -->
    <div class="absolute inset-0 z-0 opacity-15 pointer-events-none">
        <img src="/static/images/telemetry_data_city.jpg" alt="Telemetry Data Background" class="w-full h-full object-cover object-center filter blur-[1px]">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712] via-[#030712]/70 to-[#030712]"></div>
    </div>'''
    new_feat_bg = '''    <!-- Ambient Telemetry Grid Wallpaper (Bright & Crisp) -->
    <div class="absolute inset-0 z-0 opacity-45 pointer-events-none">
        <img src="/static/images/telemetry_data_city.jpg" alt="Telemetry Data Background" class="w-full h-full object-cover object-center filter brightness-110 contrast-110">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712]/70 via-[#030712]/40 to-[#030712]/80"></div>
    </div>'''
    if old_feat_bg not in content:
        old_feat_bg = old_feat_bg.replace('\n', '\r\n')
    content = content.replace(old_feat_bg, new_feat_bg)

    # 4b. #how-it-works-preview
    old_how_bg = '''                <img src="/static/images/global_market_gold.jpg" alt="How SME Finance Copilot Works" class="w-full h-full object-cover object-center filter brightness-[0.65] contrast-[1.15] group-hover:scale-105 transition-transform duration-700">
                <div class="absolute inset-0 bg-gradient-to-r from-[#030712]/95 via-[#030712]/85 to-[#030712]/50"></div>
                <div class="absolute inset-0 bg-gradient-to-t from-[#030712] via-transparent to-transparent"></div>'''
    new_how_bg = '''                <img src="/static/images/global_market_gold.jpg" alt="How SME Finance Copilot Works" class="w-full h-full object-cover object-center filter brightness-105 contrast-115 group-hover:scale-105 transition-transform duration-700">
                <div class="absolute inset-0 bg-gradient-to-r from-[#030712]/90 via-[#030712]/55 to-[#030712]/15"></div>
                <div class="absolute inset-0 bg-gradient-to-t from-[#030712]/70 via-transparent to-transparent"></div>'''
    if old_how_bg not in content:
        old_how_bg = old_how_bg.replace('\n', '\r\n')
    content = content.replace(old_how_bg, new_how_bg)

    # 4c. #forecast-engine
    old_fore_bg = '''    <!-- Ambient Emerald Matrix Runway Wallpaper -->
    <div class="absolute inset-0 z-0 opacity-25 pointer-events-none">
        <img src="/static/images/emerald_matrix_runway.jpg" alt="Emerald Matrix Runway" class="w-full h-full object-cover object-center filter blur-[0.5px]">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712] via-transparent to-[#030712]"></div>
    </div>'''
    new_fore_bg = '''    <!-- Ambient Emerald Matrix Runway Wallpaper (Bright, Zero Blur) -->
    <div class="absolute inset-0 z-0 opacity-50 pointer-events-none">
        <img src="/static/images/emerald_matrix_runway.jpg" alt="Emerald Matrix Runway" class="w-full h-full object-cover object-center filter brightness-115 contrast-115">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712]/75 via-[#030712]/35 to-[#030712]/85"></div>
    </div>'''
    if old_fore_bg not in content:
        old_fore_bg = old_fore_bg.replace('\n', '\r\n')
    content = content.replace(old_fore_bg, new_fore_bg)

    # 4d. #sandbox
    old_sand_bg = '''    <div class="absolute inset-0 z-0 opacity-20 pointer-events-none">
        <img src="/static/images/trading_terminal_depth.jpg" alt="Trading Terminal Depth" class="w-full h-full object-cover object-center filter blur-[1px]">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712] via-[#030712]/80 to-[#030712]"></div>
    </div>'''
    new_sand_bg = '''    <div class="absolute inset-0 z-0 opacity-45 pointer-events-none">
        <img src="/static/images/trading_terminal_depth.jpg" alt="Trading Terminal Depth" class="w-full h-full object-cover object-center filter brightness-110 contrast-110">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712]/75 via-[#030712]/40 to-[#030712]/85"></div>
    </div>'''
    if old_sand_bg not in content:
        old_sand_bg = old_sand_bg.replace('\n', '\r\n')
    content = content.replace(old_sand_bg, new_sand_bg)

    # 4e. #crm-receivables
    old_crm_bg = '''    <!-- Ambient Cash Receivables Currency Texture -->
    <div class="absolute inset-0 z-0 opacity-15 pointer-events-none">
        <img src="/static/images/cash_receivables_currency.jpg" alt="Cash Receivables Texture" class="w-full h-full object-cover object-center filter blur-[1px]">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712] via-[#030712]/75 to-[#030712]"></div>
    </div>'''
    new_crm_bg = '''    <!-- Ambient Cash Receivables Currency Texture (Bright & Crisp) -->
    <div class="absolute inset-0 z-0 opacity-45 pointer-events-none">
        <img src="/static/images/cash_receivables_currency.jpg" alt="Cash Receivables Texture" class="w-full h-full object-cover object-center filter brightness-110 contrast-115">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712]/70 via-[#030712]/40 to-[#030712]/80"></div>
    </div>'''
    if old_crm_bg not in content:
        old_crm_bg = old_crm_bg.replace('\n', '\r\n')
    content = content.replace(old_crm_bg, new_crm_bg)

    # 4f. #inventory-supply
    old_inv_bg = '''    <!-- Ambient Gold Coins Treasury Texture -->
    <div class="absolute inset-0 z-0 opacity-15 pointer-events-none">
        <img src="/static/images/gold_coins_treasury.jpg" alt="Gold Coins Treasury Texture" class="w-full h-full object-cover object-center filter blur-[1px]">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712] via-[#030712]/75 to-[#030712]"></div>
    </div>'''
    new_inv_bg = '''    <!-- Ambient Gold Coins Treasury Texture (Bright & Radiant) -->
    <div class="absolute inset-0 z-0 opacity-50 pointer-events-none">
        <img src="/static/images/gold_coins_treasury.jpg" alt="Gold Coins Treasury Texture" class="w-full h-full object-cover object-center filter brightness-115 contrast-115">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712]/70 via-[#030712]/35 to-[#030712]/80"></div>
    </div>'''
    if old_inv_bg not in content:
        old_inv_bg = old_inv_bg.replace('\n', '\r\n')
    content = content.replace(old_inv_bg, new_inv_bg)

    # 4g. #models
    old_mod_bg = '''    <!-- Ambient Neon Magenta ML Forecast Texture -->
    <div class="absolute inset-0 z-0 opacity-15 pointer-events-none">
        <img src="/static/images/neon_magenta_forecast.jpg" alt="Neon ML Forecast Texture" class="w-full h-full object-cover object-center filter blur-[1px]">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712] via-[#030712]/75 to-[#030712]"></div>
    </div>'''
    new_mod_bg = '''    <!-- Ambient Neon Magenta ML Forecast Texture (Bright & Vivid) -->
    <div class="absolute inset-0 z-0 opacity-45 pointer-events-none">
        <img src="/static/images/neon_magenta_forecast.jpg" alt="Neon ML Forecast Texture" class="w-full h-full object-cover object-center filter brightness-115 contrast-115">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712]/75 via-[#030712]/40 to-[#030712]/85"></div>
    </div>'''
    if old_mod_bg not in content:
        old_mod_bg = old_mod_bg.replace('\n', '\r\n')
    content = content.replace(old_mod_bg, new_mod_bg)

    # 4h. #security
    old_sec_bg = '''    <!-- Ambient Balance Scale Audit Texture -->
    <div class="absolute inset-0 z-0 opacity-15 pointer-events-none">
        <img src="/static/images/balance_scale_audit.jpg" alt="Balance Scale Audit Texture" class="w-full h-full object-cover object-center filter blur-[1px]">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712] via-[#030712]/75 to-[#030712]"></div>
    </div>'''
    new_sec_bg = '''    <!-- Ambient Balance Scale Audit Texture (Bright & Crisp) -->
    <div class="absolute inset-0 z-0 opacity-45 pointer-events-none">
        <img src="/static/images/balance_scale_audit.jpg" alt="Balance Scale Audit Texture" class="w-full h-full object-cover object-center filter brightness-110 contrast-110">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712]/70 via-[#030712]/40 to-[#030712]/80"></div>
    </div>'''
    if old_sec_bg not in content:
        old_sec_bg = old_sec_bg.replace('\n', '\r\n')
    content = content.replace(old_sec_bg, new_sec_bg)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated landing.html successfully.")

def update_how_it_works():
    path = r"F:\china project\src\web\templates\how_it_works.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Remove Antigravity Competition Build
    content = content.replace(
        '<span class="font-mono text-cyan-400">Version 0.1.0 • Antigravity Competition Build</span>',
        '<span class="font-mono text-cyan-400">Version 1.0.0 • Enterprise Edition</span>'
    )

    # 2. Hero blueprint banner: make it bright and sharp
    content = content.replace(
        'filter brightness-[0.75] contrast-[1.1]',
        'filter brightness-[0.95] contrast-[1.15]'
    )
    content = content.replace(
        '<div class="absolute inset-0 bg-gradient-to-r from-[#030712]/95 via-[#030712]/75 to-[#030712]/40"></div>',
        '<div class="absolute inset-0 bg-gradient-to-r from-[#030712]/85 via-[#030712]/55 to-[#030712]/15"></div>'
    )

    # 3. CTA Banner: make fintech skyline dusk bright and crisp
    old_cta = '''            <!-- Ambient Fintech Skyline Dusk Texture -->
            <div class="absolute inset-0 z-0 opacity-20 pointer-events-none">
                <img src="/static/images/fintech_skyline_dusk.jpg" alt="Fintech Skyline Dusk" class="w-full h-full object-cover object-center filter blur-[0.5px] group-hover:scale-105 transition-transform duration-700">
                <div class="absolute inset-0 bg-gradient-to-r from-[#030712]/95 via-[#030712]/80 to-[#030712]/95"></div>
            </div>'''
    new_cta = '''            <!-- Ambient Fintech Skyline Dusk Texture (Bright & Crisp) -->
            <div class="absolute inset-0 z-0 opacity-55 pointer-events-none">
                <img src="/static/images/fintech_skyline_dusk.jpg" alt="Fintech Skyline Dusk" class="w-full h-full object-cover object-center filter brightness-115 contrast-115 group-hover:scale-105 transition-transform duration-700">
                <div class="absolute inset-0 bg-gradient-to-r from-[#030712]/80 via-[#030712]/45 to-[#030712]/80"></div>
            </div>'''
    if old_cta not in content:
        old_cta = old_cta.replace('\n', '\r\n')
    content = content.replace(old_cta, new_cta)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated how_it_works.html successfully.")

def update_login():
    path = r"F:\china project\src\web\templates\login.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Make login background wallpaper bright and remove blur
    content = content.replace(
        'opacity: 0.65;\n  filter: brightness(0.78) contrast(1.15) saturate(1.2);',
        'opacity: 0.85;\n  filter: brightness(1.05) contrast(1.15) saturate(1.25);'
    )
    content = content.replace(
        'opacity: 0.65;\r\n  filter: brightness(0.78) contrast(1.15) saturate(1.2);',
        'opacity: 0.85;\r\n  filter: brightness(1.05) contrast(1.15) saturate(1.25);'
    )
    content = content.replace(
        'backdrop-filter: blur(0.5px);',
        'backdrop-filter: none;'
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated login.html successfully.")

if __name__ == "__main__":
    update_landing()
    update_how_it_works()
    update_login()
