import re

def localize_finance():
    path = "src/web/templates/app/finance.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    replacements = [
        ('<div class="text-[10px] font-mono uppercase text-slate-400">Total Revenue</div>', '<div class="text-[10px] font-mono uppercase text-slate-400">{{ _(\'financial.revenue\') }}</div>'),
        ('<div class="text-[10px] text-emerald-400 mt-1">Gross Inflows</div>', '<div class="text-[10px] text-emerald-400 mt-1">{{ _(\'finance.gross_inflows\') }}</div>'),
        ('<div class="text-[10px] font-mono uppercase text-slate-400">COGS (Direct)</div>', '<div class="text-[10px] font-mono uppercase text-slate-400">{{ _(\'financial.cogs\') }}</div>'),
        ('<div class="text-[10px] text-slate-400 mt-1">Cost of Goods</div>', '<div class="text-[10px] text-slate-400 mt-1">{{ _(\'finance.cost_of_goods\') }}</div>'),
        ('<div class="text-[10px] font-mono uppercase text-slate-400">Gross Profit</div>', '<div class="text-[10px] font-mono uppercase text-slate-400">{{ _(\'financial.gross_profit\') }}</div>'),
        ('<div class="text-[10px] text-cyan-300 mt-1">40.0% Margin</div>', '<div class="text-[10px] text-cyan-300 mt-1">40.0% {{ _(\'finance.margin\') }}</div>'),
        ('<div class="text-[10px] font-mono uppercase text-slate-400">Operating Expenses</div>', '<div class="text-[10px] font-mono uppercase text-slate-400">{{ _(\'finance.operating_expenses\') }}</div>'),
        ('<div class="text-[10px] text-slate-400 mt-1">Rent, Utilities, Staff</div>', '<div class="text-[10px] text-slate-400 mt-1">{{ _(\'finance.operating_desc\') }}</div>'),
        ('<div class="text-[10px] font-mono uppercase text-slate-400">Net Operating Profit</div>', '<div class="text-[10px] font-mono uppercase text-slate-400">{{ _(\'financial.net_profit\') }}</div>'),
        ('<div class="text-[10px] text-emerald-300 mt-1">22.2% Net Margin</div>', '<div class="text-[10px] text-emerald-300 mt-1">22.2% {{ _(\'finance.net_margin\') }}</div>'),
        ('<div class="text-[10px] font-mono uppercase text-slate-400">Tax / VAT Provision</div>', '<div class="text-[10px] font-mono uppercase text-slate-400">{{ _(\'finance.vat_provision\') }}</div>'),
        ('<div class="text-[10px] text-amber-300 mt-1">NBR 5% Retail VAT</div>', '<div class="text-[10px] text-amber-300 mt-1">{{ _(\'finance.nbr_vat_desc\') }}</div>'),
        ('Sales Ledger\n            </button>', '{{ _(\'finance.sales_ledger\') }}\n            </button>'),
        ('Expense Ledger\n            </button>', '{{ _(\'finance.expense_ledger\') }}\n            </button>'),
        ('<span class="text-xs text-slate-500">to</span>', '<span class="text-xs text-slate-500">{{ _(\'finance.to\') }}</span>'),
        ('<span>Apply Filter</span>', '<span>{{ _(\'finance.apply_filter\') }}</span>'),
        ('<span>Export CSV</span>', '<span>{{ _(\'finance.export_csv\') }}</span>'),
        ('<h3 id="ledger-title" class="text-sm font-bold text-white">Verified Sales Records</h3>', '<h3 id="ledger-title" class="text-sm font-bold text-white">{{ _(\'finance.verified_sales_records\') }}</h3>'),
        ('Displaying Page 1', '{{ _(\'finance.displaying_page\') }} 1'),
        ('Loading verified ledger entries...', '{{ _(\'finance.loading_ledger\') }}'),
    ]

    for old, new in replacements:
        content = content.replace(old, new)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("finance.html localized!")

