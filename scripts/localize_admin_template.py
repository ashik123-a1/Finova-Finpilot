import re

def localize_admin():
    path = "src/web/templates/app/admin.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replacements
    replacements = [
        ('{% block page_title %}Platform Super Admin Oversight{% endblock %}', '{% block page_title %}{{ _(\'admin.title\') }}{% endblock %}'),
        ('{% block page_subtitle %}Infrastructure health, multi-tenant directory, and global security audit stream{% endblock %}', '{% block page_subtitle %}{{ _(\'admin.subtitle\') }}{% endblock %}'),
        ('<span>Platform Super Administrator Mode</span>', '<span>{{ _(\'admin.super_admin_mode\') }}</span>'),
        ('Global Telemetry & Tenant Isolation', '{{ _(\'admin.telemetry_isolation\') }}'),
        ('Operating outside individual tenant boundaries. System actions are cryptographically logged in the immutable platform security stream.', '{{ _(\'admin.operating_outside\') }}'),
        ('<span>Refresh Telemetry</span>', '<span>{{ _(\'admin.refresh_telemetry\') }}</span>'),
        ('<span class="text-[10px] font-mono uppercase text-purple-300 font-semibold">Total Users</span>', '<span class="text-[10px] font-mono uppercase text-purple-300 font-semibold">{{ _(\'admin.total_users\') }}</span>'),
        ('<i data-lucide="check" class="w-3 h-3"></i> Active accounts', '<i data-lucide="check" class="w-3 h-3"></i> {{ _(\'admin.active_accounts\') }}'),
        ('<span class="text-[10px] font-mono uppercase text-purple-300 font-semibold">Workspaces</span>', '<span class="text-[10px] font-mono uppercase text-purple-300 font-semibold">{{ _(\'admin.total_workspaces\') }}</span>'),
        ('<i data-lucide="shield" class="w-3 h-3"></i> Isolated tenants', '<i data-lucide="shield" class="w-3 h-3"></i> {{ _(\'admin.isolated_tenants\') }}'),
        ('<span class="text-[10px] font-mono uppercase text-purple-300 font-semibold">Total Branches</span>', '<span class="text-[10px] font-mono uppercase text-purple-300 font-semibold">{{ _(\'admin.total_branches\') }}</span>'),
        ('<i data-lucide="store" class="w-3 h-3"></i> Outlets registered', '<i data-lucide="store" class="w-3 h-3"></i> {{ _(\'admin.outlets_registered\') }}'),
        ('<span class="text-[10px] font-mono uppercase text-purple-300 font-semibold">Synthetic Pods</span>', '<span class="text-[10px] font-mono uppercase text-purple-300 font-semibold">{{ _(\'admin.synthetic_pods\') }}</span>'),
        ('<i data-lucide="flask-conical" class="w-3 h-3"></i> Demo sandboxes', '<i data-lucide="flask-conical" class="w-3 h-3"></i> {{ _(\'admin.demo_sandboxes\') }}'),
        ('<span class="text-[10px] font-mono uppercase text-purple-300 font-semibold">AI Models</span>', '<span class="text-[10px] font-mono uppercase text-purple-300 font-semibold">{{ _(\'admin.ai_models\') }}</span>'),
        ('<i data-lucide="cpu" class="w-3 h-3"></i> Active in registry', '<i data-lucide="cpu" class="w-3 h-3"></i> {{ _(\'admin.active_in_registry\') }}'),
        ('<span class="text-[10px] font-mono uppercase text-purple-300 font-semibold">Audit Logs</span>', '<span class="text-[10px] font-mono uppercase text-purple-300 font-semibold">{{ _(\'admin.total_audits\') }}</span>'),
        ('<i data-lucide="file-check" class="w-3 h-3"></i> Tamper-evident', '<i data-lucide="file-check" class="w-3 h-3"></i> {{ _(\'admin.tamper_evident\') }}'),
        ('<span class="text-xs font-bold text-white">Active Tenants & Workspaces</span>', '<span class="text-xs font-bold text-white">{{ _(\'admin.active_tenants_title\') }}</span>'),
        ('<span>Open Workspaces</span>', '<span>{{ _(\'admin.open_workspaces\') }}</span>'),
        ('<span class="text-xs font-bold text-white">Security & Audit Event Stream</span>', '<span class="text-xs font-bold text-white">{{ _(\'admin.security_stream_title\') }}</span>'),
        ('<span>Open Audit Stream</span>', '<span>{{ _(\'admin.open_audit_stream\') }}</span>'),
        ('<span class="text-xs font-bold text-white block group-hover:text-emerald-300 transition-colors">Users & Directory</span>', '<span class="text-xs font-bold text-white block group-hover:text-emerald-300 transition-colors">{{ _(\'admin.users\') }}</span>'),
        ('<span class="text-[10px] text-slate-400">Manage 320+ accounts and tenant scopes</span>', '<span class="text-[10px] text-slate-400">{{ _(\'admin.users_directory_desc\') }}</span>'),
        ('<span class="text-xs font-bold text-white block group-hover:text-amber-300 transition-colors">Roles & RBAC Matrix</span>', '<span class="text-xs font-bold text-white block group-hover:text-amber-300 transition-colors">{{ _(\'admin.roles\') }}</span>'),
        ('<span class="text-[10px] text-slate-400">7 canonical least-privilege roles</span>', '<span class="text-[10px] text-slate-400">{{ _(\'admin.roles_rbac_desc\') }}</span>'),
        ('<span class="text-xs font-bold text-white block group-hover:text-indigo-300 transition-colors">System Health & DB</span>', '<span class="text-xs font-bold text-white block group-hover:text-indigo-300 transition-colors">{{ _(\'admin.system_health\') }}</span>'),
        ('<span class="text-[10px] text-slate-400">WAL mode, foreign keys, telemetry</span>', '<span class="text-[10px] text-slate-400">{{ _(\'admin.system_health_desc\') }}</span>'),
        ('<h3 class="text-xs font-bold text-white">Businesses & Multi-Tenant Workspaces</h3>', '<h3 class="text-xs font-bold text-white">{{ _(\'admin.businesses_workspaces\') }}</h3>'),
        ('<span class="text-[10px] text-slate-400">All registered commercial workspaces under tenant isolation</span>', '<span class="text-[10px] text-slate-400">{{ _(\'admin.businesses_workspaces_desc\') }}</span>'),
        ('<h3 class="text-xs font-bold text-white">Platform Users Directory</h3>', '<h3 class="text-xs font-bold text-white">{{ _(\'admin.platform_user_directory\') }}</h3>'),
        ('<h3 class="text-xs font-bold text-white">Roles & Permissions RBAC Matrix</h3>', '<h3 class="text-xs font-bold text-white">{{ _(\'admin.rbac_matrix_title\') }}</h3>'),
        ('<span>Database Engine & Security Parameters</span>', '<span>{{ _(\'admin.system_health_title\') }}</span>'),
        ('<span>Tamper-Evident Security Log Stream</span>', '<span>{{ _(\'admin.security_logs_title\') }}</span>'),
        ('<span>Verify Hash Chain</span>', '<span>{{ _(\'admin.btn_verify_chain\') }}</span>'),
    ]

    count = 0
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            count += 1

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"admin.html updated! Replaced {count}/{len(replacements)} strings.")

localize_admin()
