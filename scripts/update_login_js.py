from pathlib import Path

login_path = Path("F:/china project/src/web/templates/login.html")
content = login_path.read_text(encoding="utf-8")

old_fn = """async function loginWithDemoPersona(role) {
    showToast(`Signing in as ${role}...`, 'info');
    const btn = document.getElementById('btn-continue-demo');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="animate-spin mr-2">◌</span> Authenticating as ${personaTitles[role] || role}...`;
    }
    try {
        const resp = await fetch('/api/auth/demo-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ persona: role })
        });

        if (resp.ok) {
            const data = await resp.json();
            document.cookie = `sme_auth_token=${data.token}; path=/; max-age=86400`;
            document.cookie = `sme_role=${data.role_code}; path=/; max-age=86400`;
            if (data.business_id) document.cookie = `sme_active_business_id=${data.business_id}; path=/; max-age=86400`;
            if (data.shop_id) document.cookie = `sme_active_shop_id=${data.shop_id}; path=/; max-age=86400`;
            localStorage.setItem('sme_token', data.token);
            localStorage.setItem('sme_role', data.role_code);
            showToast(`Authenticated as ${data.full_name} (${data.role_code})!`, 'success');
            setTimeout(() => { window.location.href = data.redirect_url || '/app/dashboard'; }, 300);
        } else {
            const err = await resp.json().catch(() => ({}));
            showToast(err.detail || `Failed to sign in as ${role}`, 'error');
        }
    } catch (err) {
        showToast(`Connection error while signing in as ${role}`, 'error');
    }
}"""

new_fn = """async function loginWithDemoPersona(role) {
    const ownerBtn = document.getElementById('demo-btn-owner');
    const adminBtn = document.getElementById('demo-btn-admin');
    const ownerSpinner = document.getElementById('demo-spinner-owner');
    const adminSpinner = document.getElementById('demo-spinner-admin');
    const modalBtn = document.getElementById('btn-continue-demo');

    if (role === 'owner') {
        if (ownerSpinner) ownerSpinner.classList.remove('hidden');
        if (ownerBtn) ownerBtn.classList.add('opacity-75', 'pointer-events-none');
    } else if (role === 'super_admin' || role === 'admin') {
        if (adminSpinner) adminSpinner.classList.remove('hidden');
        if (adminBtn) adminBtn.classList.add('opacity-75', 'pointer-events-none');
    }

    if (modalBtn) {
        modalBtn.disabled = true;
        modalBtn.innerHTML = `<span class="animate-spin mr-2">◌</span> Authenticating as ${personaTitles[role] || role}...`;
    }

    const roleName = personaTitles[role] || role;
    showToast(`Signing in as Demo ${roleName}...`, 'info');

    try {
        const resp = await fetch('/api/auth/demo-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ persona: role })
        });

        if (resp.ok) {
            const data = await resp.json();
            document.cookie = `sme_auth_token=${data.token}; path=/; max-age=86400`;
            document.cookie = `sme_role=${data.role_code}; path=/; max-age=86400`;
            if (data.business_id) document.cookie = `sme_active_business_id=${data.business_id}; path=/; max-age=86400`;
            if (data.shop_id) document.cookie = `sme_active_shop_id=${data.shop_id}; path=/; max-age=86400`;
            localStorage.setItem('sme_token', data.token);
            localStorage.setItem('sme_role', data.role_code);
            showToast(`Authenticated as ${data.full_name} (${data.role_code})!`, 'success');
            setTimeout(() => {
                window.location.href = data.redirect_url || (role === 'super_admin' || role === 'admin' ? '/app/admin' : '/app/dashboard');
            }, 300);
        } else {
            const err = await resp.json().catch(() => ({}));
            showToast(err.detail || `Failed to sign in as ${role}`, 'error');
            if (ownerSpinner) ownerSpinner.classList.add('hidden');
            if (adminSpinner) adminSpinner.classList.add('hidden');
            if (ownerBtn) ownerBtn.classList.remove('opacity-75', 'pointer-events-none');
            if (adminBtn) adminBtn.classList.remove('opacity-75', 'pointer-events-none');
            if (modalBtn) {
                modalBtn.disabled = false;
                modalBtn.innerHTML = `<i data-lucide="log-in" class="w-4 h-4"></i><span>Continue as Demo ${personaTitles[role] || role}</span>`;
                if (typeof lucide !== 'undefined') lucide.createIcons();
            }
        }
    } catch (err) {
        showToast(`Connection error while signing in as ${role}`, 'error');
        if (ownerSpinner) ownerSpinner.classList.add('hidden');
        if (adminSpinner) adminSpinner.classList.add('hidden');
        if (ownerBtn) ownerBtn.classList.remove('opacity-75', 'pointer-events-none');
        if (adminBtn) adminBtn.classList.remove('opacity-75', 'pointer-events-none');
        if (modalBtn) {
            modalBtn.disabled = false;
            modalBtn.innerHTML = `<i data-lucide="log-in" class="w-4 h-4"></i><span>Continue as Demo ${personaTitles[role] || role}</span>`;
            if (typeof lucide !== 'undefined') lucide.createIcons();
        }
    }
}"""

norm_content = content.replace("\r\n", "\n")
norm_old = old_fn.replace("\r\n", "\n")
norm_new = new_fn.replace("\r\n", "\n")

if norm_old in norm_content:
    updated = norm_content.replace(norm_old, norm_new, 1)
    login_path.write_text(updated, encoding="utf-8")
    print("SUCCESS: Updated loginWithDemoPersona function.")
else:
    print("ERROR: old_fn not found.")