def localize_how_it_works():
    path = "src/web/templates/how_it_works.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    replacements = [
        ('{% block title %}How It Works — SME Finance Copilot Operator Guide{% endblock %}', '{% block title %}{{ _(\'how_it_works.page_title\') }}{% endblock %}'),
        ('<span>Return to Home</span>', '<span>{{ _(\'how_it_works.return_home\') }}</span>'),
        ('<span>Capabilities</span>', '<span>{{ _(\'how_it_works.capabilities\') }}</span>'),
        ('<span>Sandbox</span>', '<span>{{ _(\'how_it_works.sandbox\') }}</span>'),
        ('<span>Sign In</span>', '<span>{{ _(\'login.title\') }}</span>'),
        ('<span>App Portal</span>', '<span>{{ _(\'how_it_works.app_portal\') }}</span>'),
        ('<span>SME Operator Guide • Autonomous Financial Workflow</span>', '<span>{{ _(\'how_it_works.hero_badge\') }}</span>'),
        ('From scanning multilingual paper invoices to generating GAAP-compliant general ledgers, 95% confidence cash runways, automated debt recovery, and 1-click institutional bank credit packets.', '{{ _(\'how_it_works.hero_desc\') }}'),
        ('<span>Live Autonomous Architecture</span>', '<span>{{ _(\'how_it_works.arch_badge\') }}</span>'),
        ('An AI Participant, Not Just Another Record App', '{{ _(\'how_it_works.arch_title\') }}'),
        ('Unlike static accounting software where data must be manually keyed in, SME Finance Copilot actively participates in your business: watching cash thresholds, chasing overdue customers, forecasting liquidity, and assembling bank credit dossiers.', '{{ _(\'how_it_works.arch_desc\') }}'),
        ('<div class="text-white font-bold uppercase tracking-wider text-[11px] font-mono">Application Portals</div>', '<div class="text-white font-bold uppercase tracking-wider text-[11px] font-mono">{{ _(\'how_it_works.footer_apps_title\') }}</div>'),
        ('<div class="text-white font-bold uppercase tracking-wider text-[11px] font-mono">Compliance & Math</div>', '<div class="text-white font-bold uppercase tracking-wider text-[11px] font-mono">{{ _(\'how_it_works.footer_math_title\') }}</div>'),
        ('<div class="text-white font-bold uppercase tracking-wider text-[11px] font-mono">Developers & Markets</div>', '<div class="text-white font-bold uppercase tracking-wider text-[11px] font-mono">{{ _(\'how_it_works.footer_dev_title\') }}</div>'),
        ('<span>&copy; 2026 SME Finance Copilot. All rights reserved.</span>', '<span>&copy; 2026 SME Finance Copilot. {{ _(\'how_it_works.rights_reserved\') }}</span>'),
        ('<span class="font-mono text-cyan-400">Version 1.0.0 • Enterprise Edition</span>', '<span class="font-mono text-cyan-400">{{ _(\'how_it_works.version_tag\') }}</span>'),
    ]

    for old, new in replacements:
        content = content.replace(old, new)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("how_it_works.html localized!")

def localize_login():
    path = "src/web/templates/login.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    replacements = [
        ('{% block title %}Sign In — SME Finance Copilot{% endblock %}', '{% block title %}{{ _(\'login.title\') }} — SME Finance Copilot{% endblock %}'),
        ('<h1 class="text-xl font-bold text-white mt-4">Commercial Sign In</h1>', '<h1 class="text-xl font-bold text-white mt-4">{{ _(\'login.title\') }}</h1>'),
        ('Your business finances, cash flow, and decisions — in one intelligent workspace.', '{{ _(\'login.subtitle\') }}'),
        ('<label for="login-username" class="block text-xs font-medium text-slate-300 mb-1.5">Business Email or Username</label>', '<label for="login-username" class="block text-xs font-medium text-slate-300 mb-1.5">{{ _(\'login.username_label\') }}</label>'),
        ('<label for="login-password" class="block text-xs font-medium text-slate-300">Password</label>', '<label for="login-password" class="block text-xs font-medium text-slate-300">{{ _(\'login.password_label\') }}</label>'),
        ('Remember this device', '{{ _(\'login.remember_me\') }}'),
        ('<span id="login-btn-text">Sign In to Workspace</span>', '<span id="login-btn-text">{{ _(\'login.sign_in_button\') }}</span>'),
        ('<span>1-Click Quick Demo Profiles</span>', '<span>{{ _(\'login.demo_profiles\') }}</span>'),
        ('<span class="font-bold text-xs text-white block">Business Owner</span>', '<span class="font-bold text-xs text-white block">{{ _(\'login.profile_owner\') }}</span>'),
        ('<span class="font-bold text-xs text-white block">Branch Manager</span>', '<span class="font-bold text-xs text-white block">{{ _(\'login.profile_manager\') }}</span>'),
        ('<span class="font-bold text-xs text-white block">Shop Cashier</span>', '<span class="font-bold text-xs text-white block">{{ _(\'login.profile_cashier\') }}</span>'),
        ('<span class="font-bold text-xs text-white block">Tax Auditor</span>', '<span class="font-bold text-xs text-white block">{{ _(\'login.profile_auditor\') }}</span>'),
        ('<span class="font-bold text-xs text-rose-300 block">Platform Super Admin</span>', '<span class="font-bold text-xs text-rose-300 block">{{ _(\'login.profile_admin\') }}</span>'),
    ]

    for old, new in replacements:
        content = content.replace(old, new)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("login.html localized!")

localize_finance()
localize_how_it_works()
localize_login()
