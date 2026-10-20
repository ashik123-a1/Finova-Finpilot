import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ARTIFACT_DIR = r"C:\Users\ASHIK_CSE\.gemini\antigravity\brain\40635c6d-8320-4cc1-990c-82bc85c90e5c"
BASE_URL = "http://127.0.0.1:8050"

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--window-size=1440,900")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("--disable-gpu")
opts.add_argument("--force-device-scale-factor=1")

driver = webdriver.Chrome(options=opts)
wait = WebDriverWait(driver, 10)

try:
    print("[1/6] Capturing Bengali Landing Page...")
    driver.get(f"{BASE_URL}/landing?lang=bn")
    time.sleep(1.5)
    driver.save_screenshot(os.path.join(ARTIFACT_DIR, "verified_landing_bengali.png"))

    print("[2/6] Performing 1-Click Demo Login as Store Owner...")
    driver.get(f"{BASE_URL}/login")
    time.sleep(1.0)
    owner_btn = wait.until(EC.element_to_be_clickable((By.ID, "demo-btn-owner")))
    owner_btn.click()
    time.sleep(1.5)

    print("[3/6] Capturing Localized Executive Dashboard (/app/dashboard)...")
    wait.until(EC.presence_of_element_located((By.XPATH, "//body")))
    time.sleep(1.5)
    driver.save_screenshot(os.path.join(ARTIFACT_DIR, "verified_dashboard_bengali.png"))

    print("[4/6] Capturing Dedicated Voice Control Cyber HUD (/app/voice)...")
    driver.get(f"{BASE_URL}/app/voice")
    time.sleep(1.5)
    driver.save_screenshot(os.path.join(ARTIFACT_DIR, "verified_voice_hud_initial.png"))

    # Click first prompt chip to test active financial response HUD
    try:
        chips = driver.find_elements(By.CSS_SELECTOR, "button[onclick*='submitQuery']")
        if chips:
            print(f"Clicking prompt chip: '{chips[0].text}'")
            chips[0].click()
            time.sleep(1.5)
            driver.save_screenshot(os.path.join(ARTIFACT_DIR, "verified_voice_hud_response.png"))
    except Exception as e:
        print("Prompt click note:", e)

    print("[5/6] Capturing Localized Financial Statements (/app/finance)...")
    driver.get(f"{BASE_URL}/app/finance")
    time.sleep(1.5)
    driver.save_screenshot(os.path.join(ARTIFACT_DIR, "verified_finance_bengali.png"))

    print("[6/6] Capturing Localized Platform Super Admin Portal (/app/admin)...")
    driver.get(f"{BASE_URL}/login")
    time.sleep(1.0)
    admin_btn = wait.until(EC.element_to_be_clickable((By.ID, "demo-btn-admin")))
    admin_btn.click()
    time.sleep(1.5)
    driver.get(f"{BASE_URL}/app/admin")
    time.sleep(1.5)
    driver.save_screenshot(os.path.join(ARTIFACT_DIR, "verified_admin_portal_bengali.png"))

    print("\nAll 6 browser verification screenshots captured successfully!")

finally:
    driver.quit()
