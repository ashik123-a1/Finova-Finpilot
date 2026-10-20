from pathlib import Path

login_path = Path("F:/china project/src/web/templates/login.html")
content = login_path.read_text(encoding="utf-8")

# Target snippet starting from <!-- Separation for Competition Demo Evaluation --> up to end of login card and bottom clutter
old_block = """            <!-- Separation for Competition Demo Evaluation -->
            <div class="pt-2">
                <div class="flex items-center my-3">
                    <div class="flex-1 border-t border-white/10"></div>
                    <span class="px-3 text-[10px] font-mono text-slate-500 uppercase">Evaluation & Demonstration</span>
                    <div class="flex-1 border-t border-white/10"></div>
                </div>

                <button type="button" onclick="openDemoModal()" class="w-full py-2.5 rounded-xl border border-cyan-500/40 hover:border-cyan-400 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 font-semibold text-xs transition-all flex items-center justify-center gap-2 shadow-lg shadow-cyan-950/40">
                    <i data-lucide="sparkles" class="w-4 h-4 text-cyan-400"></i>
                    <span>1-Click Quick Demo Login (Evaluation Personas)</span>
                </button>
            </div>
        </div>

        <!-- Prominent Create Account Section -->
        <div class="mt-4 space-y-2 text-center">
            <a href="/register" class="w-full py-2.5 rounded-xl border border-white/20 hover:border-cyan-400 bg-slate-900/80 hover:bg-slate-800 text-slate-200 hover:text-white font-semibold text-xs flex items-center justify-center gap-2 transition-all shadow-md">
                <i data-lucide="user-plus" class="w-4 h-4 text-cyan-400"></i>
                <span>Create New Business Account</span>
            </a>
            <p class="text-[11px] text-slate-400">
                New enterprise or merchant? 
                <a href="/register" class="text-cyan-400 hover:underline font-semibold ml-1">Register & Launch Onboarding Wizard</a>
            </p>
        </div>

        <!-- Privacy & Terms -->
        <p class="text-center text-[10px] text-slate-600 mt-3">
            Protected by multi-tenant SQLite WAL isolation & HMAC token validation.
        </p>
    </div>
</div>"""

