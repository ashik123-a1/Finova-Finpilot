"""
Voice Assistant & Real-Time Financial AI Copilot API Route.
Handles speech-to-intent parsing, hands-free navigation actions,
and deterministic financial calculations across English, Bengali, and Chinese.
"""

from __future__ import annotations

import re
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import User, BusinessMembership
from src.ai.voice_service import VoiceService
from src.core.security import verify_token
from src.config import settings

logger = logging.getLogger("sme_finance_copilot.voice")

router = APIRouter(prefix="/voice", tags=["Voice Assistant AI"])


class VoiceCommandRequest(BaseModel):
    text: Optional[str] = None
    transcript: Optional[str] = None
    language: Optional[str] = "auto"
    locale: Optional[str] = "en"
    shop_id: Optional[int] = None
    business_id: Optional[int] = None
    confirmation_token: Optional[str] = None


# Navigation route dictionary for voice commands (requires explicit navigation verb/page intent)
NAVIGATION_MAP = {
    # Dashboard
    r"(?:go\s+to|open|navigate\s+to|switch\s+to)\s+(?:dashboard|home|kpi)|(?:ড্যাশবোর্ড|হোম)\s*(?:পেজ|পাতা|স্ক্রিন|যাও|যান|খুলুন|খুলো)|(?:前往|打开|进入)(?:控制台|仪表盘)": {
        "url": "/app/dashboard",
        "en": "Navigating to Executive Dashboard.",
        "bn": "এক্সিকিউটিভ ড্যাশবোর্ডে নিয়ে যাচ্ছি।",
        "zh": "正在前往总控仪表盘。",
    },
    # Finance / P&L
    r"(?:go\s+to|open|navigate\s+to|switch\s+to)\s+(?:finance|ledger|p&l|statements?)|(?:আর্থিক|খতিয়ান|হিসাব|ফিন্যান্স)\s*(?:পেজ|পাতা|স্ক্রিন|যাও|যান|খুলুন|খুলো)|(?:前往|打开|进入)(?:财务报表|财务明细|损益表|财务中心)": {
        "url": "/app/finance",
        "en": "Opening Financial Statements and General Ledger.",
        "bn": "আর্থিক বিবরণী এবং খতিয়ান পাতা খুলছি।",
        "zh": "正在打开财务报表与明细账。",
    },
    # Forecast
    r"(?:go\s+to|open|navigate\s+to|switch\s+to)\s+(?:forecast|runway\s+page|projection)|(?:পূর্বাভাস|ক্যাশ\s*রানওয়ে)\s*(?:পেজ|পাতা|স্ক্রিন|যাও|যান|খুলুন|খুলো)|(?:前往|打开|进入)(?:预测页面|现金流预测中心)": {
        "url": "/app/forecast",
        "en": "Opening Cash-Flow Forecast and Liquidity Projections.",
        "bn": "ক্যাশ-ফ্লো পূর্বাভাস এবং তারল্য মডেলিং পাতা খুলছি।",
        "zh": "正在打开现金流预测与资金储备。",
    },
    # Documents / OCR
    r"(?:go\s+to|open|navigate\s+to|switch\s+to)\s+(?:documents?|invoices?|receipts?|scan)|(?:ডকুমেন্ট|রসিদ|চালান)\s*(?:পেজ|পাতা|স্ক্রিন|যাও|যান|খুলুন|খুলো)|(?:前往|打开|进入)(?:单据中心|发票中心|单据审核)": {
        "url": "/app/documents",
        "en": "Opening Document Capture and OCR Staging.",
        "bn": "ডকুমেন্ট স্ক্যান এবং ওসিআর পর্যালোচনা পাতা খুলছি।",
        "zh": "正在打开票据采集与OCR审核中心。",
    },
    # Loans / DSCR
    r"(?:go\s+to|open|navigate\s+to|switch\s+to)\s+(?:loan\s+page|loans\s+screen|dscr\s+page)|(?:লোন|ঋণ|ব্যাংক\s*লোন)\s*(?:পেজ|পাতা|স্ক্রিন|যাও|যান|খুলুন|খুলো)|(?:前往|打开|进入)(?:贷款中心|贷款页面|信贷矩阵)": {
        "url": "/app/loans",
        "en": "Opening SME Loan Affordability and Bank Comparison Matrix.",
        "bn": "এসএমই ঋণ সুবিধা ও ব্যাংক তুলনা ম্যাট্রিক্স খুলছি।",
        "zh": "正在打开中小企业贷款方案与银行匹配矩阵。",
    },
    # Inventory
    r"(?:go\s+to|open|navigate\s+to|switch\s+to)\s+(?:inventory|stock\s+page|products?\s+page)|(?:ইনভেন্টরি|স্টক|পণ্য)\s*(?:পেজ|পাতা|স্ক্রিন|যাও|যান|খুলুন|খুলো)|(?:前往|打开|进入)(?:库存中心|库存页面|商品管理)": {
        "url": "/app/inventory",
        "en": "Opening Inventory Valuation and SKU Stock Levels.",
        "bn": "ইনভেন্টরি মূল্যায়ন এবং স্টক পাতা খুলছি।",
        "zh": "正在打开库存估值与SKU管理。",
    },
    # Customers / CRM
    r"(?:go\s+to|open|navigate\s+to|switch\s+to)\s+(?:customers?\s+page|clients?\s+page|crm|receivables\s+page)|(?:কাস্টমার|খরিদ্দার|বকেয়া)\s*(?:পেজ|পাতা|স্ক্রিন|যাও|যান|খুলুন|খুলো)|(?:前往|打开|进入)(?:客户中心|客户页面|应收催收)": {
        "url": "/app/customers",
        "en": "Opening Customer Directory and Receivables Management.",
        "bn": "কাস্টমার ডিরেক্টরি এবং বকেয়া পাওনা পাতা খুলছি।",
        "zh": "正在打开客户目录与应收催收管理。",
    },
    # Simulations
    r"(?:go\s+to|open|navigate\s+to|switch\s+to)\s+(?:simulations?|what\s*if\s+page|pricing\s+page)|(?:সিমুলেশন|ডিসিশন)\s*(?:পেজ|পাতা|স্ক্রিন|যাও|যান|খুলুন|খুলো)|(?:前往|打开|进入)(?:模拟器|情景模拟|商业模拟)": {
        "url": "/app/simulations",
        "en": "Opening What-If Decision Simulator.",
        "bn": "বিজনেস ডিসিশন সিমুলেটর পাতা খুলছি।",
        "zh": "正在打开商业决策情景模拟器。",
    },
    # Copilot
    r"(?:go\s+to|open|navigate\s+to|switch\s+to)\s+(?:copilot|ai\s+chat|assistant)|(?:কপিলট|এআই\s*চ্যাট)\s*(?:পেজ|পাতা|স্ক্রিন|যাও|যান|খুলুন|খুলো)|(?:前往|打开|进入)(?:智能助手|财务助手|对话中心)": {
        "url": "/app/copilot",
        "en": "Opening Conversational Financial AI Copilot.",
        "bn": "আর্থিক এআই কপিলট কনসোল খুলছি।",
        "zh": "正在打开智能财务对话助手。",
    },
    # Voice Control
    r"(?:go\s+to|open|navigate\s+to|switch\s+to)\s+(?:voice|hands\s*free)|(?:ভয়েস\s*কন্ট্রোল|ভয়েস\s*সহকারী)\s*(?:পেজ|পাতা|স্ক্রিন|যাও|যান|খুলুন|খুলো)|(?:前往|打开|进入)(?:语音控制|语音助手|双语控制台)": {
        "url": "/app/voice",
        "en": "Opening Bilingual Voice Assistant Console.",
        "bn": "দ্বিভাষিক ভয়েস সহকারী কনসোল খুলছি।",
        "zh": "正在打开双语语音交互控制台。",
    },
    # Settings
    r"(?:go\s+to|open|navigate\s+to|switch\s+to)\s+(?:settings|config)|(?:সেটিংস|কনফিগারেশন)\s*(?:পেজ|পাতা|স্ক্রিন|যাও|যান|খুলুন|খুলো)|(?:前往|打开|进入)(?:系统设置|设置中心)": {
        "url": "/app/settings",
        "en": "Opening System and Organization Settings.",
        "bn": "সিস্টেম এবং প্রতিষ্ঠান সেটিংস পাতা খুলছি।",
        "zh": "正在打开系统与企业设置。",
    },
    # Admin
    r"(?:go\s+to|open|navigate\s+to|switch\s+to)\s+(?:admin|super\s*admin|platform)|(?:এডমিন|সুপার\s*এডমিন)\s*(?:পেজ|পাতা|স্ক্রিন|যাও|যান|খুলুন|খুলো)|(?:前往|打开|进入)(?:管理后台|平台管理|超管后台)": {
        "url": "/app/admin",
        "en": "Opening Platform Super Admin Portal.",
        "bn": "প্ল্যাটফর্ম সুপার অ্যাডমিন পোর্টাল খুলছি।",
        "zh": "正在打开平台超级管理员后台。",
    },
}


