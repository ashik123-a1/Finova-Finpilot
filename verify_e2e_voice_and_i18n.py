import urllib.request
import json
import http.cookiejar

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

print("=== 1. TEST DEFAULT ENGLISH ===")
res = opener.open("http://127.0.0.1:8050/landing")
html = res.read().decode("utf-8")
print("Default Landing has lang=\"en\":", 'lang="en"' in html)

print("\n=== 2. SWITCH LANGUAGE TO BENGALI ON LANDING PAGE ===")
res_bn = opener.open("http://127.0.0.1:8050/landing?lang=bn")
html_bn = res_bn.read().decode("utf-8")
print("Landing with ?lang=bn has lang=\"bn\":", 'lang="bn"' in html_bn)

cookies = {c.name: c.value for c in cookie_jar}
print("Stored Cookies:", cookies)

print("\n=== 3. LOGIN AS STORE OWNER (DEMO) ===")
login_data = json.dumps({"persona": "owner"}).encode("utf-8")
req_login = urllib.request.Request(
    "http://127.0.0.1:8050/api/auth/demo-login",
    data=login_data,
    headers={"Content-Type": "application/json"}
)
res_login = opener.open(req_login)
login_res = json.loads(res_login.read().decode("utf-8"))
auth_token = login_res.get("token")
print("Login successful! Role:", login_res.get("role_code"))

print("\n=== 4. VERIFY INTERNAL PAGES PERSIST BENGALI WITHOUT ?lang= PARAM ===")
test_pages = [
    "/app/dashboard",
    "/app/finance",
    "/app/forecast",
    "/app/loans",
    "/app/inventory",
    "/app/customers",
    "/app/simulations",
    "/app/copilot",
    "/app/voice",
    "/app/settings"
]

all_passed = True
for page in test_pages:
    req = urllib.request.Request(f"http://127.0.0.1:8050{page}")
    req.add_header("Authorization", f"Bearer {auth_token}")
    with opener.open(req) as resp:
        page_html = resp.read().decode("utf-8")
        is_bn = 'lang="bn"' in page_html
        has_nav_voice = 'voice_control' in page_html or 'ভয়েস কন্ট্রোল' in page_html or 'ভয়েস' in page_html
        has_bengali_words = any(w in page_html for w in ['ড্যাশবোর্ড', 'আর্থিক', 'পূর্বাভাস', 'ঋণ', 'ইনভেন্টরি', 'কাস্টমার', 'কপিলট', 'ভয়েস', 'সেটিংস', 'হিসাব'])
        status_line = f"  {page:20} -> lang=\"bn\": {is_bn} | Bengali Text Found: {has_bengali_words} | Voice UI: {has_nav_voice}"
        print(status_line)
        if not is_bn or not has_bengali_words:
            all_passed = False

print("\n=== 5. VERIFY SUPER ADMIN PORTAL PERSISTENCE ===")
login_admin_data = json.dumps({"persona": "super_admin"}).encode("utf-8")
req_admin_login = urllib.request.Request(
    "http://127.0.0.1:8050/api/auth/demo-login",
    data=login_admin_data,
    headers={"Content-Type": "application/json"}
)
res_admin_login = opener.open(req_admin_login)
admin_res = json.loads(res_admin_login.read().decode("utf-8"))
admin_token = admin_res.get("token")

req_admin = urllib.request.Request("http://127.0.0.1:8050/app/admin")
req_admin.add_header("Authorization", f"Bearer {admin_token}")
with opener.open(req_admin) as resp:
    admin_html = resp.read().decode("utf-8")
    is_bn = 'lang="bn"' in admin_html
    has_bengali_admin = any(w in admin_html for w in ['সুপার অ্যাডমিন', 'প্ল্যাটফর্ম', 'সিস্টেম', 'ডাটাবেস', 'ভয়েস কন্ট্রোল', 'সার্ভার'])
    print(f"  /app/admin           -> lang=\"bn\": {is_bn} | Bengali Admin Found: {has_bengali_admin}")
    if not is_bn or not has_bengali_admin:
        all_passed = False

print("\n=== 6. VERIFY CHINESE PERSISTENCE ===")
opener.open("http://127.0.0.1:8050/landing?lang=zh")
for page in ["/app/dashboard", "/app/finance", "/app/voice", "/app/admin"]:
    req = urllib.request.Request(f"http://127.0.0.1:8050{page}")
    req.add_header("Authorization", f"Bearer {admin_token}")
    with opener.open(req) as resp:
        zh_html = resp.read().decode("utf-8")
        is_zh = 'lang="zh"' in zh_html
        has_zh_words = any(w in zh_html for w in ['仪表盘', '财务', '语音控制', '管理员', '设置', '中小企业'])
        print(f"  {page:20} -> lang=\"zh\": {is_zh} | Chinese Found: {has_zh_words}")
        if not is_zh or not has_zh_words:
            all_passed = False

print(f"\n=== RESULT: ALL E2E PERSISTENCE & LOCALIZATION TESTS PASSED: {all_passed} ===")
