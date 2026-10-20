import json

MISSING_EN = {
    "customers": {
        "credit_limit": "Credit Limit",
        "payment_reminder": "Polite Payment Reminder"
    },
    "forecast": {
        "confidence_level": "Confidence Interval"
    },
    "inventory": {
        "reorder_level": "Reorder Threshold"
    }
}

MISSING_BN = {
    "customers": {
        "credit_limit": "ক্রেডিট সীমা",
        "payment_reminder": "বিনম্র বকেয়া তাগাদা"
    },
    "forecast": {
        "confidence_level": "আত্মবিশ্বাস ব্যবধান (৯৫%)"
    },
    "inventory": {
        "reorder_level": "পুনরায় অর্ডারের ন্যূনতম সীমা"
    }
}

MISSING_ZH = {
    "customers": {
        "credit_limit": "信用额度上限",
        "payment_reminder": "礼貌催款提醒"
    },
    "forecast": {
        "confidence_level": "预测置信区间 (95%)"
    },
    "inventory": {
        "reorder_level": "补货警戒阈值"
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

update_locale('en', MISSING_EN)
update_locale('bn', MISSING_BN)
update_locale('zh', MISSING_ZH)
print("Added the 4 missing keys!")
