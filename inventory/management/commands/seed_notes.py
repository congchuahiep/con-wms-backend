"""Seed dữ liệu phiếu demo — 50 phiếu theo cấu hình user chốt.

Cấu hình (2026-09-19):
  - 40 phiếu NHẬP (loại mua): 70% (28) vào kho công trường (NCC giao thẳng),
    30% (12) vào 2 kho trung tâm (KHO_CHINH / KHO_PHU).
  - 6 phiếu XUẤT: 4 xuất dùng cho công trường + 2 điều chuyển kho.
  - 4 phiếu ĐIỀU CHỈNH (kiểm kê): chênh lệch có lý do, không âm tồn.

Tất cả 50 phiếu đều ĐÃ CHỐT (posted) — sổ kho đầy đủ, tồn chính xác.
Số liệu ngẫu nhiên nhưng DETERMINISTIC (rng seed cố định) — chạy lại cùng kết quả.

Ràng buộc được tôn trọng:
  - Nhập mua phải có NCC; xuất không vượt quá tồn kho hiện có.
  - Điều chỉnh kiểm kê: chênh lệch ≠ 0, có lý do, không làm tồn âm.
  - Kho công trường chỉ xuất dùng cho chính công trường của nó (D6).
  - Demo KHÔNG phụ thuộc kho/site ngoài seed (chỉ dùng KHO_CHINH, KHO_PHU,
    và kho của 5 công trường trong seed).

Chạy:
  python manage.py seed_notes            # thêm phiếu mới (bỏ qua số phiếu đã tồn tại)
  python manage.py seed_notes --reset    # xóa phiếu + sổ kho cũ trước khi seed
"""

import random
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from catalog.models import Material
from iam.models import User
from inventory.models import (
    InboundNote,
    InboundNoteLine,
    OutboundNote,
    OutboundNoteLine,
    StockMovement,
    StocktakeLine,
    StocktakeNote,
)
from inventory.services import (
    generate_inbound_note_number,
    generate_outbound_note_number,
    generate_stocktake_note_number,
)
from sites.models import Site
from supplier.models import Supplier
from warehouse.models import Warehouse

# (code, đơn giá nhập, số lượng min, max, số chữ số thập phân)
MATERIAL_DEFS = [
    ("XM-HT-PCB40", "88000", 20, 200, 0),        # bao
    ("XM-BS-PCB30", "72000", 10, 150, 0),        # bao
    ("THEP-D8", "15500", 100, 1500, 0),          # kg
    ("THEP-D10", "15200", 100, 2000, 0),         # kg
    ("THEP-D12", "15000", 100, 2000, 0),         # kg
    ("THEP-D16", "14800", 50, 1000, 0),          # kg
    ("THEP-H-U100", "1150000", 2, 40, 0),        # cây
    ("CAT-VANG", "350000", 1, 30, 1),            # m3
    ("CAT-DEN", "280000", 1, 25, 1),             # m3
    ("DA-1X2", "480000", 1, 25, 1),              # m3
    ("DA-4X6", "420000", 1, 20, 1),              # m3
    ("GACH-ONG", "1800", 200, 6000, 0),          # viên
    ("GACH-DAC", "2200", 100, 4000, 0),          # viên
]
PRICE = {code: Decimal(price) for code, price, *_ in MATERIAL_DEFS}

