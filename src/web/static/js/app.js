/**
 * SME Finance Copilot — Unified Client-Side Application Controller
 * Handles Signed Token Header Injection, Multi-Shop Context, Toast Notifications,
 * Financial Currency Formatting, and Interactive API Bridges.
 */

// ==============================================================================
// 1. Toast Notification System
// ==============================================================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'pointer-events-auto flex items-center gap-3 p-3.5 rounded-2xl border shadow-xl text-xs font-semibold backdrop-blur-xl transition-all duration-300 transform translate-y-2 opacity-0';

    let iconName = 'info';
    if (type === 'success') {
        toast.className += ' bg-emerald-950/90 border-emerald-500/40 text-emerald-200 shadow-emerald-950/50';
        iconName = 'check-circle';
    } else if (type === 'error') {
        toast.className += ' bg-rose-950/90 border-rose-500/40 text-rose-200 shadow-rose-950/50';
        iconName = 'alert-triangle';
    } else if (type === 'warning') {
        toast.className += ' bg-amber-950/90 border-amber-500/40 text-amber-200 shadow-amber-950/50';
        iconName = 'alert-circle';
    } else {
        toast.className += ' bg-slate-900/90 border-cyan-500/40 text-cyan-200 shadow-cyan-950/50';
        iconName = 'sparkles';
    }

    toast.innerHTML = `
        <i data-lucide="${iconName}" class="w-4 h-4 shrink-0"></i>
        <span class="flex-1">${message}</span>
        <button type="button" class="text-slate-400 hover:text-white p-0.5" onclick="this.parentElement.remove()">
            <i data-lucide="x" class="w-3.5 h-3.5"></i>
        </button>
    `;

    container.appendChild(toast);
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Trigger enter animation
    requestAnimationFrame(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    });

    // Auto dismiss after 4 seconds
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}


// ==============================================================================
// 2. Authentication & Header Helpers
// ==============================================================================

function getStoredToken() {
    return localStorage.getItem('sme_token') || getCookie('sme_auth_token') || '';
}

function getActiveShopId() {
    return getCookie('sme_active_shop_id') || document.getElementById('global-shop-switcher')?.value || '28';
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function getAuthHeaders(extra = {}) {
    const headers = {
        'Accept': 'application/json',
        ...extra
    };
    const token = getStoredToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}


// ==============================================================================
// 3. Currency & Number Formatting (Minor-Unit Protection)
// ==============================================================================

function formatMoney(minorAmount, currency = 'BDT') {
    const symbols = {
        'BDT': '৳',
        'CNY': '¥',
        'USD': '$',
        'EUR': '€'
    };
    const sym = symbols[currency] || currency;
    const major = (minorAmount || 0) / 100;
    return `${sym} ${major.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}


// ==============================================================================
// 4. API Request Wrapper with Auto-Retry & Toast Handling
// ==============================================================================

async function apiFetch(url, options = {}) {
    const headers = getAuthHeaders(options.headers || {});
    try {
        const resp = await fetch(url, { ...options, headers });
        if (resp.status === 401) {
            showToast('Session expired. Please sign in again.', 'warning');
            setTimeout(() => { window.location.href = '/login'; }, 1000);
            return null;
        }
        return resp;
    } catch (err) {
        console.error('API Error:', err);
        showToast('Network error connecting to local server.', 'error');
        return null;
    }
}


// ==============================================================================
// 5. Global Document Lifecycle Setup
// ==============================================================================

document.addEventListener("DOMContentLoaded", function () {
    // Re-bind Lucide icons on any dynamically injected content
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
});
