import json

COMP_EN = {
    "compliance": {
        "gaap_principles": "GAAP / IFRS Principles",
        "integer_math": "Integer Minor Units Math",
        "hmac_tokens": "HMAC Cryptographic Tokens",
        "audit_triggers": "Immutable Audit Triggers",
        "tenant_isolation": "Multi-Tenant Shop Isolation",
        "zero_float_error": "Zero Float Rounding Error",
        "swagger_docs": "FastAPI Swagger Docs",
        "health_api": "Health Telemetry API",
        "bangladesh_market": "🇧🇩 Bangladesh (BDT ৳ • Mushak)",
        "china_market": "🇨🇳 China (CNY ¥ • Fapiao)",
        "global_market": "🌐 Global (USD $ • EUR € • GBP £)"
    }
}

COMP_BN = {
    "compliance": {
        "gaap_principles": "গ্যাপ / আইএফআরএস মানদণ্ড",
        "integer_math": "পূর্ণসংখ্যা মাইনর ইউনিট গণিত",
        "hmac_tokens": "এইচএমএসি ক্রিপ্টোগ্রাফিক টোকেন",
        "audit_triggers": "অপরিবর্তনীয় অডিট ট্রিগার",
        "tenant_isolation": "মাল্টি-টেন্যান্ট শপ আইসোলেশন",
        "zero_float_error": "শূন্য ফ্লোটিং-পয়েন্ট রাউন্ডিং ত্রুটি",
        "swagger_docs": "ফাস্টএপিআই সোয়্যাগার ডকস",
        "health_api": "হেলথ টেলিমেট্রি এপিআই",
        "bangladesh_market": "🇧🇩 বাংলাদেশ (BDT ৳ • মূসক)",
        "china_market": "🇨🇳 চীন (CNY ¥ • 发票)",
        "global_market": "🌐 গ্লোবাল (USD $ • EUR € • GBP £)"
    }
}

COMP_ZH = {
    "compliance": {
        "gaap_principles": "GAAP / IFRS 财务准则",
        "integer_math": "整数分位无损运算",
        "hmac_tokens": "HMAC 密码学安全令牌",
        "audit_triggers": "不可篡改审计触发器",
        "tenant_isolation": "多租户门店物理隔离",
        "zero_float_error": "零浮点四舍五入误差",
        "swagger_docs": "FastAPI 交互式接口文档",
        "health_api": "健康遥测接口",
        "bangladesh_market": "🇧🇩 孟加拉国 (BDT ৳ • 增值税)",
        "china_market": "🇨🇳 中国 (CNY ¥ • 发票)",
        "global_market": "🌐 全球 (USD $ • EUR € • GBP £)"
    }
}

def merge_dict(target, source):
    for k, v in source.items():
        if isinstance(v, dict):
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            merge_dict(target[k], v)
        else:
            target[k] = v

def update_locale(lang, enrichment):
    path = f'src/i18n/locales/{lang}.json'
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    merge_dict(data, enrichment)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

update_locale('en', COMP_EN)
update_locale('bn', COMP_BN)
update_locale('zh', COMP_ZH)
print("Locales updated with compliance footer keys!")

