import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def run():
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--autoplay-policy=no-user-gesture-required')
    
    driver = webdriver.Chrome(options=opts)
    try:
        driver.get('http://127.0.0.1:8050/landing')
        time.sleep(2)
        
        info = driver.execute_script('''
            var v = document.getElementById("hero-bg-video");
            if (!v) return { found: false };
            return {
                found: true,
                paused: v.paused,
                currentTime: v.currentTime,
                duration: v.duration,
                readyState: v.readyState,
                networkState: v.networkState,
                muted: v.muted,
                currentSrc: v.currentSrc,
                videoWidth: v.videoWidth,
                videoHeight: v.videoHeight,
                clientWidth: v.clientWidth,
                clientHeight: v.clientHeight,
                display: window.getComputedStyle(v).display,
                visibility: window.getComputedStyle(v).visibility,
                opacity: window.getComputedStyle(v).opacity
            };
        ''')
        print("VIDEO_INFO_T0:", json.dumps(info, indent=2))
        
        time.sleep(2)
        cur_time = driver.execute_script('var v = document.getElementById("hero-bg-video"); return v ? v.currentTime : null;')
        is_paused = driver.execute_script('var v = document.getElementById("hero-bg-video"); return v ? v.paused : null;')
        print(f"VIDEO_INFO_T2: currentTime={cur_time}, paused={is_paused}")
        
    finally:
        driver.quit()

if __name__ == '__main__':
    run()
