"""Tiện ích domain Site — tự động tạo kho công trường 1-1 khi tạo công trường."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from catalog.models import Material
from inventory.models import OutboundNote, OutboundNoteLine, StockMovement
from inventory.services import generate_outbound_note_number
from warehouse.models import Warehouse
from warehouse.services import warehouse_code_for_site


def ensure_site_warehouse(site) -> Warehouse:
    """Tạo (hoặc gắn) kho công trường cho site. Idempotent — chạy lại không tạo mới.

    Tên kho = tên công trường (code `KHO_<site.code>` đã đủ nhận diện, khỏi cần tiền tố).
    """
    warehouse, _ = Warehouse.objects.update_or_create(
        code=warehouse_code_for_site(site),
        defaults={
            "name": site.name,
            "site": site,
        },
    )
    return warehouse


def site_stock_balances(site) -> dict[int, Decimal]:
    """Tồn kho công trường theo vật tư — SUM dòng sổ kho của kho công trường.

    Trả về dict {material_id: Decimal}. Nguồn sự thật là sổ kho (stock D1) —
    không có bảng tồn, không có khái niệm "đã sử dụng" làm trừ tồn.
    """
    warehouse = getattr(site, "warehouse", None)
    if warehouse is None:
        return {}
    rows = (
        StockMovement.objects.filter(warehouse=warehouse)
        .values("material")
        .annotate(balance=models.Sum("quantity"))
    )
    return {row["material"]: row["balance"] or Decimal(0) for row in rows}


def _requirement_row(material, balance, required, note):
    """Một dòng trong bảng so sánh — required=None nghĩa là vật tư ngoài định mức."""
    if required is None:
        status = "not_in_plan"
        default_return = balance
    else:
        status = "sufficient" if balance >= required else "insufficient"
        default_return = max(balance - required, Decimal(0))
    return {
        "material": material,
        "required_quantity": required,
        "balance": balance,
        "status": status,
        "default_return_quantity": default_return,
        "note": note,
    }


def build_requirement_rows(site):
    """Bảng so sánh định mức vs tồn kho — hợp (a) mọi dòng định mức + (b) vật tư tồn > 0.

    Sắp xếp: dòng định mức trước, theo mã vật tư; sau đó vật tư ngoài định mức.
    """
    balances = site_stock_balances(site)
    rows = []
    req_material_ids = set()
    for req in site.material_requirements.select_related("material__unit").order_by(
        "material__code"
    ):
        req_material_ids.add(req.material_id)
        balance = balances.get(req.material_id, Decimal(0))
        rows.append(_requirement_row(req.material, balance, req.quantity, req.note))

    extra_ids = [
        mid
        for mid, balance in balances.items()
        if mid not in req_material_ids and balance > 0
    ]
    if extra_ids:
        extras = Material.objects.filter(id__in=extra_ids).select_related("unit")
        for material in extras.order_by("code"):
            rows.append(_requirement_row(material, balances[material.id], None, None))
    return rows


def _default_return(balance, required):
    """Mặc định số lượng trả về khi tất toán: phần vượt định mức / toàn bộ nếu ngoài định mức."""
    if required is None:
        return balance
    return max(balance - required, Decimal(0))


@transaction.atomic
def settle_site(site, to_warehouse, lines, user) -> OutboundNote:
    """Tất toán công trường — một phiếu điều chuyển số vật tư trả về + đóng site + kho.

    - `lines`: list dict `{"material": Material, "quantity": Decimal, "note": str}`
      (cấu trúc đã validate ở serializer; nghiệp vụ validate tại đây).
    - Điều kiện: site đang hoạt động, đủ MỌI định mức, kho đích mở và khác kho công trường,
      mỗi dòng `0 < quantity <= tồn`; trả ít hơn mặc định thì bắt buộc ghi lý do (note).
    - Raise `django.core.exceptions.ValidationError` khi vi phạm.
    """
    from .models import Site

    if site.status != Site.Status.ACTIVE:
        raise ValidationError({"status": "Công trường đã đóng — không tất toán được."})
    warehouse = getattr(site, "warehouse", None)
    if warehouse is None:
        raise ValidationError({"warehouse": "Công trường chưa có kho công trường."})
    if to_warehouse is None or not to_warehouse.is_active:
        raise ValidationError(
            {"to_warehouse": "Kho đích phải là kho đang hoạt động."}
        )
    if to_warehouse == warehouse:
        raise ValidationError(
            {"to_warehouse": "Kho đích phải khác kho công trường này."}
        )

    balances = site_stock_balances(site)
    requirements = {
        req.material_id: req
        for req in site.material_requirements.select_related("material")
    }

    # 1. Bắt buộc đủ mọi định mức (kiểm tra tại thời điểm thực thi)
    missing_ids = [
        mid
        for mid, req in requirements.items()
        if balances.get(mid, Decimal(0)) < req.quantity
    ]
    if missing_ids:
        codes = list(
            Material.objects.filter(id__in=missing_ids).values_list("code", flat=True)
        )
        raise ValidationError(
            {
                "lines": (
                    "Chưa đủ định mức các vật tư: "
                    + ", ".join(codes)
                    + " — không tất toán được."
                )
            }
        )

    # 2. Validate dòng trả về
    seen = set()
    validated = []
    for item in lines:
        material = item["material"]
        if material.id in seen:
            raise ValidationError(
                {"lines": f"Trùng vật tư {material.code} trong danh sách trả về."}
            )
        seen.add(material.id)
        balance = balances.get(material.id, Decimal(0))
        quantity = item["quantity"]
        if balance <= 0:
            raise ValidationError(
                {"lines": f"Vật tư {material.code} không có tồn trong kho công trường."}
            )
        if quantity <= 0 or quantity > balance:
            raise ValidationError(
                {
                    "lines": (
                        f"Số lượng trả về của {material.code} phải trong khoảng (0, {balance}]."
                    )
                }
            )
        req = requirements.get(material.id)
        default_return = _default_return(balance, req.quantity if req else None)
        note = item.get("note", "")
        if quantity < default_return and not note.strip():
            raise ValidationError(
                {
                    "lines": (
                        f"Vật tư {material.code}: trả ít hơn mặc định ({default_return}) "
                        "phải ghi lý do."
                    )
                }
            )
        validated.append({"material": material, "quantity": quantity, "note": note})

    # 3. Phiếu điều chuyển — tạo + chốt ngay (ghi sổ kho ± ở 2 đầu)
    date = timezone.localdate()
    note = OutboundNote.objects.create(
        number=generate_outbound_note_number(date),
        note_type=OutboundNote.Type.TRANSFER,
        date=date,
        warehouse=warehouse,
        to_warehouse=to_warehouse,
        note=f"Tất toán công trường {site.code} — {site.name}",
        created_by=user,
    )
    for idx, item in enumerate(validated, start=1):
        OutboundNoteLine.objects.create(
            outbound_note=note,
            material=item["material"],
            quantity=item["quantity"],
            line_no=idx,
            note=item["note"],
        )
    note.post(user)

    # 4. Đóng công trường + kho công trường
    site.status = Site.Status.COMPLETED
    site.settled_at = timezone.now()
    site.settled_by = user
    site.save(update_fields=["status", "settled_at", "settled_by", "updated_at"])
    warehouse.is_active = False
    warehouse.save(update_fields=["is_active", "updated_at"])
    return note