new_block = """            <!-- Separation for Quick Demo Entry -->
            <div class="pt-2">
                <div class="relative my-4">
                    <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-white/10"></div></div>
                    <div class="relative flex justify-center text-xs uppercase"><span class="bg-[#0b1329] px-3.5 text-slate-400 font-mono tracking-wider text-[10.5px]">1-Click Quick Demo Entry</span></div>
                </div>

                <!-- Two Dedicated One-Click Role Cards: Store Owner and Platform Admin (LandGuard Benchmark) -->
                <div class="space-y-2.5">
                    <!-- 1. Continue as Demo Store Owner -->
                    <button type="button" id="demo-btn-owner" onclick="loginWithDemoPersona('owner')"
                            class="w-full text-left p-3.5 rounded-2xl border border-cyan-500/40 hover:border-cyan-400 bg-slate-900/90 hover:bg-slate-800/90 transition-all flex items-center justify-between group shadow-lg shadow-cyan-950/40 cursor-pointer">
                        <div class="flex items-center gap-3.5 min-w-0">
                            <div class="w-10 h-10 rounded-xl bg-cyan-950 border border-cyan-500/40 flex items-center justify-center text-cyan-400 group-hover:bg-cyan-400 group-hover:text-slate-950 transition-colors shrink-0">
                                <i data-lucide="crown" class="w-5 h-5"></i>
                            </div>
                            <div class="truncate">
                                <div class="text-xs sm:text-sm font-bold text-white group-hover:text-cyan-300 flex items-center gap-2 truncate">
                                    <span>Continue as Demo Store Owner</span>
                                    <span class="text-[9.5px] px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/60 font-mono font-medium">demo_owner</span>
                                </div>
                                <div class="text-[11px] text-slate-400 truncate mt-0.5">Full control • P&L Ledgers, POS, Loans & AI Copilot</div>
                            </div>
                        </div>
                        <div class="flex items-center gap-1.5 shrink-0 ml-2">
                            <div id="demo-spinner-owner" class="hidden w-4 h-4 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
                            <i data-lucide="chevron-right" class="w-4 h-4 text-slate-400 group-hover:text-cyan-400 group-hover:translate-x-0.5 transition-transform"></i>
                        </div>
                    </button>

                    <!-- 2. Continue as Demo Admin -->
                    <button type="button" id="demo-btn-admin" onclick="loginWithDemoPersona('super_admin')"
                            class="w-full text-left p-3.5 rounded-2xl border border-rose-500/30 hover:border-rose-400 bg-slate-900/90 hover:bg-slate-800/90 transition-all flex items-center justify-between group shadow-lg shadow-rose-950/40 cursor-pointer">
                        <div class="flex items-center gap-3.5 min-w-0">
                            <div class="w-10 h-10 rounded-xl bg-rose-950/60 border border-rose-500/40 flex items-center justify-center text-rose-400 group-hover:bg-rose-500 group-hover:text-white transition-colors shrink-0">
                                <i data-lucide="shield-check" class="w-5 h-5"></i>
                            </div>
                            <div class="truncate">
                                <div class="text-xs sm:text-sm font-bold text-white group-hover:text-rose-300 flex items-center gap-2 truncate">
                                    <span>Continue as Demo Admin</span>
                                    <span class="text-[9.5px] px-1.5 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800/60 font-mono font-medium">super_admin</span>
                                </div>
                                <div class="text-[11px] text-slate-400 truncate mt-0.5">Platform Super Admin • Multi-Tenant & Platform Governance</div>
                            </div>
                        </div>
                        <div class="flex items-center gap-1.5 shrink-0 ml-2">
                            <div id="demo-spinner-admin" class="hidden w-4 h-4 border-2 border-rose-400 border-t-transparent rounded-full animate-spin"></div>
                            <i data-lucide="chevron-right" class="w-4 h-4 text-slate-400 group-hover:text-rose-400 group-hover:translate-x-0.5 transition-transform"></i>
                        </div>
                    </button>
                </div>

                <!-- Subtle More Personas Trigger -->
                <div class="mt-3 text-center">
                    <button type="button" onclick="openDemoModal()" class="text-[11px] text-slate-400 hover:text-cyan-300 font-mono transition-colors inline-flex items-center gap-1.5">
                        <i data-lucide="sliders" class="w-3.5 h-3.5 text-cyan-400"></i>
                        <span>Explore Other Personas (Manager, Accountant, Sales, Auditor)</span>
                    </button>
                </div>
            </div>
        </div>

        <!-- Back to Home Button (High-Contrast Cyber Glass Pill - LandGuard Benchmark) -->
        <div class="text-center mt-6">
            <a href="/landing" class="inline-flex items-center gap-2.5 px-6 py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-cyan-300 hover:text-white bg-slate-900/95 hover:bg-slate-800/95 border border-cyan-500/50 hover:border-cyan-300 shadow-xl shadow-cyan-950/40 backdrop-blur-md transition-all group hover:scale-[1.02]">
                <i data-lucide="arrow-left" class="w-4 h-4 text-cyan-400 group-hover:-translate-x-1 transition-transform"></i>
                <span class="tracking-wide">Back to Home</span>
            </a>
        </div>

        <!-- Synthetic Demo Disclaimer Notice -->
        <div class="mt-4 text-center">
            <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-xl bg-slate-900/80 border border-amber-500/30 text-amber-300/80 text-[10.5px] font-mono shadow-md backdrop-blur-md">
                <i data-lucide="shield-alert" class="w-3.5 h-3.5 text-amber-400 shrink-0"></i>
                <span><strong>SYNTHETIC DEMO:</strong> Research Benchmark • Protected by Multi-Tenant SQLite WAL</span>
            </div>
        </div>
    </div>
</div>"""

# Normalize \r\n to \n for replacement
norm_content = content.replace("\r\n", "\n")
norm_old = old_block.replace("\r\n", "\n")
norm_new = new_block.replace("\r\n", "\n")

if norm_old in norm_content:
    updated = norm_content.replace(norm_old, norm_new, 1)
    login_path.write_text(updated, encoding="utf-8")
    print("SUCCESS: Updated login.html with Owner, Admin, and Back to Home buttons.")
else:
    print("ERROR: old_block not found in login.html")
