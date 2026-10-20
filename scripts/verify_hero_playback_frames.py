import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def capture_scenes():
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('--autoplay-policy=no-user-gesture-required')

    driver = webdriver.Chrome(options=opts)
    try:
        driver.get('http://127.0.0.1:8050/landing')
        time.sleep(1.5)

        # Check scene 1 (Skyscrapers, t~2s)
        driver.execute_script('var v = document.getElementById("hero-bg-video"); if (v) v.currentTime = 2.0;')
        time.sleep(0.5)
        driver.save_screenshot('C:/Users/ASHIK_CSE/.gemini/antigravity/brain/40635c6d-8320-4cc1-990c-82bc85c90e5c/playback_scene1_skyscrapers.png')

        # Check scene 2 (Monoliths + SME FINOVA COPILOT HUD, t~7s)
        driver.execute_script('var v = document.getElementById("hero-bg-video"); if (v) v.currentTime = 7.0;')
        time.sleep(0.5)
        driver.save_screenshot('C:/Users/ASHIK_CSE/.gemini/antigravity/brain/40635c6d-8320-4cc1-990c-82bc85c90e5c/playback_scene2_hud.png')

        # Check scene 3 (Candlestick charts, t~12s)
        driver.execute_script('var v = document.getElementById("hero-bg-video"); if (v) v.currentTime = 12.0;')
        time.sleep(0.5)
        driver.save_screenshot('C:/Users/ASHIK_CSE/.gemini/antigravity/brain/40635c6d-8320-4cc1-990c-82bc85c90e5c/playback_scene3_candlestick.png')

        print("All 3 scene screenshots captured successfully!")
    finally:
        driver.quit()

if __name__ == '__main__':
    capture_scenes()