def _check_navigation_intent(text: str, loc: str) -> Optional[Dict[str, Any]]:
    """Checks if voice command requests navigation to an application page."""
    t = text.strip().lower()
    for pattern, nav in NAVIGATION_MAP.items():
        if re.search(pattern, t, re.IGNORECASE):
            spoken = nav.get(loc, nav.get("en", "Navigating to requested page."))
            return {
                "intent": "NAVIGATE",
                "confidence": 0.96,
                "target_url": nav["url"],
                "suggested_action": {
                    "action": "NAVIGATE",
                    "url": nav["url"]
                },
                "spoken_response": spoken,
                "spoken_response_en": nav.get("en", spoken),
                "spoken_response_bn": nav.get("bn", spoken),
                "spoken_response_zh": nav.get("zh", spoken),
                "text_response": f"🧭 **Navigation:** {spoken}\nRedirecting to `{nav['url']}`...",
            }
    return None


@router.post("/command")
@router.post("/parse-intent")
def execute_voice_command(
    req: VoiceCommandRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Executes natural voice command.
    Dispatches to navigation, hands-free controls, or deterministic financial intelligence.
    """
    input_text = (req.text or req.transcript or "").strip()
    if not input_text:
        return {
            "status": "error",
            "intent": "EMPTY_INPUT",
            "confidence": 0.0,
            "spoken_response": "I did not detect any speech. Please tap the microphone and speak.",
            "spoken_response_en": "I did not detect any speech. Please tap the microphone and speak.",
            "spoken_response_bn": "আমি কোনো কথা শুনতে পাইনি। অনুগ্রহ করে আবার বলুন।",
            "spoken_response_zh": "未检测到语音输入。请点击麦克风重新说话。",
            "text_response": "No audio or speech input detected. Please tap the microphone and try again.",
        }

    # Resolve active language: request param, cookie, or default 'en'
    loc = req.locale or req.language or "en"
    if loc == "auto":
        # Check cookie first, else detect from text
        cookie_lang = request.cookies.get("sme_lang")
        if cookie_lang:
            loc = cookie_lang
        else:
            # Simple script detection
            if re.search(r"[\u0980-\u09FF]", input_text):
                loc = "bn"
            elif re.search(r"[\u4E00-\u9FFF]", input_text):
                loc = "zh"
            else:
                loc = "en"

    clean_loc = loc.lower().split("-")[0].strip()
    if clean_loc not in ["en", "bn", "zh"]:
        clean_loc = "en"

    # 1. Early Stop Phrase Interception
    stop_pattern = r"(?:^|[^\w])(?:stop\s+ashik|stop\s+copilot|stop\s+assistant|স্টপ\s*আশিক|স্টপ\s*কপিলট|বন্ধ\s*করো?|থামো|停止|关闭免提|disable\s+hands\s*free)(?:$|[^\w])"
    if re.search(stop_pattern, input_text, re.IGNORECASE):
        spoken_map = {
            "en": "Hands-free voice mode deactivated. Standing by.",
            "bn": "হ্যান্ডস-ফ্রি ভয়েস মোড বন্ধ করা হয়েছে।",
            "zh": "免提语音模式已关闭。助手转入待命。",
        }
        spk = spoken_map.get(clean_loc, spoken_map["en"])
        return {
            "status": "success",
            "intent": "CONTROL_STOP_COPILOT",
            "confidence": 0.99,
            "suggested_action": {"action": "DEACTIVATE_HANDS_FREE"},
            "spoken_response": spk,
            "spoken_response_en": spoken_map["en"],
            "spoken_response_bn": spoken_map["bn"],
            "spoken_response_zh": spoken_map["zh"],
            "text_response": f"🛑 **Hands-Free Deactivated:** {spk}",
        }

    # 2. Early Wake-Word Greeting Interception (e.g., "Hi Ashik", "Hey Ashik", "Hello Ashik", "Hi Copilot")
    wake_alone_pattern = r"^(?:(?:hi|hey|hello|high|hallo|hai|\u09b9\u09be\u0987|\u09b9\u09c7|\u09b9\u09cd\u09af\u09be\u09b2\u09cb|\u4f60\u597d|\u5582)[\s,.:;!?-]*)?(?:ashik|ashique|ashiq|asik|\u0986\u09b6\u09bf\u0995|copilot|\u0995\u09aa\u09bf\u09b2\u099f)\s*[!.?]*$"
    if re.match(wake_alone_pattern, input_text.strip(), re.IGNORECASE):
        greeting_map = {
            "en": "Hi Ashik! I am listening. Ask me about your cash runway, loan eligibility, daily sales, or inventory.",
            "bn": "হাই আশিক! আমি শুনছি। আপনার ক্যাশ রানওয়ে, ব্যাংক ঋণ সুবিধা, দৈনিক বিক্রয় বা স্টক সম্পর্কে জিজ্ঞাসা করুন।",
            "zh": "你好 Ashik！我在听。请随时询问现金流储备、贷款方案、今日销售或库存状况。",
        }
        spk = greeting_map.get(clean_loc, greeting_map["en"])
        return {
            "status": "success",
            "intent": "WAKE_WORD_GREETING",
            "confidence": 0.99,
            "suggested_action": {"action": "STANDBY_COMMAND_LISTENING"},
            "spoken_response": spk,
            "spoken_response_en": greeting_map["en"],
            "spoken_response_bn": greeting_map["bn"],
            "spoken_response_zh": greeting_map["zh"],
            "text_response": (
                f"👋 **Hi Ashik!** I'm active and listening for your voice commands.\n\n"
                f"**Try asking:**\n"
                f"- 💰 *\"What is my cash runway?\"*\n"
                f"- 📊 *\"What is my net profit?\"*\n"
                f"- 🏦 *\"Show loan options and DSCR\"*\n"
                f"- 📦 *\"Check low stock alerts\"*\n"
                f"- 🧭 *\"Go to dashboard\"* or *\"Open finance\"*"
            ),
        }

    # 2. Check Navigation Request
    nav_result = _check_navigation_intent(input_text, clean_loc)
    if nav_result:
        nav_result["status"] = "success"
        nav_result["language"] = clean_loc
        return nav_result

    # 3. Resolve user identity and tenant context
    token = request.cookies.get("sme_auth_token")
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]

    user_id = 1
    user_role = "owner"
    business_id = req.business_id or 19
    shop_id = req.shop_id or 28

    if token:
        try:
            uid = verify_token(token, settings.SECRET_KEY)
            if uid:
                u = db.get(User, uid)
                if u:
                    user_id = u.id
                    mem = db.query(BusinessMembership).filter_by(user_id=uid, is_active=True).first()
                    if mem:
                        user_role = mem.role_code
                        business_id = mem.business_id
        except Exception:
            pass

    # 4. Dispatch to VoiceService Financial Processor
    result = VoiceService.process_voice_command(
        session=db,
        transcript=input_text,
        user_id=user_id,
        user_role=user_role,
        business_id=business_id,
        shop_id=shop_id,
        locale=clean_loc,
        confirmation_token=req.confirmation_token,
    )

    # Format consistent response envelope for frontend controller
    spoken_text = result.get("spoken_response") or result.get("text_response", "")
    return {
        "status": result.get("status", "success"),
        "intent": result.get("intent", "FINANCIAL_QUERY"),
        "confidence": 0.92,
        "language": clean_loc,
        "text_response": result.get("text_response", ""),
        "spoken_response": spoken_text,
        "spoken_response_en": spoken_text if clean_loc == "en" else result.get("spoken_response", spoken_text),
        "spoken_response_bn": spoken_text if clean_loc == "bn" else result.get("spoken_response", spoken_text),
        "spoken_response_zh": spoken_text if clean_loc == "zh" else result.get("spoken_response", spoken_text),
        "data": result.get("data", {}),
        "requires_confirmation": result.get("requires_confirmation", False),
        "confirmation_token": result.get("confirmation_token"),
    }


@router.get("/status")
def get_voice_service_status() -> Dict[str, Any]:
    """Returns telemetry on Voice AI engine availability and supported wake words."""
    return {
        "status": "online",
        "engine": "Local-First Web Audio & Deterministic Financial Logic",
        "supported_locales": ["en", "bn", "zh"],
        "wake_words": [
            "Hi Ashik", "Hey Ashik", "Hello Ashik",
            "হাই আশিক", "হে আশিক", "你好 Ashik", "Hello Copilot"
        ],
        "stop_words": [
            "Stop Ashik", "Stop Copilot", "স্টপ আশিক", "স্টপ কপিলট", "停止", "Turn off hands free"
        ],
        "capabilities": [
            "Continuous hands-free wake word listening",
            "Cross-page session persistence via sessionStorage",
            "Client-side verified page navigation routing",
            "Deterministic integer math financial calculations",
            "Multilingual Web Speech synthesis playback"
        ]
    }
