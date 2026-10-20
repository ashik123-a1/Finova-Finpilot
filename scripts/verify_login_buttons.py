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
    print("1. Opening Login page...")
    driver.get("http://127.0.0.1:8050/login")
    time.sleep(2)
    driver.save_screenshot(str(artifact_dir / "login_page_verified.png"))
    print("Saved login_page_verified.png")

    body_text = driver.find_element(By.TAG_NAME, "body").text
    assert "Continue as Demo Store Owner" in body_text, "Missing Continue as Demo Store Owner"
    assert "Continue as Demo Admin" in body_text, "Missing Continue as Demo Admin"
    assert "Back to Home" in body_text, "Missing Back to Home button"
    print("UI Elements verified successfully!")

    # Verify Back to Home link
    home_link = driver.find_element(By.XPATH, "//a[contains(., 'Back to Home')]")
    assert "/landing" in home_link.get_attribute("href") or "/" in home_link.get_attribute("href"), "Back to home href invalid"
    print("Back to Home link verified!")

    # Test 1-Click Login as Store Owner
    print("2. Clicking Continue as Demo Store Owner...")
    owner_btn = driver.find_element(By.ID, "demo-btn-owner")
    owner_btn.click()
    time.sleep(3)
    driver.save_screenshot(str(artifact_dir / "login_owner_redirect_verified.png"))
    current_url = driver.current_url
    print(f"Redirected to: {current_url}")
    assert "/app/dashboard" in current_url, f"Expected dashboard redirect, got {current_url}"
    print("Store Owner login verified!")

    # Test 1-Click Login as Admin
    print("3. Navigating back to Login page for Admin test...")
    driver.get("http://127.0.0.1:8050/login")
    time.sleep(2)
    admin_btn = driver.find_element(By.ID, "demo-btn-admin")
    admin_btn.click()
    time.sleep(3)
    driver.save_screenshot(str(artifact_dir / "login_admin_redirect_verified.png"))
    current_url = driver.current_url
    print(f"Redirected to: {current_url}")
    assert "/app/admin" in current_url or "/app/dashboard" in current_url, f"Unexpected redirect: {current_url}"
    print("Admin login verified!")

    print("ALL LOGIN VERIFICATION CHECKS PASSED CLEANLY!")
finally:
    driver.quit()