# Now replace in landing.html and how_it_works.html
replacements = [
    ('<li><a href="/app/dashboard" class="hover:text-cyan-400 transition-colors">Executive Dashboard</a></li>', '<li><a href="/app/dashboard" class="hover:text-cyan-400 transition-colors">{{ _(\'navigation.dashboard\') }}</a></li>'),
    ('<li><a href="/app/finance" class="hover:text-cyan-400 transition-colors">P&L Ledgers & Cash Flow</a></li>', '<li><a href="/app/finance" class="hover:text-cyan-400 transition-colors">{{ _(\'navigation.finance\') }}</a></li>'),
    ('<li><a href="/app/forecast" class="hover:text-cyan-400 transition-colors">Cash Forecast Engine</a></li>', '<li><a href="/app/forecast" class="hover:text-cyan-400 transition-colors">{{ _(\'navigation.forecast\') }}</a></li>'),
    ('<li><a href="/app/documents" class="hover:text-cyan-400 transition-colors">Document Capture & OCR</a></li>', '<li><a href="/app/documents" class="hover:text-cyan-400 transition-colors">{{ _(\'navigation.documents\') }}</a></li>'),
    ('<li><a href="/app/loans" class="hover:text-cyan-400 transition-colors">SME Loan Financing</a></li>', '<li><a href="/app/loans" class="hover:text-cyan-400 transition-colors">{{ _(\'navigation.loans\') }}</a></li>'),
    ('<li><a href="/app/customers" class="hover:text-cyan-400 transition-colors">Customers & Overdue Dues</a></li>', '<li><a href="/app/customers" class="hover:text-cyan-400 transition-colors">{{ _(\'navigation.customers\') }}</a></li>'),
    ('<li><a href="/app/inventory" class="hover:text-cyan-400 transition-colors">SKU Inventory & Movements</a></li>', '<li><a href="/app/inventory" class="hover:text-cyan-400 transition-colors">{{ _(\'navigation.inventory\') }}</a></li>'),
    ('<li><a href="/app/admin" class="hover:text-rose-400 transition-colors">Super Admin Console</a></li>', '<li><a href="/app/admin" class="hover:text-rose-400 transition-colors">{{ _(\'navigation.admin\') }}</a></li>'),
    ('<span>GAAP / IFRS Principles</span>', '<span>{{ _(\'compliance.gaap_principles\') }}</span>'),
    ('<span>Integer Minor Units Math</span>', '<span>{{ _(\'compliance.integer_math\') }}</span>'),
    ('<span>HMAC Cryptographic Tokens</span>', '<span>{{ _(\'compliance.hmac_tokens\') }}</span>'),
    ('<span>Immutable Audit Triggers</span>', '<span>{{ _(\'compliance.audit_triggers\') }}</span>'),
    ('<span>Multi-Tenant Shop Isolation</span>', '<span>{{ _(\'compliance.tenant_isolation\') }}</span>'),
    ('<span>Zero Float Rounding Error</span>', '<span>{{ _(\'compliance.zero_float_error\') }}</span>'),
    ('<span>FastAPI Swagger Docs</span>', '<span>{{ _(\'compliance.swagger_docs\') }}</span>'),
    ('<span>Health Telemetry API</span>', '<span>{{ _(\'compliance.health_api\') }}</span>'),
    ('<li><a href="/login" class="hover:text-cyan-400 transition-colors">1-Click Evaluation Personas</a></li>', '<li><a href="/login" class="hover:text-cyan-400 transition-colors">{{ _(\'login.demo_profiles\') }}</a></li>'),
    ('<li><span class="text-slate-300">🇧🇩 Bangladesh (BDT ৳ • Mushak)</span></li>', '<li><span class="text-slate-300">{{ _(\'compliance.bangladesh_market\') }}</span></li>'),
    ('<li><span class="text-slate-300">🇨🇳 China (CNY ¥ • Fapiao)</span></li>', '<li><span class="text-slate-300">{{ _(\'compliance.china_market\') }}</span></li>'),
    ('<li><span class="text-slate-300">🌐 Global (USD $ • EUR € • GBP £)</span></li>', '<li><span class="text-slate-300">{{ _(\'compliance.global_market\') }}</span></li>'),
    ('<a href="/landing" class="hover:text-slate-300 transition-colors">Home</a>', '<a href="/landing" class="hover:text-slate-300 transition-colors">{{ _(\'how_it_works.return_home\') }}</a>'),
    ('<a href="/how-it-works" class="hover:text-slate-300 transition-colors">Operator Guide</a>', '<a href="/how-it-works" class="hover:text-slate-300 transition-colors">{{ _(\'how_it_works.capabilities\') }}</a>'),
    ('<a href="/login" class="hover:text-slate-300 transition-colors">Sign In</a>', '<a href="/login" class="hover:text-slate-300 transition-colors">{{ _(\'login.title\') }}</a>'),
    ('<a href="/app/dashboard" class="text-cyan-400 hover:underline">App Portal</a>', '<a href="/app/dashboard" class="text-cyan-400 hover:underline">{{ _(\'how_it_works.app_portal\') }}</a>'),
]

for t_path in ["src/web/templates/landing.html", "src/web/templates/how_it_works.html"]:
    with open(t_path, "r", encoding="utf-8") as f:
        c = f.read()
    rep_count = 0
    for old, new in replacements:
        if old in c:
            c = c.replace(old, new)
            rep_count += 1
    with open(t_path, "w", encoding="utf-8") as f:
        f.write(c)
    print(f"Updated {t_path}: {rep_count}/{len(replacements)} replaced.")