INBOUND_CENTRAL_TEXTS = [
    "Nhập vật tư kho trung tâm phục vụ dự trữ",
    "Nhập xi măng + thép dự trữ kho chính",
    "Nhập gạch, cát, đá bổ sung tồn kho",
    "Nhập vật liệu theo kế hoạch tuần",
]
INBOUND_SITE_TEXTS = [
    "Nhập vật tư đổ bê tông móng — NCC giao thẳng",
    "Nhập xi măng + thép khung kết cấu — giao thẳng công trường",
    "Nhập gạch, cát, đá phục vụ xây tường — giao thẳng",
    "Nhập vật liệu theo kế hoạch tuần — giao thẳng",
    "Nhập bổ sung do thiếu hàng thi công — giao thẳng",
]
OUTBOUND_NOTE_TEXTS = [
    "Cấp vật tư cho tổ thi công",
    "Xuất phục vụ đổ bê tông sàn tầng",
    "Cấp xi măng, gạch cho xây tường",
    "Xuất theo phiếu yêu cầu vật tư",
]
TRANSFER_NOTE_TEXTS = [
    "Điều chuyển vật liệu dư thừa sang kho khác",
    "Điều chuyển phục vụ cân đối hàng tồn",
]
STOCKTAKE_NOTE_TEXTS = [
    "Kiểm kê định kỳ cuối tháng",
    "Kiểm kê sau đợt thi công lớn",
    "Kiểm kê đột xuất theo yêu cầu",
]
STOCKTAKE_REASONS = [
    "Bao rách/đổ vỡ khi vận chuyển",
    "Thừa sau khi đếm lại",
    "Hao hụt trong quá trình bốc xếp",
    "Hàng sai quy cách, phát hiện khi kiểm kê",
    "Nhập liệu sai số lượng ở phiếu trước",
    "Mất mát chưa rõ nguyên nhân",
]
LINE_NOTES = ["", "", "", "", "Bao 50kg", "Kèm hóa đơn điện tử", "Giao kèm C/O", "Chất xếp cao 3 tầng"]


