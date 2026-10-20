import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def verify_all():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1440,1050")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=chrome_options)
    artifact_dir = r"C:\Users\ASHIK_CSE\.gemini\antigravity\brain\40635c6d-8320-4cc1-990c-82bc85c90e5c"
    base_url = "http://127.0.0.1:8050"

    try:
        # 1. Landing Page Hero (Untouched)
        print("Visiting /landing ...")
        driver.get(f"{base_url}/landing")
        time.sleep(2)
        driver.save_screenshot(os.path.join(artifact_dir, "landing_bg_hero_untouched.png"))

        # Scroll to features & how-it-works
        driver.execute_script("window.scrollTo(0, 1100);")
        time.sleep(1)
        driver.save_screenshot(os.path.join(artifact_dir, "landing_bg_features_and_preview.png"))

        # Scroll to forecast & sandbox
        driver.execute_script("window.scrollTo(0, 2000);")
        time.sleep(1)
        driver.save_screenshot(os.path.join(artifact_dir, "landing_bg_forecast_and_sandbox.png"))

        # Scroll to crm & inventory
        driver.execute_script("window.scrollTo(0, 2900);")
        time.sleep(1)
        driver.save_screenshot(os.path.join(artifact_dir, "landing_bg_crm_and_inventory.png"))

        # Scroll to models & security
        driver.execute_script("window.scrollTo(0, 3800);")
        time.sleep(1)
        driver.save_screenshot(os.path.join(artifact_dir, "landing_bg_models_and_security.png"))

        # 2. How It Works Page
        print("Visiting /how-it-works ...")
        driver.get(f"{base_url}/how-it-works")
        time.sleep(2)
        driver.save_screenshot(os.path.join(artifact_dir, "how_it_works_bg_hero.png"))

        driver.execute_script("window.scrollTo(0, 1100);")
        time.sleep(1)
        driver.save_screenshot(os.path.join(artifact_dir, "how_it_works_bg_phases1_2.png"))

        driver.execute_script("window.scrollTo(0, 2000);")
        time.sleep(1)
        driver.save_screenshot(os.path.join(artifact_dir, "how_it_works_bg_phases3_4.png"))

        driver.execute_script("window.scrollTo(0, 2900);")
        time.sleep(1)
        driver.save_screenshot(os.path.join(artifact_dir, "how_it_works_bg_phases5_6.png"))

        driver.execute_script("window.scrollTo(0, 3800);")
        time.sleep(1)
        driver.save_screenshot(os.path.join(artifact_dir, "how_it_works_bg_cta_and_footer.png"))

        # 3. Login Page
        print("Visiting /login ...")
        driver.get(f"{base_url}/login")
        time.sleep(2)
        driver.save_screenshot(os.path.join(artifact_dir, "login_bg_skyline_dusk.png"))

        print("Visual verification screenshots saved successfully!")
    finally:
        driver.quit()

if __name__ == "__main__":
    verify_all()
