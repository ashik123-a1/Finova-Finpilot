import json
from pathlib import Path

locales_dir = Path("F:/china project/src/i18n/locales")

extra_keys = {
    "en": {
        "nav_how_it_works": "How It Works",
        "footer_platform": "Platform Capabilities",
        "footer_apps": "Core Application Portals",
        "footer_compliance": "Security & Compliance",
        "footer_developers": "Developers & Telemetry",
        "footer_regional": "Global SME Markets",
        "btn_explore_guide": "Explore Full Operator Guide",
        "feat_crm_title": "Customers & CRM Receivables Chase",
        "feat_crm_desc": "Automated WhatsApp and SMS payment chase for overdue dues with RFM loyalty segmentation.",
        "feat_inv_title": "Inventory Valuation & Stock Aging",
        "feat_inv_desc": "FIFO & WAC inventory valuation, stock turnover tracking, and automated reorder purchase orders.",
        "feat_voice_title": "Hands-Free Multilingual Voice AI",
        "feat_voice_desc": "Voice-driven financial queries in English, Bengali, and Chinese for real-time P&L insights.",
        "feat_forecast_title": "Chronological Cash Flow AI Runway",
        "feat_forecast_desc": "Rolling ARIMA and LightGBM models projecting 7, 14, 30, and 90-day cash liquidity."
    },
    "zh": {
        "nav_how_it_works": "工作流程",
        "footer_platform": "平台核心能力",
        "footer_apps": "核心业务工作台",
        "footer_compliance": "安全与数据合规",
        "footer_developers": "开发者与系统遥测",
        "footer_regional": "全球中小微企业覆盖",
        "btn_explore_guide": "浏览完整操作使用指南",
        "feat_crm_title": "客户CRM与应收账款催收",
        "feat_crm_desc": "基于RFM分群的一键WhatsApp/短信催款，结合毛利安全护栏的个性化折扣营销。",
        "feat_inv_title": "存货估值与库龄呆滞分析",
        "feat_inv_desc": "先进先出与移动加权平均核算，库龄分级监控与安全库存自动生成采购补货单。",
        "feat_voice_title": "多语种智能语音AI助手",
        "feat_voice_desc": "支持中文、英语与孟加拉语语音交互，随时随地问询收支异常与税务临界点。",
        "feat_forecast_title": "时序现金流AI滚动预测跑道",
        "feat_forecast_desc": "融合ARIMA与LightGBM回归树，精准预测7天、14天、30天与90天流动性区间。"
    },
    "bn": {
        "nav_how_it_works": "কীভাবে কাজ করে",
        "footer_platform": "প্ল্যাটফর্ম সক্ষমতা",
        "footer_apps": "মূল অ্যাপ্লিকেশন পোর্টাল",
        "footer_compliance": "নিরাপত্তা ও সম্মতি",
        "footer_developers": "ডেভেলপার ও টেলিমেট্রি",
        "footer_regional": "গ্লোবাল এসএমই মার্কেটস",
        "btn_explore_guide": "সম্পূর্ণ অপারেটর গাইড দেখুন",
        "feat_crm_title": "গ্রাহক সিআরএম এবং বকেয়া আদায়",
        "feat_crm_desc": "আরএফএম সেগমেন্টেশন সহ বকেয়া আদায়ে স্বয়ংক্রিয় হোয়াটসঅ্যাপ ও এসএমএস অনুস্মারক।",
        "feat_inv_title": "ইনভেন্টরি মূল্যায়ন এবং স্টক এজিং",
        "feat_inv_desc": "ফিফো এবং ডাব্লুএসি ইনভেন্টরি মূল্যায়ন এবং স্বয়ংক্রিয় পুনঃঅর্ডার ক্রয় আদেশ।",
        "feat_voice_title": "হ্যান্ডস-ফ্রি বহুভাষিক ভয়েস এআই",
        "feat_voice_desc": "রিয়েল-টাইম পিঅ্যান্ডএল অন্তর্দৃষ্টির জন্য ইংরেজি, বাংলা এবং চীনা ভাষায় ভয়েস কমান্ড।",
        "feat_forecast_title": "নগদ প্রবাহ এআই রানওয়ে পূর্বাভাস",
        "feat_forecast_desc": "৭, ১৪, ৩০ এবং ৯০ দিনের নগদ তারল্য পূর্বাভাস দিতে এআই ও রিগ্রেশন মডেল।"
    },
    "ar": {
        "nav_how_it_works": "كيف يعمل",
        "footer_platform": "قدرات المنصة",
        "footer_apps": "بوابات التطبيق الأساسية",
        "footer_compliance": "الأمان والامتثال",
        "footer_developers": "المطورون والقياس عن بعد",
        "footer_regional": "أسواق الشركات الصغيرة العالمية",
        "btn_explore_guide": "استكشف دليل المشغل الكامل",
        "feat_crm_title": "إدارة العملاء وتحصيل المستحقات",
        "feat_crm_desc": "تذكيرات تلقائية عبر واتساب ورسائل نصية لتحصيل الديون مع تقسيم العملاء.",
        "feat_inv_title": "تقييم المخزون وأعمار البضائع",
        "feat_inv_desc": "تقييم FIFO وWAC وتتبع حركة المخزون مع أوامر شراء تلقائية.",
        "feat_voice_title": "مساعد صوتي ذكي متعدد اللغات",
        "feat_voice_desc": "أوامر صوتية باللغات الإنجليزية والبنغالية والصينية لمعرفة الأرباح والخسائر.",
        "feat_forecast_title": "توقعات التدفقات النقدية الذكية",
        "feat_forecast_desc": "نماذج تتوقع سيولة النقد لـ 7 و14 و30 و90 يومًا."
    },
    "es": {
        "nav_how_it_works": "Cómo Funciona",
        "footer_platform": "Capacidades de la Plataforma",
        "footer_apps": "Portales Principales de la App",
        "footer_compliance": "Seguridad y Cumplimiento",
        "footer_developers": "Desarrolladores y Telemetría",
        "footer_regional": "Mercados Globales de PYMES",
        "btn_explore_guide": "Explorar Guía Completa de Uso",
        "feat_crm_title": "CRM y Cobro de Saldos Vencidos",
        "feat_crm_desc": "Recordatorios automáticos por WhatsApp y SMS para deudas con segmentación RFM.",
        "feat_inv_title": "Valuación de Inventario y Antigüedad",
        "feat_inv_desc": "Valuación FIFO y WAC, rotación de existencias y órdenes de compra automáticas.",
        "feat_voice_title": "Voz IA Manos Libres Multilingüe",
        "feat_voice_desc": "Consultas por voz en inglés, bengalí y chino para análisis de P&L en tiempo real.",
        "feat_forecast_title": "Pista de Flujo de Caja con IA",
        "feat_forecast_desc": "Modelos ARIMA y LightGBM que proyectan liquidez a 7, 14, 30 y 90 días."
    },
    "hi": {
        "nav_how_it_works": "यह कैसे काम करता है",
        "footer_platform": "प्लेटफ़ॉर्म क्षमताएं",
        "footer_apps": "मुख्य एप्लिकेशन पोर्टल",
        "footer_compliance": "सुरक्षा और अनुपालन",
        "footer_developers": "डेवलपर्स और टेलीमेट्री",
        "footer_regional": "वैश्विक एसएमई बाजार",
        "btn_explore_guide": "ऑपरेटर गाइड देखें",
        "feat_crm_title": "ग्राहक सीआरएम और बकाया वसूली",
        "feat_crm_desc": "आरएफएम विभाजन के साथ बकाया वसूली के लिए स्वचालित व्हाट्सएप और एसएमएस अनुस्मारक।",
        "feat_inv_title": "इन्वेंटरी मूल्यांकन और स्टॉक आयु",
        "feat_inv_desc": "फीफो और डब्ल्यूएसी इन्वेंटरी मूल्यांकन और स्वचालित पुनः आदेश खरीद आदेश।",
        "feat_voice_title": "हैंड्स-फ्री बहुभाषी वॉयस एआई",
        "feat_voice_desc": "लाभ और हानि के त्वरित विश्लेषण के लिए अंग्रेजी, बंगाली और चीनी में वॉयस कमांड।",
        "feat_forecast_title": "कैश फ्लो एआई रनवे पूर्वानुमान",
        "feat_forecast_desc": "7, 14, 30 और 90 दिनों की नकदी तरलता का अनुमान लगाने वाले एआई मॉडल।"
    }
}

for loc in ["en", "zh", "bn", "ar", "es", "hi"]:
    fpath = locales_dir / f"{loc}.json"
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "landing" not in data:
        data["landing"] = {}
    data["landing"].update(extra_keys[loc])
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Updated {loc}.json with new landing & navigation keys.")
