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
    print("1. Opening Enriched Landing Page in English (?lang=en)...")
    driver.get("http://127.0.0.1:8050/landing?lang=en")
    time.sleep(2)
    driver.save_screenshot(str(artifact_dir / "landing_enriched_hero.png"))
    print("Saved landing_enriched_hero.png")

    # Scroll down to How It Works Preview and Forecast Engine
    driver.execute_script("window.scrollTo(0, 1400);")
    time.sleep(1.5)
    driver.save_screenshot(str(artifact_dir / "landing_enriched_how_it_works_preview.png"))
    print("Saved landing_enriched_how_it_works_preview.png")

    # Scroll down to CRM Receivables and Inventory Aging
    driver.execute_script("window.scrollTo(0, 2800);")
    time.sleep(1.5)
    driver.save_screenshot(str(artifact_dir / "landing_enriched_crm_and_inventory.png"))
    print("Saved landing_enriched_crm_and_inventory.png")

    # Scroll to Footer
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)
    driver.save_screenshot(str(artifact_dir / "landing_enriched_footer.png"))
    print("Saved landing_enriched_footer.png")

    # Check key text elements on Landing Page (using upper case check to handle CSS text-transform)
    body_text = driver.find_element(By.TAG_NAME, "body").text.upper()
    assert "AUTONOMOUS FINANCIAL COPILOT FOR MULTI-SHOP RETAILERS" in body_text, "Missing hero title"
    assert "PLATFORM CAPABILITIES" in body_text, "Missing footer platform section"
    assert "EXECUTIVE DASHBOARD" in body_text, "Missing footer dashboard link"
    assert "SUPER ADMIN CONSOLE" in body_text, "Missing footer admin link"
    print("Landing page text & footer elements verified!")

    # Test Navigation from Landing to 2nd Page: How It Works
    print("2. Clicking How It Works link...")
    driver.get("http://127.0.0.1:8050/landing?lang=en")
    time.sleep(1)
    how_it_works_nav = driver.find_element(By.XPATH, "//a[contains(., 'How It Works')]")
    how_it_works_nav.click()
    time.sleep(2)
    assert "/how-it-works" in driver.current_url, f"Expected /how-it-works, got {driver.current_url}"
    print(f"Navigated to: {driver.current_url}")

    driver.save_screenshot(str(artifact_dir / "how_it_works_page_hero.png"))
    print("Saved how_it_works_page_hero.png")

    # Scroll to phases
    driver.execute_script("window.scrollTo(0, 1100);")
    time.sleep(1.5)
    driver.save_screenshot(str(artifact_dir / "how_it_works_page_phases.png"))
    print("Saved how_it_works_page_phases.png")

    # Scroll to CTA and Footer
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)
    driver.save_screenshot(str(artifact_dir / "how_it_works_page_footer.png"))
    print("Saved how_it_works_page_footer.png")

    # Check 2nd page content
    page2_text = driver.find_element(By.TAG_NAME, "body").text.upper()
    assert "HOW SME FINANCE COPILOT OPERATES" in page2_text, "Missing 2nd page header"
    assert "GATED OCR & MULTILINGUAL INVOICE EXTRACTION" in page2_text, "Missing Phase 1"
    assert "CHRONOLOGICAL CASH FLOW & RUNWAY FORECASTING" in page2_text, "Missing Phase 2"
    assert "SME BANK LOAN & DSCR PRE-QUALIFICATION" in page2_text, "Missing Phase 3"
    assert "CUSTOMER RECEIVABLES RECOVERY & STOCK REORDERS" in page2_text, "Missing Phase 4"
    assert "PLATFORM CAPABILITIES" in page2_text, "Missing footer in 2nd page"
    print("How It Works 2nd page content verified successfully!")

    # Test Return to Home
    home_link = driver.find_element(By.XPATH, "//a[contains(., 'Return to Home')]")
    home_link.click()
    time.sleep(2)
    assert "/landing" in driver.current_url, f"Expected return to landing, got {driver.current_url}"
    print("Return to Home navigation verified successfully!")

    print("ALL VERIFICATIONS COMPLETED WITH 100% SUCCESS!")
finally:
    driver.quit()
