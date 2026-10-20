import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

opt = Options()
opt.add_argument('--headless=new')
opt.add_argument('--window-size=1440,900')
driver = webdriver.Chrome(options=opt)

try:
    driver.get('http://127.0.0.1:8050/landing')
    time.sleep(2)

    # 1. Capture #how-it-works-preview
    el1 = driver.find_element('id', 'how-it-works-preview')
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el1)
    time.sleep(1)
    driver.save_screenshot(r'C:\Users\ASHIK_CSE\.gemini\antigravity\brain\40635c6d-8320-4cc1-990c-82bc85c90e5c\fixed_how_it_works_preview_bg.png')

    # 2. Capture #sandbox
    el2 = driver.find_element('id', 'sandbox')
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el2)
    time.sleep(1)
    driver.save_screenshot(r'C:\Users\ASHIK_CSE\.gemini\antigravity\brain\40635c6d-8320-4cc1-990c-82bc85c90e5c\fixed_sandbox_bg.png')

    print("Screenshots captured successfully!")
finally:
    driver.quit()
