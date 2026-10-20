import sys
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

artifact_dir = Path("C:/Users/ASHIK_CSE/.gemini/antigravity/brain/40635c6d-8320-4cc1-990c-82bc85c90e5c")

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=chrome_options)

try:
    print("1. Opening Landing page in English...")
    driver.get("http://127.0.0.1:8050/?lang=en")
    time.sleep(2)
    driver.save_screenshot(str(artifact_dir / "landing_english_verified.png"))
    print("Saved landing_english_verified.png")

    print("2. Opening Landing page in Chinese...")
    driver.get("http://127.0.0.1:8050/?lang=zh")
    time.sleep(2)
    driver.save_screenshot(str(artifact_dir / "landing_chinese_verified.png"))
    print("Saved landing_chinese_verified.png")

    body_text = driver.find_element(By.TAG_NAME, "body").text
    assert "核心功能" in body_text, "Failed to find Chinese nav in landing page"
    assert "自主智能财务Copilot" in body_text, "Failed to find Chinese title in landing page"
    print("Chinese landing page text verified successfully!")

    print("3. Opening Landing page in Bengali...")
    driver.get("http://127.0.0.1:8050/?lang=bn")
    time.sleep(2)
    driver.save_screenshot(str(artifact_dir / "landing_bengali_verified.png"))
    print("Saved landing_bengali_verified.png")

    body_text_bn = driver.find_element(By.TAG_NAME, "body").text
    assert "সক্ষমতা" in body_text_bn, "Failed to find Bengali nav in landing page"
    assert "ফাইন্যান্স কোপাইলট" in body_text_bn, "Failed to find Bengali title in landing page"
    print("Bengali landing page text verified successfully!")

    print("4. Testing language pill switcher click (EN -> ZH)...")
    driver.get("http://127.0.0.1:8050/?lang=en")
    time.sleep(1)
    zh_pill = driver.find_element(By.XPATH, "//a[contains(text(), '中文')]")
    zh_pill.click()
    time.sleep(2)
    driver.save_screenshot(str(artifact_dir / "landing_switcher_clicked_zh.png"))
    current_body = driver.find_element(By.TAG_NAME, "body").text
    assert "自主智能财务Copilot" in current_body, "Pill click failed to switch language to Chinese"
    print("Pill click switcher verified successfully!")

    print("5. Testing language pill switcher click (ZH -> BN)...")
    bn_pill = driver.find_element(By.XPATH, "//a[contains(text(), 'বাংলা')]")
    bn_pill.click()
    time.sleep(2)
    driver.save_screenshot(str(artifact_dir / "landing_switcher_clicked_bn.png"))
    current_body_bn = driver.find_element(By.TAG_NAME, "body").text
    assert "ফাইন্যান্স কোপাইলট" in current_body_bn, "Pill click failed to switch language to Bengali"
    print("Pill click switcher to Bengali verified successfully!")

    print("All browser verification passed cleanly!")
finally:
    driver.quit()
