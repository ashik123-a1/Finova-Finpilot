import re
from pathlib import Path

landing_path = Path("F:/china project/src/web/templates/landing.html")
text = landing_path.read_text(encoding="utf-8")

# Verify lines 1 to 157
split_token = "<!-- Core Capabilities Grid -->"
assert split_token in text, "Split token not found in landing.html"

top_part, _ = text.split(split_token, 1)

# Ensure How It Works link is added to top nav
if "/how-it-works" not in top_part:
    old_nav_block = """            <!-- Left Side Menu (Styled as glass-panel buttons, strictly one line) -->
            <div class="hidden md:flex items-center justify-start gap-2.5 whitespace-nowrap">
                <a href="#features" class="px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-200 hover:text-white glass-panel hover:bg-slate-800/80 transition-all border border-slate-700/60 shadow-sm flex items-center gap-1.5 whitespace-nowrap shrink-0">
                    <i data-lucide="layers" class="w-3.5 h-3.5 text-cyan-400 shrink-0"></i>
                    <span>{{ _('landing.nav_capabilities') }}</span>
                </a>"""
    new_nav_block = """            <!-- Left Side Menu (Styled as glass-panel buttons, strictly one line) -->
            <div class="hidden md:flex items-center justify-start gap-2.5 whitespace-nowrap">
                <a href="/how-it-works" class="px-3 py-2 rounded-xl text-xs font-semibold text-cyan-300 hover:text-white glass-panel hover:bg-slate-800/80 transition-all border border-cyan-500/40 shadow-sm flex items-center gap-1.5 whitespace-nowrap shrink-0">
                    <i data-lucide="compass" class="w-3.5 h-3.5 text-cyan-400 shrink-0"></i>
                    <span>{{ _('landing.nav_how_it_works') }}</span>
                </a>
                <a href="#features" class="px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-200 hover:text-white glass-panel hover:bg-slate-800/80 transition-all border border-slate-700/60 shadow-sm flex items-center gap-1.5 whitespace-nowrap shrink-0">
                    <i data-lucide="layers" class="w-3.5 h-3.5 text-cyan-400 shrink-0"></i>
                    <span>{{ _('landing.nav_capabilities') }}</span>
                </a>"""
    top_part = top_part.replace(old_nav_block, new_nav_block)

