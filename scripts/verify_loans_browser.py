import sys
import time
sys.stdout.reconfigure(encoding='utf-8')
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1600,1200")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=chrome_options)
try:
    print("Navigating to http://127.0.0.1:8050/app/loans...")
    driver.get("http://127.0.0.1:8050/app/loans")
    time.sleep(2)

    # 1. Verify initial calculation values
    emi_initial = driver.find_element(By.ID, "res-emi").text
    dscr_initial = driver.find_element(By.ID, "res-dscr").text
    total_initial = driver.find_element(By.ID, "res-total").text
    print(f"Initial UI: EMI={emi_initial}, DSCR={dscr_initial}, Total={total_initial}")
    assert "৳" in emi_initial
    assert "x" in dscr_initial

    # 2. Change inputs and verify reactive update
    principal_input = driver.find_element(By.ID, "loan-principal")
    principal_input.clear()
    principal_input.send_keys("1500000")

    tenure_select = driver.find_element(By.ID, "loan-tenure")
    for opt in tenure_select.find_elements(By.TAG_NAME, "option"):
        if opt.get_attribute("value") == "36":
            opt.click()
            break

    rate_input = driver.find_element(By.ID, "loan-rate")
    rate_input.clear()
    rate_input.send_keys("10.0")

    time.sleep(1)

    emi_updated = driver.find_element(By.ID, "res-emi").text
    dscr_updated = driver.find_element(By.ID, "res-dscr").text
    total_updated = driver.find_element(By.ID, "res-total").text
    print(f"Updated UI: EMI={emi_updated}, DSCR={dscr_updated}, Total={total_updated}")

    assert emi_updated != emi_initial, "EMI did not update reactively!"
    assert dscr_updated != dscr_initial, "DSCR did not update reactively!"
    print("SUCCESS: Input change visibly updated EMI, DSCR, and Total Repayment!")

    # 3. Verify bank product cards rendered dynamically
    time.sleep(1.5)
    product_cards = driver.find_elements(By.CSS_SELECTOR, "#bank-products-container > div")
    print(f"Rendered Bank Product Cards: {len(product_cards)}")
    assert len(product_cards) > 0, "No bank product cards rendered!"

    # 4. Click 'Generate Bank Loan Packet'
    gen_btn = driver.find_element(By.ID, "btn-generate-packet")
    driver.execute_script("arguments[0].click();", gen_btn)
    print("Clicked 'Generate Bank Loan Packet' button...")

    # Wait for modal to become visible
    WebDriverWait(driver, 10).until(
        lambda d: "hidden" not in d.find_element(By.ID, "loan-packet-modal").get_attribute("class")
    )
    print("Modal successfully appeared!")

    modal_app_ref = driver.find_element(By.ID, "modal-app-ref").text
    modal_principal = driver.find_element(By.ID, "modal-principal").text
    modal_emi = driver.find_element(By.ID, "modal-emi").text
    modal_dscr = driver.find_element(By.ID, "modal-dscr").text
    dl_link = driver.find_element(By.ID, "modal-download-link").get_attribute("href")

    print(f"Modal Data: Ref={modal_app_ref}, Principal={modal_principal}, EMI={modal_emi}, DSCR={modal_dscr}")
    print(f"Download PDF Link: {dl_link}")

    assert "SME-PKT-" in modal_app_ref, "Application reference not generated!"
    assert "/download" in dl_link, "Download link not wired properly!"

    # Save screenshot of modal
    driver.save_screenshot("loan_packet_modal_verified.png")
    print("Saved screenshot to loan_packet_modal_verified.png")

finally:
    driver.quit()
