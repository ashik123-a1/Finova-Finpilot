import re

def update_landing():
    path = r"F:\china project\src\web\templates\landing.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Ensure Hero section (lines 1 to 161) remains 100% untouched
    hero_end = content.find('<!-- Core Capabilities Grid -->')
    assert hero_end > 0, "Could not find hero end in landing.html"
    hero_part = content[:hero_end]
    rest_part = content[hero_end:]

    # 2. Add telemetry backdrop to #features
    feat_old = '<section id="features" class="py-20 border-t border-white/5 bg-slate-950/40 relative">\n    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">'
    feat_new = '''<section id="features" class="py-20 border-t border-white/5 bg-slate-950/40 relative overflow-hidden">
    <!-- Ambient Telemetry Grid Wallpaper -->
    <div class="absolute inset-0 z-0 opacity-15 pointer-events-none">
        <img src="/static/images/telemetry_data_city.jpg" alt="Telemetry Data Background" class="w-full h-full object-cover object-center filter blur-[1px]">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712] via-[#030712]/70 to-[#030712]"></div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">'''
    rest_part = rest_part.replace(feat_old, feat_new)

    # 3. Update #how-it-works-preview to global_market_gold.jpg
    rest_part = rest_part.replace('/static/images/how_it_works_workspace.jpg', '/static/images/global_market_gold.jpg')

    # 4. Update #forecast-engine to emerald_matrix_runway.jpg
    rest_part = rest_part.replace('/static/images/hero_growth_neon.jpg', '/static/images/emerald_matrix_runway.jpg')

    # 5. Update #sandbox to trading_terminal_depth.jpg
    rest_part = rest_part.replace('/static/images/dscr_loans_chart.jpg', '/static/images/trading_terminal_depth.jpg')

    # 6. Add cash receivables backdrop to #crm-receivables
    crm_old = '<section id="crm-receivables" class="py-20 border-t border-white/5 bg-[#02050f] relative">\n    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">'
    crm_new = '''<section id="crm-receivables" class="py-20 border-t border-white/5 bg-[#02050f] relative overflow-hidden">
    <!-- Ambient Cash Receivables Currency Texture -->
    <div class="absolute inset-0 z-0 opacity-15 pointer-events-none">
        <img src="/static/images/cash_receivables_currency.jpg" alt="Cash Receivables Texture" class="w-full h-full object-cover object-center filter blur-[1px]">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712] via-[#030712]/75 to-[#030712]"></div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12 relative z-10">'''
    rest_part = rest_part.replace(crm_old, crm_new)

    # 7. Add gold coins treasury backdrop to #inventory-supply
    inv_old = '<section id="inventory-supply" class="py-20 border-t border-white/5 relative">\n    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">'
    inv_new = '''<section id="inventory-supply" class="py-20 border-t border-white/5 relative overflow-hidden">
    <!-- Ambient Gold Coins Treasury Texture -->
    <div class="absolute inset-0 z-0 opacity-15 pointer-events-none">
        <img src="/static/images/gold_coins_treasury.jpg" alt="Gold Coins Treasury Texture" class="w-full h-full object-cover object-center filter blur-[1px]">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712] via-[#030712]/75 to-[#030712]"></div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12 relative z-10">'''
    rest_part = rest_part.replace(inv_old, inv_new)

    # 8. Add neon magenta backdrop to #models
    models_old = '<section id="models" class="py-20 border-t border-white/5 bg-slate-950/60 relative">\n    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">'
    models_new = '''<section id="models" class="py-20 border-t border-white/5 bg-slate-950/60 relative overflow-hidden">
    <!-- Ambient Neon Magenta ML Forecast Texture -->
    <div class="absolute inset-0 z-0 opacity-15 pointer-events-none">
        <img src="/static/images/neon_magenta_forecast.jpg" alt="Neon ML Forecast Texture" class="w-full h-full object-cover object-center filter blur-[1px]">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712] via-[#030712]/75 to-[#030712]"></div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">'''
    rest_part = rest_part.replace(models_old, models_new)

    # 9. Add balance scale backdrop to #security
    sec_old = '<section id="security" class="py-20 border-t border-white/5 relative">\n    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">'
    sec_new = '''<section id="security" class="py-20 border-t border-white/5 relative overflow-hidden">
    <!-- Ambient Balance Scale Audit Texture -->
    <div class="absolute inset-0 z-0 opacity-15 pointer-events-none">
        <img src="/static/images/balance_scale_audit.jpg" alt="Balance Scale Audit Texture" class="w-full h-full object-cover object-center filter blur-[1px]">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712] via-[#030712]/75 to-[#030712]"></div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">'''
    rest_part = rest_part.replace(sec_old, sec_new)

    new_content = hero_part + rest_part
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Updated landing.html successfully.")

def update_login():
    path = r"F:\china project\src\web\templates\login.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace("city_growth_bg.jpg?v=4", "fintech_skyline_dusk.jpg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated login.html successfully.")

def update_how_it_works():
    path = r"F:\china project\src\web\templates\how_it_works.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Update Phase 2 image to neon_magenta_forecast.jpg
    content = content.replace('/static/images/hero_growth_neon.jpg', '/static/images/neon_magenta_forecast.jpg')

    # Update Phase 3 image to bank_credit_index.jpg
    content = content.replace('/static/images/dscr_loans_chart.jpg', '/static/images/bank_credit_index.jpg')

    # Update Phase 4 image to cash_receivables_currency.jpg
    content = content.replace('/static/images/accounting_blueprint.jpg', '/static/images/cash_receivables_currency.jpg')

    # Add CTA Banner Background: fintech_skyline_dusk.jpg
    cta_old = '<div class="glass-panel-glow p-8 sm:p-12 rounded-3xl border border-cyan-500/40 text-center space-y-6 relative overflow-hidden">'
    cta_new = '''<div class="glass-panel-glow p-8 sm:p-12 rounded-3xl border border-cyan-500/40 text-center space-y-6 relative overflow-hidden group">
            <!-- Ambient Fintech Skyline Dusk Texture -->
            <div class="absolute inset-0 z-0 opacity-20 pointer-events-none">
                <img src="/static/images/fintech_skyline_dusk.jpg" alt="Fintech Skyline Dusk" class="w-full h-full object-cover object-center filter blur-[0.5px] group-hover:scale-105 transition-transform duration-700">
                <div class="absolute inset-0 bg-gradient-to-r from-[#030712]/95 via-[#030712]/80 to-[#030712]/95"></div>
            </div>'''
    content = content.replace(cta_old, cta_new)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated how_it_works.html successfully.")

if __name__ == "__main__":
    update_landing()
    update_login()
    update_how_it_works()