new_bottom_part = """<!-- Core Capabilities Grid -->
<section id="features" class="py-20 border-t border-white/5 bg-slate-950/40 relative">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-3xl mx-auto mb-16">
            <h2 class="text-xs font-bold font-mono tracking-widest uppercase text-cyan-400 mb-2">{{ _('landing.arch_tag') }}</h2>
            <p class="text-3xl font-extrabold text-white">{{ _('landing.arch_title') }}</p>
            <p class="mt-3 text-slate-400 text-sm">{{ _('landing.arch_desc') }}</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Feature 1 -->
            <div class="glass-panel p-6 rounded-3xl border border-white/5 hover:border-cyan-500/30 transition-all group">
                <div class="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-5 group-hover:scale-110 transition-transform">
                    <i data-lucide="trending-up" class="w-6 h-6"></i>
                </div>
                <h3 class="text-lg font-bold text-white mb-2">{{ _('landing.feat1_title') }}</h3>
                <p class="text-slate-400 text-xs leading-relaxed">{{ _('landing.feat1_desc') }}</p>
            </div>

            <!-- Feature 2 -->
            <div class="glass-panel p-6 rounded-3xl border border-white/5 hover:border-emerald-500/30 transition-all group">
                <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-5 group-hover:scale-110 transition-transform">
                    <i data-lucide="file-check-2" class="w-6 h-6"></i>
                </div>
                <h3 class="text-lg font-bold text-white mb-2">{{ _('landing.feat2_title') }}</h3>
                <p class="text-slate-400 text-xs leading-relaxed">{{ _('landing.feat2_desc') }}</p>
            </div>

            <!-- Feature 3 -->
            <div class="glass-panel p-6 rounded-3xl border border-white/5 hover:border-indigo-500/30 transition-all group">
                <div class="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-5 group-hover:scale-110 transition-transform">
                    <i data-lucide="shield-check" class="w-6 h-6"></i>
                </div>
                <h3 class="text-lg font-bold text-white mb-2">{{ _('landing.feat3_title') }}</h3>
                <p class="text-slate-400 text-xs leading-relaxed">{{ _('landing.feat3_desc') }}</p>
            </div>

            <!-- Feature 4 -->
            <div class="glass-panel p-6 rounded-3xl border border-white/5 hover:border-cyan-500/30 transition-all group">
                <div class="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 mb-5 group-hover:scale-110 transition-transform">
                    <i data-lucide="building-2" class="w-6 h-6"></i>
                </div>
                <h3 class="text-lg font-bold text-white mb-2">{{ _('landing.feat4_title') }}</h3>
                <p class="text-slate-400 text-xs leading-relaxed">{{ _('landing.feat4_desc') }}</p>
            </div>

            <!-- Feature 5 -->
            <div class="glass-panel p-6 rounded-3xl border border-white/5 hover:border-emerald-500/30 transition-all group">
                <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 mb-5 group-hover:scale-110 transition-transform">
                    <i data-lucide="bot" class="w-6 h-6"></i>
                </div>
                <h3 class="text-lg font-bold text-white mb-2">{{ _('landing.feat5_title') }}</h3>
                <p class="text-slate-400 text-xs leading-relaxed">{{ _('landing.feat5_desc') }}</p>
            </div>

            <!-- Feature 6 -->
            <div class="glass-panel p-6 rounded-3xl border border-white/5 hover:border-indigo-500/30 transition-all group">
                <div class="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mb-5 group-hover:scale-110 transition-transform">
                    <i data-lucide="globe" class="w-6 h-6"></i>
                </div>
                <h3 class="text-lg font-bold text-white mb-2">{{ _('landing.feat6_title') }}</h3>
                <p class="text-slate-400 text-xs leading-relaxed">{{ _('landing.feat6_desc') }}</p>
            </div>
        </div>
    </div>
</section>

<!-- How It Works Showcase Section (Photo 2: how_it_works_workspace.jpg) -->
<section id="how-it-works-preview" class="py-20 border-t border-white/5 relative bg-[#020611]">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="relative rounded-3xl overflow-hidden border border-cyan-500/30 shadow-2xl bg-slate-950/80">
            <!-- Background Image -->
            <div class="absolute inset-0 z-0">
                <img src="/static/images/how_it_works_workspace.jpg" alt="How SME Finance Copilot Works" class="w-full h-full object-cover object-center filter brightness-[0.70] contrast-[1.1]">
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
</section>

<!-- Cash Flow Runway & AI Forecast Engine (Photo 1: hero_growth_neon.jpg) -->
<section id="forecast-engine" class="py-20 border-t border-white/5 relative overflow-hidden">
    <!-- Ambient Neon Grid Background -->
    <div class="absolute inset-0 z-0 opacity-25 pointer-events-none">
        <img src="/static/images/hero_growth_neon.jpg" alt="Neon Growth Mesh" class="w-full h-full object-cover object-center filter blur-[1px]">
        <div class="absolute inset-0 bg-gradient-to-b from-[#030712] via-transparent to-[#030712]"></div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 space-y-12">
        <div class="text-center max-w-3xl mx-auto">
            <h2 class="text-xs font-bold font-mono tracking-widest uppercase text-emerald-400 mb-2">Predictive Liquidity Engine</h2>
            <p class="text-3xl font-extrabold text-white">{{ _('landing.feat_forecast_title') }}</p>
            <p class="mt-3 text-slate-400 text-sm">{{ _('landing.feat_forecast_desc') }}</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="glass-panel p-5 rounded-2xl border border-white/10 space-y-2">
                <div class="text-xs font-mono text-cyan-400">7-Day Horizon</div>
                <div class="text-2xl font-bold font-mono text-white">৳ 128,450</div>
                <div class="text-[11px] text-emerald-400 flex items-center gap-1">
                    <i data-lucide="trending-up" class="w-3.5 h-3.5"></i>
                    <span>+4.2% Cash Cushion</span>
                </div>
            </div>
            <div class="glass-panel p-5 rounded-2xl border border-white/10 space-y-2">
                <div class="text-xs font-mono text-cyan-400">14-Day Horizon</div>
                <div class="text-2xl font-bold font-mono text-white">৳ 242,100</div>
                <div class="text-[11px] text-emerald-400 flex items-center gap-1">
                    <i data-lucide="check-circle" class="w-3.5 h-3.5"></i>
                    <span>Optimal Supplier Liquidity</span>
                </div>
            </div>
            <div class="glass-panel p-5 rounded-2xl border border-white/10 space-y-2">
                <div class="text-xs font-mono text-cyan-400">30-Day Runway</div>
                <div class="text-2xl font-bold font-mono text-white">৳ 518,900</div>
                <div class="text-[11px] text-cyan-300">WAPE: 0.12 • High Stability</div>
            </div>
            <div class="glass-panel p-5 rounded-2xl border border-white/10 space-y-2">
                <div class="text-xs font-mono text-cyan-400">90-Day Projected</div>
                <div class="text-2xl font-bold font-mono text-white">৳ 1,480,000</div>
                <div class="text-[11px] text-indigo-300">ARIMA Rolling Origin (95% CI)</div>
            </div>
        </div>
    </div>
</section>

<!-- Interactive Live Sandbox (Photo 3: dscr_loans_chart.jpg as ambient texture) -->
<section id="sandbox" class="py-20 relative">
    <div class="absolute inset-0 z-0 opacity-15 pointer-events-none">
        <img src="/static/images/dscr_loans_chart.jpg" alt="DSCR Chart Ambient" class="w-full h-full object-cover object-center filter blur-sm">
        <div class="absolute inset-0 bg-[#030712]/90"></div>
    </div>

    <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div class="glass-panel-glow p-8 rounded-3xl border border-cyan-500/30">
            <div class="text-center max-w-xl mx-auto mb-8">
                <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 text-xs font-mono mb-2">
                    <i data-lucide="sliders" class="w-3.5 h-3.5"></i>
                    <span>{{ _('landing.sim_tag') }}</span>
                </div>
                <h3 class="text-2xl font-bold text-white">{{ _('landing.sim_title') }}</h3>
                <p class="text-xs text-slate-400 mt-1">{{ _('landing.sim_desc') }}</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                <!-- Sliders -->
                <div class="space-y-6">
                    <div>
                        <div class="flex justify-between text-xs font-semibold text-slate-300 mb-2">
                            <span>{{ _('landing.sim_monthly_noi') }}</span>
                            <span id="slider-noi-label" class="text-cyan-400 font-mono">৳ 250,000</span>
                        </div>
                        <input type="range" id="slider-noi" min="50000" max="1000000" step="10000" value="250000" class="w-full accent-cyan-400 cursor-pointer" oninput="updateLandingSandbox()">
                    </div>

                    <div>
                        <div class="flex justify-between text-xs font-semibold text-slate-300 mb-2">
                            <span>{{ _('landing.sim_requested_principal') }}</span>
                            <span id="slider-principal-label" class="text-cyan-400 font-mono">৳ 800,000</span>
                        </div>
                        <input type="range" id="slider-principal" min="100000" max="5000000" step="50000" value="800000" class="w-full accent-cyan-400 cursor-pointer" oninput="updateLandingSandbox()">
                    </div>

                    <div>
                        <div class="flex justify-between text-xs font-semibold text-slate-300 mb-2">
                            <span>{{ _('landing.sim_loan_tenure') }}</span>
                            <span id="slider-tenure-label" class="text-cyan-400 font-mono">24 {{ _('landing.sim_tenure_months') }}</span>
                        </div>
                        <input type="range" id="slider-tenure" min="6" max="60" step="6" value="24" class="w-full accent-cyan-400 cursor-pointer" oninput="updateLandingSandbox()">
                    </div>
                </div>

                <!-- Live Results Gauge -->
                <div class="glass-panel p-6 rounded-2xl border border-white/10 text-center space-y-4">
                    <div class="text-xs font-mono text-slate-400 uppercase tracking-widest">{{ _('landing.sim_estimated_emi') }}</div>
                    <div id="sandbox-emi" class="font-orbitron text-3xl font-extrabold text-white">৳ 37,458</div>
                    
                    <div class="pt-3 border-t border-white/10">
                        <div class="text-xs font-mono text-slate-400 uppercase tracking-widest">{{ _('landing.sim_dscr_label') }}</div>
                        <div id="sandbox-dscr" class="font-orbitron text-3xl font-extrabold text-emerald-400 mt-1">6.67x</div>
                    </div>

                    <div id="sandbox-verdict" class="py-2 px-4 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-bold">
                        {{ _('landing.sim_prime_verdict') }}
                    </div>

                    <a href="/app/loans" class="block w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs font-semibold border border-cyan-500/30 transition-all">
                        {{ _('landing.sim_compare_btn') }}
                    </a>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Customers & CRM Overdue Dues Chase Section -->
<section id="crm-receivables" class="py-20 border-t border-white/5 bg-[#02050f] relative">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div class="text-center max-w-3xl mx-auto">
            <h2 class="text-xs font-bold font-mono tracking-widest uppercase text-amber-400 mb-2">Automated Cash Acceleration</h2>
            <p class="text-3xl font-extrabold text-white">{{ _('landing.feat_crm_title') }}</p>
            <p class="mt-3 text-slate-400 text-sm">{{ _('landing.feat_crm_desc') }}</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="glass-panel p-6 rounded-3xl border border-white/10 space-y-3">
                <div class="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                    <i data-lucide="users" class="w-5 h-5"></i>
                </div>
                <h4 class="text-sm font-bold text-white">4-Tier RFM Segmentation</h4>
                <p class="text-slate-400 text-xs leading-relaxed">
                    Classifies retail accounts into Champions, Loyal Customers, At Risk, and Hibernating to target follow-ups effectively.
                </p>
            </div>
            <div class="glass-panel p-6 rounded-3xl border border-white/10 space-y-3">
                <div class="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                    <i data-lucide="message-square" class="w-5 h-5"></i>
                </div>
                <h4 class="text-sm font-bold text-white">WhatsApp & SMS Chase</h4>
                <p class="text-slate-400 text-xs leading-relaxed">
                    1-click individualized payment reminder drafts sent via actual messaging channels with consent management.
                </p>
            </div>
            <div class="glass-panel p-6 rounded-3xl border border-white/10 space-y-3">
                <div class="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                    <i data-lucide="percent" class="w-5 h-5"></i>
                </div>
                <h4 class="text-sm font-bold text-white">Margin-Guarded Discounts</h4>
                <p class="text-slate-400 text-xs leading-relaxed">
                    Personalized offers are mathematically bounded by minimum margin guardrails, strictly preventing sales below cost.
                </p>
            </div>
        </div>
    </div>
</section>

<!-- Inventory Valuation & Stock Aging Section -->
<section id="inventory-supply" class="py-20 border-t border-white/5 relative">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div class="text-center max-w-3xl mx-auto">
            <h2 class="text-xs font-bold font-mono tracking-widest uppercase text-indigo-400 mb-2">Supply Chain Liquidity</h2>
            <p class="text-3xl font-extrabold text-white">{{ _('landing.feat_inv_title') }}</p>
            <p class="mt-3 text-slate-400 text-sm">{{ _('landing.feat_inv_desc') }}</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="glass-panel p-5 rounded-2xl border border-white/10 space-y-2">
                <span class="text-xs font-mono text-emerald-400 block font-bold">0-30 Days (Fresh)</span>
                <span class="text-lg font-bold text-white">Active Fast-Turnover</span>
                <p class="text-[11px] text-slate-400">Peak gross margins and rapid working capital conversion velocity.</p>
            </div>
            <div class="glass-panel p-5 rounded-2xl border border-white/10 space-y-2">
                <span class="text-xs font-mono text-cyan-400 block font-bold">31-60 Days (Normal)</span>
                <span class="text-lg font-bold text-white">Standard Stock</span>
                <p class="text-[11px] text-slate-400">Regular supplier reorder cycles monitored by automated minimum buffers.</p>
            </div>
            <div class="glass-panel p-5 rounded-2xl border border-white/10 space-y-2">
                <span class="text-xs font-mono text-amber-400 block font-bold">61-90 Days (Aging)</span>
                <span class="text-lg font-bold text-white">Slow-Moving SKUs</span>
                <p class="text-[11px] text-slate-400">Targeted discount campaigns automatically drafted to clear capital.</p>
            </div>
            <div class="glass-panel p-5 rounded-2xl border border-white/10 space-y-2">
                <span class="text-xs font-mono text-rose-400 block font-bold">90+ Days (Dead Stock)</span>
                <span class="text-lg font-bold text-white">Liquidation Priority</span>
                <p class="text-[11px] text-slate-400">Immediate write-down prevention alerts and supplier return workflows.</p>
            </div>
        </div>
    </div>
</section>

<!-- AI Model Baselines & Animated Visual Assets -->
<section id="models" class="py-20 border-t border-white/5 bg-slate-950/60 relative">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-3xl mx-auto mb-16">
            <h2 class="text-xs font-bold font-mono tracking-widest uppercase text-emerald-400 mb-2">{{ _('landing.models_tag') }}</h2>
            <p class="text-3xl font-extrabold text-white">{{ _('landing.models_title') }}</p>
            <p class="mt-3 text-slate-400 text-sm">{{ _('landing.models_desc') }}</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div class="glass-panel p-5 rounded-3xl border border-white/5 space-y-3">
                <div class="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
                    <i data-lucide="line-chart" class="w-5 h-5"></i>
                </div>
                <h4 class="text-sm font-bold text-white">ARIMA(1,1,1)</h4>
                <div class="text-xs text-emerald-400 font-mono font-bold">MASE: 0.42</div>
                <p class="text-slate-400 text-xs leading-relaxed">{{ _('landing.model1_desc') }}</p>
            </div>

            <div class="glass-panel p-5 rounded-3xl border border-white/5 space-y-3">
                <div class="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                    <i data-lucide="cpu" class="w-5 h-5"></i>
                </div>
                <h4 class="text-sm font-bold text-white">LightGBM GBDT</h4>
                <div class="text-xs text-emerald-400 font-mono font-bold">WAPE: 0.12 • R²: 0.91</div>
                <p class="text-slate-400 text-xs leading-relaxed">{{ _('landing.model2_desc') }}</p>
            </div>

            <div class="glass-panel p-5 rounded-3xl border border-white/5 space-y-3">
                <div class="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                    <i data-lucide="file-text" class="w-5 h-5"></i>
                </div>
                <h4 class="text-sm font-bold text-white">{{ _('landing.model3_title') }}</h4>
                <div class="text-xs text-indigo-300 font-mono font-bold">Accuracy: 98.6%</div>
                <p class="text-slate-400 text-xs leading-relaxed">{{ _('landing.model3_desc') }}</p>
            </div>

            <div class="glass-panel p-5 rounded-3xl border border-white/5 space-y-3">
                <div class="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                    <i data-lucide="shield" class="w-5 h-5"></i>
                </div>
                <h4 class="text-sm font-bold text-white">{{ _('landing.model4_title') }}</h4>
                <div class="text-xs text-amber-300 font-mono font-bold">12/12 Stress Vectors</div>
                <p class="text-slate-400 text-xs leading-relaxed">{{ _('landing.model4_desc') }}</p>
            </div>
        </div>

        <!-- Animated SVG Preloader Showcase -->
        <div class="mt-12 glass-panel p-6 rounded-3xl border border-white/10 flex flex-col md:flex-row items-center justify-between gap-6">
            <div class="flex items-center gap-5">
                <img src="/static/images/preloader_badge.svg" alt="Preloader Badge" class="w-16 h-16 drop-shadow-[0_0_15px_rgba(34,211,238,0.4)]">
                <div>
                    <h4 class="text-sm font-bold text-white flex items-center gap-2">
                        <span>{{ _('landing.preloader_title') }}</span>
                        <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300">SVG Animated</span>
                    </h4>
                    <p class="text-xs text-slate-400 mt-1">{{ _('landing.preloader_desc') }}</p>
                </div>
            </div>

            <div class="flex items-center gap-4">
                <img src="/static/images/preloader_scanner.svg" alt="Preloader Scanner" class="h-12 w-auto opacity-80 hover:opacity-100 transition-opacity">
                <img src="/static/images/preloader.svg" alt="Preloader Flow" class="h-12 w-auto opacity-80 hover:opacity-100 transition-opacity">
            </div>
        </div>
    </div>
</section>

<!-- Security, Privacy & Audit -->
<section id="security" class="py-20 border-t border-white/5 relative">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center max-w-3xl mx-auto mb-16">
            <h2 class="text-xs font-bold font-mono tracking-widest uppercase text-cyan-400 mb-2">{{ _('landing.security_tag') }}</h2>
            <p class="text-3xl font-extrabold text-white">{{ _('landing.security_title') }}</p>
            <p class="mt-3 text-slate-400 text-sm">{{ _('landing.security_desc') }}</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="glass-panel p-6 rounded-3xl border border-white/5 space-y-3">
                <div class="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                    <i data-lucide="lock" class="w-5 h-5"></i>
                </div>
                <h4 class="text-sm font-bold text-white">{{ _('landing.sec1_title') }}</h4>
                <p class="text-slate-400 text-xs leading-relaxed">{{ _('landing.sec1_desc') }}</p>
            </div>

            <div class="glass-panel p-6 rounded-3xl border border-white/5 space-y-3">
                <div class="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
                    <i data-lucide="file-check" class="w-5 h-5"></i>
                </div>
                <h4 class="text-sm font-bold text-white">{{ _('landing.sec2_title') }}</h4>
                <p class="text-slate-400 text-xs leading-relaxed">{{ _('landing.sec2_desc') }}</p>
            </div>

            <div class="glass-panel p-6 rounded-3xl border border-white/5 space-y-3">
                <div class="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                    <i data-lucide="database" class="w-5 h-5"></i>
                </div>
                <h4 class="text-sm font-bold text-white">{{ _('landing.sec3_title') }}</h4>
                <p class="text-slate-400 text-xs leading-relaxed">{{ _('landing.sec3_desc') }}</p>
            </div>
        </div>
    </div>
</section>

<!-- Master 5-Column Enterprise Application Footer -->
<footer class="border-t border-white/10 bg-[#02050e] pt-16 pb-12 text-slate-400 text-xs relative z-20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
            <!-- Col 1: Brand & Autonomous Telemetry -->
            <div class="space-y-4 lg:col-span-1">
                <a href="/landing" class="flex items-center gap-2.5">
                    <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-emerald-400 p-[1px]">
                        <div class="w-full h-full bg-[#080e1e] rounded-[7px] flex items-center justify-center">
                            <i data-lucide="sparkles" class="w-4 h-4 text-cyan-400"></i>
                        </div>
                    </div>
                    <span class="font-orbitron font-bold text-white text-sm">SME<span class="text-cyan-400">FINANCE</span></span>
                </a>
                <p class="text-[11px] text-slate-400 leading-relaxed">
                    {{ _('landing.footer_built_for') }}
                </p>
                <div class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-[10px] font-mono">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span>Zero-Loss SQLite WAL Engine</span>
                </div>
            </div>

            <!-- Col 2: Platform Capabilities -->
            <div class="space-y-3">
                <div class="text-white font-bold uppercase tracking-wider text-[11px] font-mono">{{ _('landing.footer_platform') }}</div>
                <ul class="space-y-2 text-[11.5px]">
                    <li><a href="#features" class="hover:text-cyan-400 transition-colors">Cash Runway Forecast</a></li>
                    <li><a href="#features" class="hover:text-cyan-400 transition-colors">Gated Multilingual OCR</a></li>
                    <li><a href="#sandbox" class="hover:text-cyan-400 transition-colors">SME Loan & DSCR Evaluator</a></li>
                    <li><a href="#crm-receivables" class="hover:text-cyan-400 transition-colors">CRM Receivables Recovery</a></li>
                    <li><a href="#inventory-supply" class="hover:text-cyan-400 transition-colors">Inventory Aging & POs</a></li>
                    <li><a href="/app/copilot" class="hover:text-cyan-400 transition-colors">Autonomous Voice AI</a></li>
                </ul>
            </div>

            <!-- Col 3: Core Application Portals -->
            <div class="space-y-3">
                <div class="text-white font-bold uppercase tracking-wider text-[11px] font-mono">{{ _('landing.footer_apps') }}</div>
                <ul class="space-y-2 text-[11.5px]">
                    <li><a href="/app/dashboard" class="hover:text-cyan-400 transition-colors">Executive Dashboard</a></li>
                    <li><a href="/app/finance" class="hover:text-cyan-400 transition-colors">P&L Ledgers & Cash Flow</a></li>
                    <li><a href="/app/forecast" class="hover:text-cyan-400 transition-colors">Cash Forecast Engine</a></li>
                    <li><a href="/app/documents" class="hover:text-cyan-400 transition-colors">Document Capture & OCR</a></li>
                    <li><a href="/app/loans" class="hover:text-cyan-400 transition-colors">SME Loan Financing</a></li>
                    <li><a href="/app/customers" class="hover:text-cyan-400 transition-colors">Customers & Overdue Dues</a></li>
                    <li><a href="/app/inventory" class="hover:text-cyan-400 transition-colors">SKU Inventory & Movements</a></li>
                    <li><a href="/app/admin" class="hover:text-rose-400 transition-colors">Super Admin Console</a></li>
                </ul>
            </div>

            <!-- Col 4: Compliance & Financial Math -->
            <div class="space-y-3">
                <div class="text-white font-bold uppercase tracking-wider text-[11px] font-mono">{{ _('landing.footer_compliance') }}</div>
                <ul class="space-y-2 text-[11.5px]">
                    <li class="flex items-center gap-1.5"><i data-lucide="check" class="w-3.5 h-3.5 text-cyan-400"></i><span>GAAP / IFRS Principles</span></li>
                    <li class="flex items-center gap-1.5"><i data-lucide="check" class="w-3.5 h-3.5 text-cyan-400"></i><span>Integer Minor Units Math</span></li>
                    <li class="flex items-center gap-1.5"><i data-lucide="check" class="w-3.5 h-3.5 text-cyan-400"></i><span>HMAC Cryptographic Tokens</span></li>
                    <li class="flex items-center gap-1.5"><i data-lucide="check" class="w-3.5 h-3.5 text-cyan-400"></i><span>Immutable Audit Triggers</span></li>
                    <li class="flex items-center gap-1.5"><i data-lucide="check" class="w-3.5 h-3.5 text-cyan-400"></i><span>Multi-Tenant Shop Isolation</span></li>
                    <li class="flex items-center gap-1.5"><i data-lucide="check" class="w-3.5 h-3.5 text-cyan-400"></i><span>Zero Float Rounding Error</span></li>
                </ul>
            </div>

            <!-- Col 5: Developer & Regional Coverage -->
            <div class="space-y-3">
                <div class="text-white font-bold uppercase tracking-wider text-[11px] font-mono">{{ _('landing.footer_developers') }}</div>
                <ul class="space-y-2 text-[11.5px]">
                    <li><a href="/docs" target="_blank" class="hover:text-cyan-400 transition-colors flex items-center gap-1 font-mono"><span>FastAPI Swagger Docs</span><i data-lucide="external-link" class="w-3 h-3 text-slate-500"></i></a></li>
                    <li><a href="/health" target="_blank" class="hover:text-cyan-400 transition-colors flex items-center gap-1 font-mono"><span>Health Telemetry API</span><i data-lucide="external-link" class="w-3 h-3 text-slate-500"></i></a></li>
                    <li><a href="/login" class="hover:text-cyan-400 transition-colors">1-Click Evaluation Personas</a></li>
                    <li><span class="text-slate-300">🇧🇩 Bangladesh (BDT ৳ • Mushak)</span></li>
                    <li><span class="text-slate-300">🇨🇳 China (CNY ¥ • Fapiao)</span></li>
                    <li><span class="text-slate-300">🌐 Global (USD $ • EUR € • GBP £)</span></li>
                </ul>
            </div>
        </div>

        <!-- Bottom Sub-Footer Bar -->
        <div class="border-t border-white/10 pt-8 flex flex-col md:flex-row items-center justify-between gap-4 text-[11px] text-slate-500">
            <div class="flex items-center gap-3">
                <span>&copy; 2026 SME Finance Copilot. {{ _('landing.footer_rights') }}</span>
                <span>•</span>
                <span class="font-mono text-cyan-400">Version 0.1.0 • Antigravity Competition Build</span>
            </div>
            <div class="flex items-center gap-6">
                <a href="/landing" class="hover:text-slate-300 transition-colors">Home</a>
                <a href="/how-it-works" class="hover:text-slate-300 transition-colors">Operator Guide</a>
                <a href="/login" class="hover:text-slate-300 transition-colors">Sign In</a>
                <a href="/app/dashboard" class="text-cyan-400 hover:underline">App Portal</a>
            </div>
        </div>
    </div>
</footer>

<script>
window.CURRENT_LOCALE = "{{ current_lang or 'en' }}";
window.CURRENT_CURRENCY = "{{ current_currency or (business.currency if business else 'BDT') }}";
window.TRANSLATIONS = {{ translations_json | safe if translations_json else '{}' }};

window.t = function(key, fallback) {
    if (!key) return fallback || '';
    const parts = key.split('.');
    let curr = window.TRANSLATIONS;
    for (const p of parts) {
        if (curr && typeof curr === 'object' && p in curr) {
            curr = curr[p];
        } else {
            return fallback || key;
        }
    }
    return typeof curr === 'string' ? curr : (fallback || key);
};

async function changeLandingLanguage(newLang) {
    document.cookie = `sme_lang=${newLang}; path=/; max-age=31536000; SameSite=Lax`;
    try {
        const token = localStorage.getItem('sme_token') || '{{ current_user.token if current_user else "" }}';
        await fetch('/api/i18n/set-language', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': token ? `Bearer ${token}` : ''
            },
            body: JSON.stringify({ locale: newLang })
        });
    } catch (e) {
        console.warn('Could not persist language via API:', e);
    }
    const url = new URL(window.location.href);
    url.searchParams.set('lang', newLang);
    window.location.href = url.toString();
}
window.changeLandingLanguage = changeLandingLanguage;

function updateLandingSandbox() {
    const noi = parseFloat(document.getElementById('slider-noi').value);
    const principal = parseFloat(document.getElementById('slider-principal').value);
    const tenure = parseInt(document.getElementById('slider-tenure').value);
    const annualRate = 0.115; // 11.5% BRAC SME base

    const curr = window.CURRENT_CURRENCY || 'BDT';
    const symMap = { 'BDT': '৳', 'CNY': '¥', 'USD': '$', 'EUR': '€', 'GBP': '£' };
    const sym = symMap[curr] || curr;
    const monthsText = window.t('landing.sim_tenure_months', 'Months');

    document.getElementById('slider-noi-label').innerText = sym + ' ' + noi.toLocaleString();
    document.getElementById('slider-principal-label').innerText = sym + ' ' + principal.toLocaleString();
    document.getElementById('slider-tenure-label').innerText = tenure + ' ' + monthsText;

    // Reducing balance EMI calculation
    const monthlyRate = annualRate / 12;
    const emi = (principal * monthlyRate * Math.pow(1 + monthlyRate, tenure)) / (Math.pow(1 + monthlyRate, tenure) - 1);
    const dscr = noi / emi;

    document.getElementById('sandbox-emi').innerText = sym + ' ' + Math.round(emi).toLocaleString();
    document.getElementById('sandbox-dscr').innerText = dscr.toFixed(2) + 'x';

    const verdictEl = document.getElementById('sandbox-verdict');
    if (dscr >= 1.5) {
        verdictEl.className = 'py-2 px-4 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-bold';
        verdictEl.innerText = window.t('landing.sim_prime_verdict', '✓ Prime Bank Quality — High Approval Probability');
        document.getElementById('sandbox-dscr').className = 'font-orbitron text-3xl font-extrabold text-emerald-400 mt-1';
    } else if (dscr >= 1.2) {
        verdictEl.className = 'py-2 px-4 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-300 text-xs font-bold';
        verdictEl.innerText = window.t('landing.sim_tight_verdict', '⚠ Moderate Risk — Collateral or Working Capital Boost Recommended');
        document.getElementById('sandbox-dscr').className = 'font-orbitron text-3xl font-extrabold text-amber-400 mt-1';
    } else {
        verdictEl.className = 'py-2 px-4 rounded-xl bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs font-bold';
        verdictEl.innerText = window.t('landing.sim_risk_verdict', '✕ High Debt Risk — EMI Exceeds Operating Cash Buffer');
        document.getElementById('sandbox-dscr').className = 'font-orbitron text-3xl font-extrabold text-rose-400 mt-1';
    }
}

// Background Hero Video Play/Pause & Accessibility Handler
function toggleHeroVideo() {
    const video = document.getElementById('hero-bg-video');
    const icon = document.getElementById('hero-video-toggle-icon');
    const label = document.getElementById('hero-video-toggle-label');
    if (!video) return;

    if (video.paused) {
        video.play().then(() => {
            if (icon) icon.setAttribute('data-lucide', 'pause');
            if (label) label.textContent = window.t('landing.video_active', 'Video Active');
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }).catch(err => {
            console.warn('Hero video play prevented:', err);
        });
    } else {
        video.pause();
        if (icon) icon.setAttribute('data-lucide', 'play');
        if (label) label.textContent = window.t('landing.video_paused', 'Video Paused');
        if (typeof lucide !== 'undefined') lucide.createIcons();
    }
}
window.toggleHeroVideo = toggleHeroVideo;

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Sandbox calculation
    if (typeof updateLandingSandbox === 'function') {
        updateLandingSandbox();
    }

    // 2. Background Video Event Synchronization & Robust Autoplay
    const video = document.getElementById('hero-bg-video');
    const icon = document.getElementById('hero-video-toggle-icon');
    const label = document.getElementById('hero-video-toggle-label');
    if (video) {
        video.muted = true;
        video.defaultMuted = true;

        const startAutoplay = () => {
            const playPromise = video.play();
            if (playPromise !== undefined) {
                playPromise.then(() => {
                    if (icon) icon.setAttribute('data-lucide', 'pause');
                    if (label) label.textContent = window.t('landing.video_active', 'Video Active');
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                }).catch(err => {
                    console.log('Autoplay deferred, awaiting user touch/click:', err);
                });
            }
        };

        video.addEventListener('play', () => {
            if (icon) icon.setAttribute('data-lucide', 'pause');
            if (label) label.textContent = window.t('landing.video_active', 'Video Active');
            if (typeof lucide !== 'undefined') lucide.createIcons();
        });
        video.addEventListener('pause', () => {
            if (icon) icon.setAttribute('data-lucide', 'play');
            if (label) label.textContent = window.t('landing.video_paused', 'Video Paused');
            if (typeof lucide !== 'undefined') lucide.createIcons();
        });

        // Trigger playback immediately
        startAutoplay();
        video.addEventListener('canplay', startAutoplay, { once: true });
        video.addEventListener('loadeddata', startAutoplay, { once: true });

        // First interaction fallback in case browser policy is strictly demanding user gesture
        const onFirstInteraction = () => {
            if (video.paused) {
                startAutoplay();
            }
            window.removeEventListener('click', onFirstInteraction);
            window.removeEventListener('touchstart', onFirstInteraction);
            window.removeEventListener('scroll', onFirstInteraction);
        };
        window.addEventListener('click', onFirstInteraction, { passive: true, once: true });
        window.addEventListener('touchstart', onFirstInteraction, { passive: true, once: true });
        window.addEventListener('scroll', onFirstInteraction, { passive: true, once: true });
    }
});
</script>
{% endblock %}
"""

final_text = top_part + new_bottom_part
landing_path.write_text(final_text, encoding="utf-8")
print("SUCCESS: Enriched landing.html while keeping 1st page untouched.")
