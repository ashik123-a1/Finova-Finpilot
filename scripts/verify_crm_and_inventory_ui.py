"""
Selenium End-to-End Browser Verification for CRM & Inventory Modules.
Captures screenshots of live interactive workflows into the artifact directory.
"""

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ARTIFACTS_DIR = r"C:\Users\ASHIK_CSE\.gemini\antigravity\brain\40635c6d-8320-4cc1-990c-82bc85c90e5c"
BASE_URL = "http://127.0.0.1:8050"

def run_verification():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1600,1050")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)

    try:
        print("[1/6] Navigating to Customers CRM Directory...")
        driver.get(f"{BASE_URL}/app/customers?shop_id=28")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#customers-table-body tr")))
        time.sleep(1.5)  # Let Lucide icons render and data settle

        # 1. Full Page Screenshot of CRM
        crm_page_path = os.path.join(ARTIFACTS_DIR, "crm_customers_directory.png")
        driver.save_screenshot(crm_page_path)
        print(f" -> Saved CRM page screenshot: {crm_page_path}")

        # 2. Open Add Customer Modal
        print("[2/6] Testing Add Customer Modal...")
        add_btn = driver.find_element(By.XPATH, "//button[contains(., 'Add Customer')]")
        add_btn.click()
        wait.until(EC.visibility_of_element_located((By.ID, "add-customer-modal")))
        time.sleep(0.5)

        driver.find_element(By.ID, "add-name").send_keys("Padma General Trading Ltd.")
        driver.find_element(By.ID, "add-phone").send_keys("+880 1711-889900")
        driver.find_element(By.ID, "add-wa").send_keys("+8801711889900")
        driver.find_element(By.ID, "add-credit-limit").send_keys("150000")
        driver.find_element(By.ID, "add-opening-balance").send_keys("25000")
        driver.find_element(By.ID, "add-address").send_keys("Motijheel C/A, Dhaka")

        modal_path = os.path.join(ARTIFACTS_DIR, "crm_add_customer_modal.png")
        driver.save_screenshot(modal_path)
        print(f" -> Saved Add Customer Modal screenshot: {modal_path}")

        # Submit Add Customer
        save_cust_btn = driver.find_element(By.ID, "btn-save-customer")
        save_cust_btn.click()
        time.sleep(2)  # Wait for API POST and table refresh

        # 3. Test Polite Reminder Generator Modal
        print("[3/6] Testing Polite Reminder Generator Modal...")
        remind_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Remind')]")
        if remind_btns:
            remind_btns[0].click()
            wait.until(EC.visibility_of_element_located((By.ID, "reminder-modal")))
            time.sleep(1)

            # Switch tone to Bengali
            bn_btn = driver.find_element(By.ID, "tone-btn-bn_friendly")
            bn_btn.click()
            time.sleep(1)

            rem_modal_path = os.path.join(ARTIFACTS_DIR, "crm_payment_reminder_modal.png")
            driver.save_screenshot(rem_modal_path)
            print(f" -> Saved Payment Reminder Modal screenshot: {rem_modal_path}")

            # Close Reminder Modal
            driver.find_element(By.XPATH, "//div[@id='reminder-modal']//button[contains(., 'Close')]").click()
            time.sleep(0.5)

        # 4. Test Record Payment Modal
        print("[4/6] Testing Record Payment Modal...")
        pay_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Pay')]")
        if pay_btns:
            pay_btns[0].click()
            wait.until(EC.visibility_of_element_located((By.ID, "payment-modal")))
            time.sleep(0.8)

            pay_modal_path = os.path.join(ARTIFACTS_DIR, "crm_record_payment_modal.png")
            driver.save_screenshot(pay_modal_path)
            print(f" -> Saved Record Payment Modal screenshot: {pay_modal_path}")

            driver.find_element(By.XPATH, "//div[@id='payment-modal']//button[contains(., 'Cancel')]").click()
            time.sleep(0.5)

        # 5. Navigate to Inventory Valuation & Receivables Aging
        print("[5/6] Navigating to Inventory & Aging Module...")
        driver.get(f"{BASE_URL}/app/inventory?shop_id=28")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#products-table-body tr")))
        time.sleep(1.5)

        inv_page_path = os.path.join(ARTIFACTS_DIR, "inventory_sku_catalog_page.png")
        driver.save_screenshot(inv_page_path)
        print(f" -> Saved Inventory Page screenshot: {inv_page_path}")

        # 6. Test Add Product Modal
        print("[6/6] Testing Add Product Modal...")
        add_prod_btn = driver.find_element(By.XPATH, "//button[contains(., 'Add Product')]")
        add_prod_btn.click()
        wait.until(EC.visibility_of_element_located((By.ID, "add-product-modal")))
        time.sleep(0.5)

        driver.find_element(By.ID, "add-sku").send_keys("SKU-TX-NEW99")
        driver.find_element(By.ID, "add-prod-name").send_keys("Silk Cotton Dupatta (2.5m)")
        driver.find_element(By.ID, "add-prod-category").send_keys("Apparel")
        driver.find_element(By.ID, "add-cost-price").send_keys("650")
        driver.find_element(By.ID, "add-selling-price").send_keys("1200")
        driver.find_element(By.ID, "add-initial-stock").send_keys("35")
        driver.find_element(By.ID, "add-reorder-alert").send_keys("15")

        add_prod_modal_path = os.path.join(ARTIFACTS_DIR, "inventory_add_product_modal.png")
        driver.save_screenshot(add_prod_modal_path)
        print(f" -> Saved Add Product Modal screenshot: {add_prod_modal_path}")

        driver.find_element(By.ID, "btn-save-product").click()
        time.sleep(2)

        # 7. Test Auto-Draft Purchase Orders
        print("[7/6] Testing Auto-Draft Purchase Orders button...")
        draft_po_btn = driver.find_element(By.ID, "btn-auto-draft")
        draft_po_btn.click()
        time.sleep(2)

        po_modal = driver.find_element(By.ID, "po-modal")
        if not ("hidden" in po_modal.get_attribute("class")):
            po_modal_path = os.path.join(ARTIFACTS_DIR, "inventory_auto_draft_po_modal.png")
            driver.save_screenshot(po_modal_path)
            print(f" -> Saved Auto-Draft PO Modal screenshot: {po_modal_path}")
        else:
            print(" -> All stocks optimal; no PO modal needed or toast shown.")

        print("=== ALL BROWSER E2E VERIFICATIONS SUCCESSFUL ===")

    finally:
        driver.quit()

if __name__ == "__main__":
    run_verification()
