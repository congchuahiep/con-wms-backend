"""Tiện ích domain Warehouse."""


def warehouse_code_for_site(site) -> str:
    """Mã kho công trường: `KHO_<site.code>`, cắt tối đa 20 ký tự (`Warehouse.code`)."""
    return f"KHO_{site.code}"[:20]