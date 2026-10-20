path = r'F:\china project\src\web\templates\how_it_works.html'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

phase5_6 = '''
            <!-- Phase 5: Balance Sheet Audit & Compliance Integrity -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
                <div class="space-y-4">
                    <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 text-xs font-mono">
                        <i data-lucide="scale" class="w-3.5 h-3.5"></i>
                        <span>Phase 05 • Balance Sheet Audit</span>
                    </div>
                    <h3 class="text-2xl sm:text-3xl font-extrabold text-white">
                        Immutable Ledger &amp; Statutory Audit Verification
                    </h3>
                    <p class="text-sm text-slate-300 leading-relaxed">
                        Every ledger entry is anchored by cryptographic checksums and immutable audit logging. Whether preparing tax filings under Chinese VAT or Bangladesh NBR regulations, the balance sheet remains mathematically verified with zero float errors.
                    </p>
                    <div class="p-4 rounded-2xl bg-cyan-950/30 border border-cyan-500/30 space-y-2">
                        <h5 class="text-xs font-bold text-cyan-300 flex items-center gap-2">
                            <i data-lucide="shield-check" class="w-4 h-4"></i>
                            <span>Zero-Loss SQLite WAL Mode</span>
                        </h5>
                        <p class="text-xs text-slate-300">
                            ACID compliance with write-ahead logging guarantees no transaction loss during power cuts or network drops across all retail store branches.
                        </p>
                    </div>
                </div>
                <div class="relative rounded-3xl overflow-hidden border border-cyan-500/30 shadow-2xl">
                    <img src="/static/images/balance_scale_audit.jpg" alt="Balance Sheet Audit and Compliance" class="w-full h-80 object-cover object-center filter brightness-95 contrast-105">
                    <div class="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/30 to-transparent flex items-end p-6">
                        <span class="text-xs font-mono text-cyan-300 bg-slate-900/90 px-3 py-1 rounded-full border border-cyan-500/40">Automated GAAP / IFRS Balance Reconciliation</span>
                    </div>
                </div>
            </div>

            <!-- Phase 6: Autonomous AI Financial Copilot & Live Decision Cockpit -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
                <div class="order-2 lg:order-1 relative rounded-3xl overflow-hidden border border-emerald-500/30 shadow-2xl">
                    <img src="/static/images/cfo_cockpit_terminal.jpg" alt="Autonomous Financial Decision Cockpit" class="w-full h-80 object-cover object-center filter brightness-95 contrast-110">
                    <div class="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/30 to-transparent flex items-end p-6">
                        <span class="text-xs font-mono text-emerald-300 bg-slate-900/90 px-3 py-1 rounded-full border border-emerald-500/40">Multi-Channel Voice AI &amp; Real-Time Financial Advisory</span>
                    </div>
                </div>
                <div class="order-1 lg:order-2 space-y-4">
                    <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-mono">
                        <i data-lucide="bot" class="w-3.5 h-3.5"></i>
                        <span>Phase 06 • Autonomous Copilot</span>
                    </div>
                    <h3 class="text-2xl sm:text-3xl font-extrabold text-white">
                        Autonomous Voice &amp; Text Financial Copilot
                    </h3>
                    <p class="text-sm text-slate-300 leading-relaxed">
                        Ask your financial copilot questions in English, Chinese (中文), or Bengali (বাংলা). From querying today's cash velocity to simulating interest rate hikes, your copilot provides instantaneous, grounded answers.
                    </p>
                    <div class="grid grid-cols-2 gap-3">
                        <div class="p-3.5 rounded-xl bg-slate-900/90 border border-white/10">
                            <span class="text-xs font-bold text-white block flex items-center gap-1.5">
                                <i data-lucide="mic" class="w-3.5 h-3.5 text-cyan-400"></i>
                                Multilingual Voice AI
                            </span>
                            <span class="text-[11px] text-slate-400 mt-1 block">Full browser speech synthesis &amp; recognition across 3 languages</span>
                        </div>
                        <div class="p-3.5 rounded-xl bg-slate-900/90 border border-white/10">
                            <span class="text-xs font-bold text-white block flex items-center gap-1.5">
                                <i data-lucide="zap" class="w-3.5 h-3.5 text-emerald-400"></i>
                                Instant Simulation
                            </span>
                            <span class="text-[11px] text-slate-400 mt-1 block">Real-time what-if stress tests without writing complex Excel formulas</span>
                        </div>
                    </div>
                </div>
            </div>
'''

target_str = '</div>\r\n            </div>\r\n        </div>\r\n\r\n        <!-- Section 5: High-Impact Call to Action Banner -->'
if target_str not in c:
    target_str = '</div>\n            </div>\n        </div>\n\n        <!-- Section 5: High-Impact Call to Action Banner -->'

replacement = '</div>\n            </div>' + phase5_6 + '\n        </div>\n\n        <!-- Section 5: High-Impact Call to Action Banner -->'
c = c.replace(target_str, replacement, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('Successfully inserted Phase 5 and 6 into how_it_works.html')
