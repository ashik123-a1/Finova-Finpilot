import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def run_audit():
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=opts)

    try:
        # 1. Login
        driver.get('http://127.0.0.1:8050/login')
        time.sleep(1)

        # Execute demo login for owner
        driver.execute_script("loginWithDemoPersona('owner');")
        time.sleep(3)

        # 2. Go to /app/loans
        driver.get('http://127.0.0.1:8050/app/loans')
        time.sleep(2)

        initial = driver.execute_script("""
            return {
                url: window.location.href,
                hasCalculateFn: typeof window.calculateLoanEvaluation === 'function',
                hasGenerateFn: typeof window.generateBankDossier === 'function',
                principal: document.getElementById('loan-principal') ? document.getElementById('loan-principal').value : null,
                emi: document.getElementById('res-emi') ? document.getElementById('res-emi').innerText : null,
                interest: document.getElementById('res-interest') ? document.getElementById('res-interest').innerText : null,
                total: document.getElementById('res-total') ? document.getElementById('res-total').innerText : null,
                dscr: document.getElementById('res-dscr') ? document.getElementById('res-dscr').innerText : null,
                dti: document.getElementById('res-dti') ? document.getElementById('res-dti').innerText : null,
                badge: document.getElementById('loan-verdict-badge') ? document.getElementById('loan-verdict-badge').innerText : null
            };
        """)
        print("INITIAL LOAN STATE:", json.dumps(initial, indent=2))

        # Test 1: Change principal to 1,500,000
        driver.execute_script("""
            var p = document.getElementById('loan-principal');
            if (p) {
                p.value = '1500000';
                p.dispatchEvent(new Event('input', { bubbles: true }));
                p.dispatchEvent(new Event('change', { bubbles: true }));
            }
        """)
        time.sleep(1)

        after_principal = driver.execute_script("""
            return {
                principal: document.getElementById('loan-principal').value,
                emi: document.getElementById('res-emi').innerText,
                interest: document.getElementById('res-interest').innerText,
                total: document.getElementById('res-total').innerText,
                dscr: document.getElementById('res-dscr').innerText,
                dti: document.getElementById('res-dti').innerText,
                badge: document.getElementById('loan-verdict-badge').innerText
            };
        """)
        print("\nAFTER PRINCIPAL = 1,500,000:", json.dumps(after_principal, indent=2))

        # Test 2: Check Bank Products in comparison matrix
        products = driver.execute_script("""
            var cards = document.querySelectorAll('.glass-panel:nth-of-type(2) .grid > div, .grid-cols-1.md\\\\:grid-cols-3 > div');
            var result = [];
            cards.forEach(function(c) {
                result.push({
                    text: c.innerText.replace(/\\n+/g, ' | ')
                });
            });
            return result;
        """)
        print("\nBANK PRODUCTS DISPLAYED:", json.dumps(products, indent=2))

        # Test 3: Click Generate Bank Loan Packet
        driver.execute_script("""
            var btn = document.querySelector('button[onclick*="generateBankDossier"]');
            if (btn) btn.click();
        """)
        time.sleep(1.5)

        toast = driver.execute_script("""
            var t = document.getElementById('toast-container');
            return t ? t.innerText : null;
        """)
        modal = driver.execute_script("""
            return {
                modal: !!document.getElementById('loan-packet-modal'),
                drawer: !!document.getElementById('loan-packet-drawer'),
                anyModal: !!document.querySelector('.modal, [role="dialog"]')
            };
        """)
        print("\nCLICK 'Generate Bank Loan Packet' RESULT:")
        print("Toast:", toast)
        print("Modal/Drawer:", json.dumps(modal, indent=2))

    finally:
        driver.quit()

if __name__ == '__main__':
    run_audit()
