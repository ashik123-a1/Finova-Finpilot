import json

# Load en, bn, zh
with open('src/i18n/locales/en.json', 'r', encoding='utf-8') as f:
    en = json.load(f)
with open('src/i18n/locales/bn.json', 'r', encoding='utf-8') as f:
    bn = json.load(f)
with open('src/i18n/locales/zh.json', 'r', encoding='utf-8') as f:
    zh = json.load(f)

# 1. Update titles in en
en_titles = {
    "dashboard": {"title": "Executive Financial Dashboard"},
    "finance": {"title": "Financial Ledgers & P&L Statements"},
    "forecast": {"title": "Cash-Flow Forecasting & AI Runway"},
    "documents": {"title": "Document Capture & OCR Staging"},
    "loans": {"title": "SME Loan Underwriting & Affordability"},
    "inventory": {"title": "Inventory Valuation & Stock Aging"},
    "customers": {"title": "Customer Management & Receivables CRM"},
    "simulations": {"title": "Business Decision Intelligence & Simulations"},
    "copilot": {"title": "Autonomous Financial AI Copilot"},
    "audit": {"title": "Security Audit & Tamper-Evident Trail"},
    "settings": {"title": "Organization Settings & System Configuration"},
    "onboarding": {"title": "Workspace Onboarding & Commercial Setup"},
    "login": {
        "demo_profiles": "1-Click Quick Demo Login",
        "profile_owner": "Store Owner"
    }
}

bn_titles = {
    "dashboard": {"title": "এক্সিকিউটিভ ফিন্যান্সিয়াল ড্যাশবোর্ড"},
    "finance": {"title": "আর্থিক খতিয়ান ও লাভ-ক্ষতি বিবরণী"},
    "forecast": {"title": "ক্যাশ-ফ্লো পূর্বাভাস ও এআই রানওয়ে"},
    "documents": {"title": "ডকুমেন্ট ক্যাপচার ও ওসিআর স্টেজ"},
    "loans": {"title": "এসএমই ঋণ মূল্যায়ন ও সামর্থ্য"},
    "inventory": {"title": "ইনভেন্টরি মূল্যায়ন ও মজুদ ব্যবস্থাপনা"},
    "customers": {"title": "কাস্টমার ম্যানেজমেন্ট ও বাকি খতিয়ান"},
    "simulations": {"title": "ব্যবসায়িক সিদ্ধান্ত বুদ্ধিমত্তা ও সিমুলেশন"},
    "copilot": {"title": "স্বায়ত্তশাসিত আর্থিক এআই কপিলট"},
    "audit": {"title": "সিকিউরিটি অডিট ও অপরিবর্তনীয় লগ"},
    "settings": {"title": "প্রতিষ্ঠান সেটিংস ও কনফিগারেশন"},
    "onboarding": {"title": "ওয়ার্কস্পেস অনবোর্ডিং ও বাণিজ্যিক সেটআপ"},
    "login": {
        "demo_profiles": "১-ক্লিক দ্রুত ডেমো লগইন",
        "profile_owner": "স্টোর ওনার (Store Owner)"
    }
}

zh_titles = {
    "dashboard": {"title": "高管财务总控仪表盘 (Executive Financial Dashboard)"},
    "finance": {"title": "财务账簿与损益表 (Financial Ledgers)"},
    "forecast": {"title": "现金流智能预测 (Cash-Flow Forecasting)"},
    "documents": {"title": "票据采集与OCR审核 (Document Capture)"},
    "loans": {"title": "中小企业贷款承销与评估 (SME Loan Underwriting)"},
    "inventory": {"title": "存货估值与库龄管理 (Inventory Valuation)"},
    "customers": {"title": "客户管理与应收账款 (Customer Management)"},
    "simulations": {"title": "商业决策智能模拟 (Business Decision Intelligence)"},
    "copilot": {"title": "自主运行财务智能助手 (Autonomous Financial AI Copilot)"},
    "audit": {"title": "安全审计与防篡改追踪 (Security Audit)"},
    "settings": {"title": "机构设置与系统配置 (Organization Settings)"},
    "onboarding": {"title": "企业工作区配置向导 (Workspace Onboarding & Commercial Setup)"},
    "login": {
        "demo_profiles": "一键快速演示登录 (1-Click Quick Demo Login)",
        "profile_owner": "店主账户 (Store Owner)"
    }
}

def deep_merge(target, source):
    for k, v in source.items():
        if isinstance(v, dict):
            if k not in target or not isinstance(target[k], dict):
                target[k] = {}
            deep_merge(target[k], v)
        else:
            target[k] = v

deep_merge(en, en_titles)
deep_merge(bn, bn_titles)
deep_merge(zh, zh_titles)

with open('src/i18n/locales/en.json', 'w', encoding='utf-8') as f:
    json.dump(en, f, ensure_ascii=False, indent=2)
with open('src/i18n/locales/bn.json', 'w', encoding='utf-8') as f:
    json.dump(bn, f, ensure_ascii=False, indent=2)
with open('src/i18n/locales/zh.json', 'w', encoding='utf-8') as f:
    json.dump(zh, f, ensure_ascii=False, indent=2)

# Now mirror any missing keys from master (en) to ar, es, hi
def sync_to_other_locales(other_lang):
    path = f'src/i18n/locales/{other_lang}.json'
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = {}

    def copy_missing(src, dest):
        for k, v in src.items():
            if isinstance(v, dict):
                if k not in dest or not isinstance(dest[k], dict):
                    dest[k] = {}
                copy_missing(v, dest[k])
            else:
                if k not in dest:
                    dest[k] = v

    copy_missing(en, data)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Synced {path}")

for l in ['ar', 'es', 'hi']:
    sync_to_other_locales(l)

print("Catalog alignment complete!")