class Command(BaseCommand):
    help = "Seed 50 phiếu demo (40 nhập, 6 xuất, 4 điều chỉnh) — 70% nhập vào kho công trường."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Xóa toàn bộ phiếu + sổ kho hiện có trước khi seed.",
        )

    def handle(self, *args, **options):
        self._rng = random.Random(20260919)  # deterministic

        user = User.objects.filter(role="admin").first()
        # Demo chỉ dùng 2 kho trung tâm (không phụ thuộc kho UI tạo thêm)
        central = list(
            Warehouse.objects.filter(
                code__in=["KHO_CHINH", "KHO_PHU"], is_active=True
            ).order_by("id")
        )
        sites = list(Site.objects.filter(status=Site.Status.ACTIVE).order_by("id"))
        site_warehouses = [
            s.warehouse for s in sites if getattr(s, "warehouse", None) is not None
        ]
        suppliers = list(Supplier.objects.all().order_by("id"))
        materials = {
            code: Material.objects.get(code=code) for code, *_ in MATERIAL_DEFS
        }

        missing = []
        if not user:
            missing.append("User admin (chạy seed_users)")
        if len(central) < 2:
            missing.append("Thiếu 2 kho trung tâm (chạy seed_warehouses)")
        if len(sites) < 5:
            missing.append("Thiếu công trường (chạy seed_sites — cần đủ 5)")
        if len(site_warehouses) < 5:
            missing.append("Thiếu kho công trường (chạy seed_sites)")
        if len(suppliers) < 1:
            missing.append("Supplier (chạy seed_suppliers)")
        if len(materials) < len(MATERIAL_DEFS):
            missing.append("Vật tư thiếu (chạy seed_catalog)")
        if missing:
            self.stdout.write(self.style.ERROR("Thiếu dữ liệu nền:"))
            for item in missing:
                self.stdout.write(f"  - {item}")
            return

        if options["reset"]:
            # Xóa dòng reversal (con) trước, rồi dòng gốc — tránh ProtectedError
            # do tự tham chiếu `reversal_of` (PROTECT).
            StockMovement.objects.filter(reversal_of__isnull=False).delete()
            StockMovement.objects.filter(reversal_of__isnull=True).delete()
            InboundNote.objects.all().delete()
            OutboundNote.objects.all().delete()
            StocktakeNote.objects.all().delete()
            self.stdout.write(self.style.WARNING("🗑 Đã xóa toàn bộ phiếu + sổ kho cũ."))

        self.user = user
        self.warehouses = central + site_warehouses
        self.central_warehouses = central
        self.site_warehouses = site_warehouses
        self.sites = sites
        self.suppliers = suppliers
        self.materials = materials

        # Tồn kho chạy trong bộ nhớ — đồng bộ với DB qua từng lần post().
        self.stock = defaultdict(lambda: defaultdict(Decimal))
        self.counters = defaultdict(int)

        # 40 phiếu nhập: 70% (28) vào kho công trường, 30% (12) vào kho trung tâm
        site_flags = [True] * 28 + [False] * 12
        self._rng.shuffle(site_flags)
        self._seed_inbound_posted(site_flags, days=28)

        # 6 phiếu xuất: 4 xuất dùng cho công trường + 2 điều chuyển
        self._seed_outbound_posted(4, kind=OutboundNote.Type.ISSUE_FOR_USE, days=18)
        self._seed_outbound_posted(2, kind=OutboundNote.Type.TRANSFER, days=12)

        # 4 phiếu điều chỉnh (kiểm kê)
        self._seed_stocktake_posted(4, days=12)

        self._report()

    # ── Helpers ──────────────────────────────────────────────────────

    def _rand_qty(self, lo, hi, dec):
        if dec:
            return Decimal(str(round(self._rng.uniform(lo, hi), dec)))
        return Decimal(str(self._rng.randint(lo, hi)))

    def _rand_note(self, texts):
        return texts[self._rng.randrange(len(texts))]

    def _rand_line_notes(self, n):
        return [self._rng.choice(LINE_NOTES) for _ in range(n)]

    def _stock_of(self, warehouse_id, material_id):
        return self.stock[warehouse_id][material_id]

    def _available_materials(self, warehouse_id):
        return [
            mat for mat in self.materials.values() if self._stock_of(warehouse_id, mat.id) > 0
        ]

    def _add_stock(self, warehouse_id, material_id, qty):
        self.stock[warehouse_id][material_id] += qty

    def _inbound_lines(self, n):
        """n dòng nhập: (material, qty, unit_price, note)."""
        picked = self._rng.sample(list(MATERIAL_DEFS), n)
        line_notes = self._rand_line_notes(n)
        return [
            (
                self.materials[code],
                self._rand_qty(lo, hi, dec),
                PRICE[code],
                line_notes[idx],
            )
            for idx, (code, _, lo, hi, dec) in enumerate(picked)
        ]

    def _outbound_lines(self, warehouse_id, n):
        """n dòng xuất: (material, qty) — chỉ lấy mặt hàng đang có tồn, qty ≤ tồn."""
        avail = self._available_materials(warehouse_id)
        if not avail:
            return []
        picked = self._rng.sample(avail, min(n, len(avail)))
        lines = []
        for mat in picked:
            s = self._stock_of(warehouse_id, mat.id)
            frac = Decimal(str(round(self._rng.uniform(0.2, 0.9), 2)))
            qty = (s * frac).quantize(Decimal("0.001"))
            qty = min(qty, s)
            if qty <= 0:
                qty = s
            lines.append((mat, qty))
        return lines

    def _stocktake_lines(self, warehouse_id, n):
        """n dòng điều chỉnh: (material, difference, reason) — diff ≠ 0, không âm tồn."""
        from_mats = self._available_materials(warehouse_id)
        if not from_mats:
            return []
        picked = self._rng.sample(from_mats, min(n, len(from_mats)))
        lines = []
        for mat in picked:
            s = self._stock_of(warehouse_id, mat.id)
            max_diff = (s * Decimal("0.4")).quantize(Decimal("0.1"))
            if self._rng.random() < 0.5 and max_diff >= Decimal("0.1"):
                diff = -max_diff  # hao hụt → giảm tồn
            else:
                diff = (s * Decimal("0.2") + Decimal(1)).quantize(Decimal("0.1"))
            if diff == 0:
                diff = Decimal("0.1")
            diff = max(diff, -s)
            lines.append((mat, diff, self._rng.choice(STOCKTAKE_REASONS)))
        return lines

    def _base(self, model, number_fn, d, **fields):
        """Tạo phiếu (chưa có dòng) với số phiếu tự sinh; bỏ qua nếu trùng số."""
        number = number_fn(d)
        if model.objects.filter(number=number).exists():
            self.stdout.write(self.style.WARNING(f"⏭ Số phiếu đã tồn tại, bỏ qua: {number}"))
            return None
        return model.objects.create(number=number, date=d, **fields)

    # ── Inbound (40 phiếu) ───────────────────────────────────────────

    def _seed_inbound_posted(self, site_flags, days):
        """site_flags[i]=True → phiếu thứ i nhập vào kho công trường (giao thẳng)."""
        for is_site in site_flags:
            d = date(2026, 8, 3) + timedelta(days=self._rng.randrange(days))
            if is_site:
                warehouse = self._rng.choice(self.site_warehouses)
                note_text = self._rand_note(INBOUND_SITE_TEXTS)
                note_text += f" — giao thẳng tới {warehouse.site.name}"
            else:
                warehouse = self._rng.choice(self.central_warehouses)
                note_text = self._rand_note(INBOUND_CENTRAL_TEXTS)
            lines = self._inbound_lines(self._rng.randint(1, 10))
            note = self._base(
                InboundNote,
                generate_inbound_note_number,
                d,
                note_type=InboundNote.Type.PURCHASE,
                warehouse=warehouse,
                supplier=self._rng.choice(self.suppliers),
                note=note_text,
                created_by=self.user,
            )
            if note is None:
                continue
            for idx, (mat, qty, price, line_note) in enumerate(lines, start=1):
                InboundNoteLine.objects.create(
                    inbound_note=note,
                    material=mat,
                    quantity=qty,
                    unit_price=price,
                    line_no=idx,
                    note=line_note,
                )
            self._post(note, [(mat, qty) for mat, qty, _, _ in lines])

    # ── Outbound (6 phiếu) ───────────────────────────────────────────

    def _seed_outbound_posted(self, count, kind, days):
        for _ in range(count):
            d = date(2026, 8, 8) + timedelta(days=self._rng.randrange(days))
            is_issue = kind == OutboundNote.Type.ISSUE_FOR_USE

            if is_issue:
                # Ưu tiên xuất dùng tại kho công trường (D6: site = chính CT của kho)
                site_whs = [
                    w for w in self.site_warehouses if self._available_materials(w.id)
                ]
                central_whs = [
                    w for w in self.central_warehouses if self._available_materials(w.id)
                ]
                if not site_whs and not central_whs:
                    self.stdout.write(self.style.WARNING("  (bỏ qua: chưa có tồn để xuất)"))
                    continue
                if site_whs and self._rng.random() < 0.7:
                    warehouse = self._rng.choice(site_whs)
                else:
                    warehouse = self._rng.choice(central_whs or site_whs)
                site = (
                    warehouse.site
                    if warehouse.site_id is not None
                    else self._rng.choice(self.sites)
                )
                to_warehouse = None
            else:
                # Điều chuyển: kho trung tâm → kho công trường là chính
                src_pool = [
                    w for w in self.central_warehouses if self._available_materials(w.id)
                ] or self.warehouses
                warehouse = self._rng.choice(src_pool)
                dst_pool = [w for w in self.warehouses if w.id != warehouse.id]
                site_whs = [w for w in self.site_warehouses if w.id != warehouse.id]
                to_warehouse = (
                    self._rng.choice(site_whs)
                    if site_whs and self._rng.random() < 0.7
                    else self._rng.choice(dst_pool)
                )
                site = None

            lines = self._outbound_lines(warehouse.id, self._rng.randint(1, 10))
            if not lines:
                continue
            note = self._base(
                OutboundNote,
                generate_outbound_note_number,
                d,
                note_type=kind,
                warehouse=warehouse,
                site=site,
                to_warehouse=to_warehouse,
                note=self._rand_note(OUTBOUND_NOTE_TEXTS if is_issue else TRANSFER_NOTE_TEXTS),
                created_by=self.user,
            )
            if note is None:
                continue
            for idx, (mat, qty) in enumerate(lines, start=1):
                OutboundNoteLine.objects.create(
                    outbound_note=note, material=mat, quantity=qty, line_no=idx,
                )
            self._post(note, [(mat, qty, warehouse, note.to_warehouse) for mat, qty in lines])

    # ── Điều chỉnh kiểm kê (4 phiếu) ─────────────────────────────────

    def _seed_stocktake_posted(self, count, days):
        for _ in range(count):
            d = date(2026, 8, 15) + timedelta(days=self._rng.randrange(days))
            whs_with_stock = [
                w for w in self.warehouses if self._available_materials(w.id)
            ]
            if not whs_with_stock:
                continue
            warehouse = self._rng.choice(whs_with_stock)
            lines = self._stocktake_lines(warehouse.id, self._rng.randint(1, 10))
            if not lines:
                continue
            note = self._base(
                StocktakeNote,
                generate_stocktake_note_number,
                d,
                warehouse=warehouse,
                note=self._rand_note(STOCKTAKE_NOTE_TEXTS),
                created_by=self.user,
            )
            if note is None:
                continue
            for idx, (mat, diff, reason) in enumerate(lines, start=1):
                StocktakeLine.objects.create(
                    stocktake_note=note, material=mat, difference=diff,
                    reason=reason, line_no=idx,
                )
            self._post(note, [(mat, diff) for mat, diff, _ in lines])

    # ── Chốt + cập nhật tồn chạy ─────────────────────────────────────

    def _post(self, note, stock_effects):
        """Chốt phiếu: gọi note.post(user) và cập nhật tồn chạy tương ứng.

        stock_effects — mỗi phần tử là:
          - inbound/stocktake: (material, qty)               → tồn kho mặc định của phiếu ± qty
          - outbound         : (material, qty, from_wh, to_wh) → trừ kho nguồn, cộng kho đích (nếu điều chuyển)
        """
        try:
            note.post(self.user)
        except Exception as exc:  # noqa: BLE001 — seed tooling: log & bỏ qua
            self.stdout.write(
                self.style.ERROR(f"❌ Chốt {note.number} lỗi: {exc} — sẽ xóa phiếu.")
            )
            note.delete()
            return
        for effect in stock_effects:
            if len(effect) == 4:
                mat, qty, from_wh, to_wh = effect
                self._add_stock(from_wh.id, mat.id, -qty)
                if to_wh:
                    self._add_stock(to_wh.id, mat.id, qty)
            else:
                mat, qty = effect
                self._add_stock(note.warehouse_id, mat.id, qty)
        self.counters[f"{note._meta.model_name}_posted"] += 1

    def _report(self):
        total = InboundNote.objects.count() + OutboundNote.objects.count() + StocktakeNote.objects.count()
        by_type = {
            "Nhập vào kho công trường": InboundNote.objects.filter(
                warehouse__site__isnull=False
            ).count(),
            "Nhập vào kho trung tâm": InboundNote.objects.filter(
                warehouse__site__isnull=True
            ).count(),
            "Xuất kho": OutboundNote.objects.count(),
            "Điều chỉnh (kiểm kê)": StocktakeNote.objects.count(),
        }
        self.stdout.write(self.style.SUCCESS("🎉 Seed notes hoàn tất! Tổng số phiếu:"))
        for label, n in by_type.items():
            self.stdout.write(f"  {label}: {n}")
        self.stdout.write(f"  TỔNG: {total} phiếu — Dòng sổ kho: {StockMovement.objects.count()}")