import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ARTIFACTS_DIR = r"C:\Users\ASHIK_CSE\.gemini\antigravity\brain\40635c6d-8320-4cc1-990c-82bc85c90e5c"
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1600,1200")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=chrome_options)

try:
    print("==================================================")
    print("1. VERIFY DASHBOARD IN ENGLISH (lang=en)")
    print("==================================================")
    driver.get("http://127.0.0.1:8050/app/dashboard?lang=en")
    time.sleep(2)
    html_lang = driver.find_element(By.TAG_NAME, "html").get_attribute("lang")
    print(f"HTML lang attribute: {html_lang}")
    assert html_lang == "en", f"Expected en, got {html_lang}"
    page_text = driver.find_element(By.TAG_NAME, "body").text
    assert "Dashboard" in page_text, "Expected 'Dashboard' in English page"
    assert "Active Shop" in page_text or "Switch to Demo Store" in page_text
    
    shot1 = os.path.join(ARTIFACTS_DIR, "i18n_dashboard_en.png")
    driver.save_screenshot(shot1)
    print(f"Saved: {shot1}")

    print("\n==================================================")
    print("2. VERIFY DASHBOARD IN BENGALI (lang=bn)")
    print("==================================================")
    driver.get("http://127.0.0.1:8050/app/dashboard?lang=bn")
    time.sleep(2)
    html_lang = driver.find_element(By.TAG_NAME, "html").get_attribute("lang")
    print(f"HTML lang attribute: {html_lang}")
    assert html_lang == "bn", f"Expected bn, got {html_lang}"
    page_text = driver.find_element(By.TAG_NAME, "body").text
    assert "ড্যাশবোর্ড" in page_text, "Expected Bengali 'ড্যাশবোর্ড' in page"
    assert "অ্যাক্টিভ শপ" in page_text or "বাংলা" in page_text
    
    shot2 = os.path.join(ARTIFACTS_DIR, "i18n_dashboard_bn.png")
    driver.save_screenshot(shot2)
    print(f"Saved: {shot2}")

    print("\n==================================================")
    print("3. VERIFY DASHBOARD IN SIMPLIFIED CHINESE (lang=zh)")
    print("==================================================")
    driver.get("http://127.0.0.1:8050/app/dashboard?lang=zh")
    time.sleep(2)
    html_lang = driver.find_element(By.TAG_NAME, "html").get_attribute("lang")
    print(f"HTML lang attribute: {html_lang}")
    assert html_lang == "zh", f"Expected zh, got {html_lang}"
    page_text = driver.find_element(By.TAG_NAME, "body").text
    assert "控制台仪表盘" in page_text, "Expected Chinese '控制台仪表盘' in page"
    assert "当前店铺" in page_text or "简体中文" in page_text
    
    shot3 = os.path.join(ARTIFACTS_DIR, "i18n_dashboard_zh.png")
    driver.save_screenshot(shot3)
    print(f"Saved: {shot3}")

    print("\n==================================================")
    print("4. VERIFY COPILOT & VOICE AI CONTROLS IN BENGALI")
    print("==================================================")
    driver.get("http://127.0.0.1:8050/app/copilot?lang=bn")
    time.sleep(2)
    
    # Check Voice Language Selector
    voice_select = driver.find_element(By.ID, "voice-lang-select")
    selected_val = voice_select.get_attribute("value")
    print(f"Voice select value: {selected_val}")
    assert selected_val == "bn-BD", f"Expected bn-BD, got {selected_val}"
    
    # Check Audio Player Bar Elements
    audio_bar = driver.find_element(By.ID, "audio-playback-controls")
    assert audio_bar is not None
    btn_pause = driver.find_element(By.ID, "btn-audio-pause")
    btn_resume = driver.find_element(By.ID, "btn-audio-resume")
    btn_stop = driver.find_element(By.ID, "btn-audio-stop")
    print("Voice Audio Controls Found: Pause, Resume, Stop buttons verified!")
    
    shot4 = os.path.join(ARTIFACTS_DIR, "i18n_copilot_voice_bn.png")
    driver.save_screenshot(shot4)
    print(f"Saved: {shot4}")

    print("\n==================================================")
    print("5. VERIFY SETTINGS PAGE IN SIMPLIFIED CHINESE")
    print("==================================================")
    driver.get("http://127.0.0.1:8050/app/settings?lang=zh")
    time.sleep(2)
    page_text = driver.find_element(By.TAG_NAME, "body").text
    assert "系统设置" in page_text or "设置" in page_text, "Expected Chinese Settings in page"
    assert "核算本位币" in page_text or "货币" in page_text, "Expected Accounting Currency label in Chinese"
    
    shot5 = os.path.join(ARTIFACTS_DIR, "i18n_settings_zh.png")
    driver.save_screenshot(shot5)
    print(f"Saved: {shot5}")

    print("\n==================================================")
    print("6. VERIFY ONBOARDING CURRENCY SUGGESTION IN BENGALI")
    print("==================================================")
    driver.get("http://127.0.0.1:8050/app/onboarding?lang=bn")
    time.sleep(2)
    html_lang = driver.find_element(By.TAG_NAME, "html").get_attribute("lang")
    print(f"HTML lang attribute: {html_lang}")
    assert html_lang == "bn", f"Expected bn, got {html_lang}"
    
    # Check currency recommendation banner or currency select
    curr_select = driver.find_element(By.ID, "ob-currency")
    assert curr_select is not None, "Expected currency selector"
    note = driver.find_element(By.ID, "ob-currency-suggestion-note")
    assert note is not None
    print("Currency selector and suggestion note verified!")
    
    shot6 = os.path.join(ARTIFACTS_DIR, "i18n_onboarding_bn.png")
    driver.save_screenshot(shot6)
    print(f"Saved: {shot6}")

    print("\nALL BROWSER VERIFICATIONS PASSED SUCCESSFULLY!")

except Exception as e:
    print(f"\nERROR DURING BROWSER VERIFICATION: {e}")
    sys.exit(1)
finally:
    driver.quit()
