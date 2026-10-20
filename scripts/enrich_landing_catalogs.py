import json
from pathlib import Path

locales_dir = Path("F:/china project/src/i18n/locales")

extra_landing_keys = {
    "en": {
        "sim_risk_verdict": "✕ High Debt Risk — EMI Exceeds Operating Cash Buffer",
        "model1_desc": "Captures 7, 14, 30, and 90-day cash trends with 95% confidence intervals and 58% beat over random-walk.",
        "model2_desc": "Working capital regression model that learns non-linear retail sales surges and supplier payment patterns.",
        "model3_title": "Multilingual Classifier",
        "model3_desc": "TF-IDF + Logistic Regression categorizing English invoices, Chinese Fapiao (发票), and Bengali Mushak 6.3.",
        "model4_title": "Deterministic DSCR",
        "model4_desc": "Mathematical guardrail calculating exact reducing-balance EMI and debt-to-income without LLM float errors.",
        "preloader_title": "Autonomous Visual Preloaders",
        "preloader_desc": "Custom animated telemetry assets rendered in pure responsive scalable vectors."
    },
    "zh": {
        "sim_risk_verdict": "✕ 高偿债违约风险 — 每月还款超出营运资金安全垫",
        "model1_desc": "捕捉7天、14天、30天与90天现金流趋势，具备95%置信区间，相较随机游走基准提升58%。",
        "model2_desc": "营运资金回归模型，自主学习非线性零售销售高峰与供应商账期还款规律。",
        "model3_title": "多语种票据分类器",
        "model3_desc": "结合TF-IDF与逻辑回归，精准识别英文商业发票、中国增值税发票与孟加拉Mushak 6.3税单。",
        "model4_title": "确定性DSCR防护栏",
        "model4_desc": "高精数学护栏，计算精准等额本息还款与偿债收入比，杜绝大模型浮点计算误差。",
        "preloader_title": "自主动态遥测预载器",
        "preloader_desc": "纯自适应可缩放矢量渲染的定制动态遥测资产。"
    },
    "bn": {
        "sim_risk_verdict": "✕ উচ্চ ঋণের ঝুঁকি — ইএমআই পরিচালন নগদ বাফার অতিক্রম করেছে",
        "model1_desc": "৯৫% আত্মবিশ্বাসের সাথে ৭, ১৪, ৩০ এবং ৯০ দিনের নগদ প্রবণতা নিখুঁতভাবে পূর্বাভাস দেয়।",
        "model2_desc": "চলতি মূলধন রিগ্রেশন মডেল যা খুচরা বিক্রয় বৃদ্ধি এবং সরবরাহকারী পেমেন্ট প্যাটার্ন শেখে।",
        "model3_title": "বহুভাষিক ক্লাসিফায়ার",
        "model3_desc": "ইংরেজি চালান, চীনা ফা পিয়াও এবং বাংলা মূসক ৬.৩ চালান স্বয়ংক্রিয়ভাবে শ্রেণীবদ্ধ করে।",
        "model4_title": "ডিটারমিনিস্টিক ডিএসসিআর",
        "model4_desc": "এলএলএম ফ্লোট ত্রুটি ছাড়াই সুনির্দিষ্ট সমপরিমাণ মাসিক কিস্তি এবং ঋণ-আয় অনুপাত গণনা করে।",
        "preloader_title": "স্বায়ত্তশাসিত ভিজ্যুয়াল প্রিলোডার",
        "preloader_desc": "বিশুদ্ধ প্রতিক্রিয়াশীল স্কেলযোগ্য ভেক্টরে রেন্ডার করা কাস্টম অ্যানিমেটেড সম্পদ।"
    },
    "ar": {
        "sim_risk_verdict": "✕ مخاطر ديون عالية — القسط يتجاوز احتياطي النقد التشغيلي",
        "model1_desc": "يلتقط اتجاهات السيولة النقدية لـ 7 و14 و30 و90 يومًا مع فترات ثقة 95٪.",
        "model2_desc": "نموذج انحدار رأس المال العامل الذي يتعلم طفرات مبيعات التجزئة غير الخطية.",
        "model3_title": "مصنف متعدد اللغات",
        "model3_desc": "تصنيف الفواتير الإنجليزية والصينية (Fapiao) والبنغالية بدقة عالية.",
        "model4_title": "حساب DSCR الحتمي",
        "model4_desc": "حاجز حماية رياضي يحسب بدقة أقساط القروض المتناقصة دون أخطاء أرقام عشرية.",
        "preloader_title": "محملات بصرية متحركة ذاتية",
        "preloader_desc": "أصول قياس عن بعد متحركة مخصصة بمتجهات قابلة للتطوير."
    },
    "es": {
        "sim_risk_verdict": "✕ Alto Riesgo de Deuda — La cuota supera el colchón operativo",
        "model1_desc": "Captura tendencias de caja a 7, 14, 30 y 90 días con intervalos de confianza del 95%.",
        "model2_desc": "Modelo de regresión de capital de trabajo que aprende picos de ventas y patrones de pago a proveedores.",
        "model3_title": "Clasificador Multilingüe",
        "model3_desc": "TF-IDF + Regresión Logística clasificando facturas en inglés, Fapiao chino y Mushak bengalí.",
        "model4_title": "DSCR Determinista",
        "model4_desc": "Barandilla matemática que calcula cuotas sobre saldos e ingresos sin errores de coma flotante.",
        "preloader_title": "Precargadores Visuales Autónomos",
        "preloader_desc": "Recursos de telemetría animados personalizados renderizados en vectores escalables."
    },
    "hi": {
        "sim_risk_verdict": "✕ उच्च ऋण जोखिम — ईएमआई परिचालन नकद बफर से अधिक है",
        "model1_desc": "95% विश्वास अंतराल के साथ 7, 14, 30 और 90 दिनों के नकद रुझानों का पूर्वानुमान।",
        "model2_desc": "कार्यशील पूंजी प्रतिगमन मॉडल जो खुदरा बिक्री वृद्धि और आपूर्तिकर्ता भुगतान पैटर्न सीखता है।",
        "model3_title": "बहुभाषी क्लासिफायर",
        "model3_desc": "अंग्रेजी चालान, चीनी फापियाओ और बंगाली मूषक 6.3 चालानों को वर्गीकृत करता है।",
        "model4_title": "निश्चित DSCR गार्डरेल",
        "model4_desc": "बिना किसी फ्लोट त्रुटि के सटीक ईएमआई और ऋण-आय अनुपात की गणना करता है।",
        "preloader_title": "स्वायत्त विजुअल प्रीलोडर",
        "preloader_desc": "शुद्ध प्रतिक्रियाशील स्केलेबल वैक्टर में प्रस्तुत कस्टम एनिमेटेड संपत्तियां।"
    }
}

for loc in ["en", "zh", "bn", "ar", "es", "hi"]:
    fpath = locales_dir / f"{loc}.json"
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "landing" not in data:
        data["landing"] = {}
    data["landing"].update(extra_landing_keys[loc])
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Updated {loc}.json with extra landing keys.")
