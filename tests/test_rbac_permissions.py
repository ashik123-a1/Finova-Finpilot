"""
Unit and Integration Tests for 7 User Roles, 22 Permissions, and Server-Side RBAC Enforcement.
Covers Master SRS Part 3 (Roles, Registration, RBAC Matrix, Tenant Boundaries).
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from src.database.connection import SessionLocal
from src.core.security import (
    has_permission,
    enforce_shop_isolation,
    CANONICAL_ROLE_PERMISSIONS,
)
from src.core.exceptions import ShopAccessDeniedError


def test_database_roles_and_permissions_seeded():
    """Verify that all 7 canonical roles and 22 permissions are seeded in database."""
    with SessionLocal() as db:
        roles = db.execute(text("SELECT code FROM roles ORDER BY code;")).scalars().all()
        assert set(roles) == {
            "super_admin",
            "owner",
            "manager",
            "accountant",
            "sales",
            "inventory",
            "auditor",
        }

        perms = db.execute(text("SELECT code FROM permissions;")).scalars().all()
        assert len(perms) == 22
        assert "business.view" in perms
        assert "finance.create" in perms
        assert "admin.access" in perms
        assert "document.post" in perms


def test_rbac_least_privilege_boundaries():
    """Verify that permissions strictly adhere to the principle of least privilege."""
    # 1. Platform Super Admin has admin.access, but Business Owner does not
    assert has_permission("super_admin", "admin.access") is True
    assert has_permission("owner", "admin.access") is False

    # 2. Business Owner has business and financial control
    assert has_permission("owner", "finance.delete") is True
    assert has_permission("owner", "team.roles") is True

    # 3. Accountant can view & post finance, but cannot delete or invite team
    assert has_permission("accountant", "finance.view") is True
    assert has_permission("accountant", "document.post") is True
    assert has_permission("accountant", "finance.delete") is False
    assert has_permission("accountant", "team.roles") is False

    # 4. Sales / CRM staff can manage CRM & create sales, but cannot view P&L or delete
    assert has_permission("sales", "crm.manage") is True
    assert has_permission("sales", "finance.create") is True
    assert has_permission("sales", "finance.view") is False
    assert has_permission("sales", "finance.delete") is False

    # 5. Inventory staff can manage inventory, but cannot access CRM or finance
    assert has_permission("inventory", "inventory.manage") is True
    assert has_permission("inventory", "crm.manage") is False
    assert has_permission("inventory", "finance.view") is False

    # 6. Auditor has read-only audit & finance access, but zero write/post permissions
    assert has_permission("auditor", "finance.view") is True
    assert has_permission("auditor", "audit.view") is True
    assert has_permission("auditor", "finance.create") is False
    assert has_permission("auditor", "document.post") is False
    assert has_permission("auditor", "finance.delete") is False


def test_enforce_shop_isolation_with_rbac_permission():
    """Verify enforce_shop_isolation validates role-based permissions at shop level."""
    # User 10 has sales role in shop 5
    memberships = [
        {"user_id": 10, "business_id": 1, "shop_id": 5, "role_code": "sales", "is_active": True}
    ]

    # Sales role CAN create finance (sales entry)
    assert enforce_shop_isolation(10, 5, memberships, required_permission="finance.create") is True

    # Sales role CANNOT delete finance -> Must raise ShopAccessDeniedError
    with pytest.raises(ShopAccessDeniedError) as exc_info:
        enforce_shop_isolation(10, 5, memberships, required_permission="finance.delete")
    assert "Permission Denied" in str(exc_info.value)
    assert "finance.delete" in str(exc_info.value)

    # Cross-shop access is denied regardless of role
    with pytest.raises(ShopAccessDeniedError) as exc_info:
        enforce_shop_isolation(10, 99, memberships, required_permission="finance.create")
    assert "not authorized to access shop 99" in str(exc_info.value)
