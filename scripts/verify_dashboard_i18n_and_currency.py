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
    print("1. TEST DASHBOARD IN CHINESE (lang=zh)")
    print("==================================================")
    driver.get("http://127.0.0.1:8050/app/dashboard?lang=zh")
    time.sleep(3)
    
    # Check sidebar is Chinese
    sidebar_text = driver.find_element(By.ID, "desktop-sidebar").text
    assert "控制台仪表盘" in sidebar_text or "销售总账" in sidebar_text, "Sidebar must be in Chinese"
    print("Sidebar verified in Chinese!")

    # Check main dashboard content is Chinese
    main_text = driver.find_element(By.TAG_NAME, "main").text
    print("\nSample main dashboard text snippet:")
    print(main_text[:400])

    # Assertions for main body localization in Chinese
    assert "30天营业收入" in main_text, "KPI 1 must be '30天营业收入'"
    assert "营业净利润" in main_text, "KPI 2 must be '营业净利润'"
    assert "现金与流动资产" in main_text, "KPI 3 must be '现金与流动资产'"
    assert "现金跑道与偿债备付率" in main_text, "KPI 4 must be '现金跑道与偿债备付率'"
    assert "营业收入与经营支出对比" in main_text, "Chart header must be in Chinese"
    assert "智能财务顾问" in main_text, "Advisor widget must be '智能财务顾问'"
    assert "实时交易流水动态" in main_text, "Table header must be '实时交易流水动态'"
    print("SUCCESS: Full dashboard main content is localized in Chinese!")

    shot_zh = os.path.join(ARTIFACTS_DIR, "dashboard_chinese_full_verified.png")
    driver.save_screenshot(shot_zh)
    print(f"Saved: {shot_zh}")

    print("\n==================================================")
    print("2. TEST GLOBAL CURRENCY SWITCHER (Switch to CNY)")
    print("==================================================")
    # Check global currency switcher in header
    curr_switcher = driver.find_element(By.ID, "global-currency-switcher")
    assert curr_switcher is not None, "Global currency switcher must be present in header!"
    print("Global currency switcher found in header!")

    # Switch to CNY via URL and cookie
    driver.get("http://127.0.0.1:8050/app/dashboard?lang=zh&currency=CNY")
    time.sleep(3)

    kpi_rev = driver.find_element(By.ID, "kpi-revenue").text
    kpi_profit = driver.find_element(By.ID, "kpi-profit").text
    chart_badge = driver.find_element(By.ID, "chart-currency-badge").text
    print(f"Updated KPI Revenue: {kpi_rev}")
    print(f"Updated KPI Profit: {kpi_profit}")
    print(f"Updated Chart Badge: {chart_badge}")

    assert "¥" in kpi_rev or "CNY" in kpi_rev, f"Expected ¥ or CNY in revenue, got {kpi_rev}"
    assert chart_badge == "CNY", f"Expected CNY in chart badge, got {chart_badge}"
    print("SUCCESS: Dashboard numbers and chart reactively changed to CNY (¥)!")

    shot_cny = os.path.join(ARTIFACTS_DIR, "dashboard_currency_cny_verified.png")
    driver.save_screenshot(shot_cny)
    print(f"Saved: {shot_cny}")

    print("\n==================================================")
    print("3. TEST GLOBAL CURRENCY SWITCHER (Switch to USD)")
    print("==================================================")
    driver.get("http://127.0.0.1:8050/app/dashboard?lang=en&currency=USD")
    time.sleep(3)

    kpi_rev_usd = driver.find_element(By.ID, "kpi-revenue").text
    chart_badge_usd = driver.find_element(By.ID, "chart-currency-badge").text
    print(f"Updated KPI Revenue: {kpi_rev_usd}")
    print(f"Updated Chart Badge: {chart_badge_usd}")

    assert "$" in kpi_rev_usd or "USD" in kpi_rev_usd, f"Expected $ or USD in revenue, got {kpi_rev_usd}"
    assert chart_badge_usd == "USD", f"Expected USD in chart badge, got {chart_badge_usd}"
    print("SUCCESS: Dashboard numbers and chart reactively changed to USD ($)!")

    shot_usd = os.path.join(ARTIFACTS_DIR, "dashboard_currency_usd_verified.png")
    driver.save_screenshot(shot_usd)
    print(f"Saved: {shot_usd}")

    print("\nALL DASHBOARD LOCALIZATION AND CURRENCY SWITCHING VERIFIED SUCCESSFULLY!")

except Exception as e:
    print(f"\nERROR: {e}")
    sys.exit(1)
finally:
    driver.quit()
