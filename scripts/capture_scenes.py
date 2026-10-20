import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def main():
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('--autoplay-policy=no-user-gesture-required')

    driver = webdriver.Chrome(options=opts)
    try:
        driver.get('http://127.0.0.1:8050/landing')
        time.sleep(2)

        # Scene 1
        t1 = driver.execute_script("return document.getElementById('hero-bg-video').currentTime;")
        p1 = 'C:/Users/ASHIK_CSE/.gemini/antigravity/brain/40635c6d-8320-4cc1-990c-82bc85c90e5c/desktop_scene1.png'
        driver.save_screenshot(p1)
        print(f"Captured scene 1 at t={t1:.2f}s")

        # Let it play into Scene 2
        time.sleep(5)
        t2 = driver.execute_script("return document.getElementById('hero-bg-video').currentTime;")
        p2 = 'C:/Users/ASHIK_CSE/.gemini/antigravity/brain/40635c6d-8320-4cc1-990c-82bc85c90e5c/desktop_scene2.png'
        driver.save_screenshot(p2)
        print(f"Captured scene 2 at t={t2:.2f}s")

        # Let it play into Scene 3
        time.sleep(5)
        t3 = driver.execute_script("return document.getElementById('hero-bg-video').currentTime;")
        p3 = 'C:/Users/ASHIK_CSE/.gemini/antigravity/brain/40635c6d-8320-4cc1-990c-82bc85c90e5c/desktop_scene3.png'
        driver.save_screenshot(p3)
        print(f"Captured scene 3 at t={t3:.2f}s")

        # Check loop back
        time.sleep(3)
        t4 = driver.execute_script("return document.getElementById('hero-bg-video').currentTime;")
        print(f"Captured loop at t={t4:.2f}s")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
