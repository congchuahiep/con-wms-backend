from django.core.management.base import BaseCommand

from catalog.models import Material, MaterialCategory, Unit, UnitConversion


class Command(BaseCommand):
    help = "Seed dữ liệu mẫu cho Catalog (danh mục, đơn vị, vật tư, quy đổi)."

    def handle(self, *args, **options):
        self._seed_categories()
        self._seed_units()
        self._seed_materials()
        self._seed_conversions()
        self.stdout.write(self.style.SUCCESS("Seed catalog OK"))

    def _seed_categories(self):
        if MaterialCategory.objects.exists():
            return

        # L1
        root = MaterialCategory.objects.create(code="VLXD", name="Vật liệu xây dựng")

        # L2
        xm = MaterialCategory.objects.create(code="XM", name="Xi măng", parent=root)
        cat = MaterialCategory.objects.create(code="CAT", name="Cát", parent=root)
        da = MaterialCategory.objects.create(code="DA", name="Đá", parent=root)
        gach = MaterialCategory.objects.create(code="GACH", name="Gạch", parent=root)
        thep = MaterialCategory.objects.create(code="THEP", name="Thép", parent=root)

        # L3
        MaterialCategory.objects.create(code="GACH_ONG", name="Gạch ống", parent=gach)
        MaterialCategory.objects.create(code="GACH_DAC", name="Gạch đặc", parent=gach)

        thep_tron = MaterialCategory.objects.create(code="THEP_TRON", name="Thép tròn", parent=thep)
        MaterialCategory.objects.create(code="THEP_HINH", name="Thép hình", parent=thep)

        # L4 — dưới THEP_TRON
        MaterialCategory.objects.create(code="THEP_TRON_NHO", name="Thép tròn D≤10", parent=thep_tron)
        MaterialCategory.objects.create(code="THEP_TRON_LON", name="Thép tròn D>10", parent=thep_tron)

        self.stdout.write("  Categories: 12 created (1 L1 + 5 L2 + 4 L3 + 2 L4)")

    def _seed_units(self):
        if Unit.objects.exists():
            return

        units = [
            ("BAO", "Bao"),
            ("KG", "Kilogram"),
            ("TAN", "Tấn"),
            ("M3", "Mét khối"),
            ("M", "Mét"),
            ("L", "Lít"),
            ("CAY", "Cây"),
            ("VIEN", "Viên"),
        ]
        for code, name in units:
            Unit.objects.create(code=code, name=name)
        self.stdout.write(f"  Units: {len(units)} created")

    def _seed_materials(self):
        if Material.objects.exists():
            return

        cat_xm = MaterialCategory.objects.get(code="XM")
        cat_cat = MaterialCategory.objects.get(code="CAT")
        cat_da = MaterialCategory.objects.get(code="DA")
        cat_gach_ong = MaterialCategory.objects.get(code="GACH_ONG")
        cat_gach_dac = MaterialCategory.objects.get(code="GACH_DAC")
        cat_thep_tron_nho = MaterialCategory.objects.get(code="THEP_TRON_NHO")
        cat_thep_tron_lon = MaterialCategory.objects.get(code="THEP_TRON_LON")
        cat_thep_hinh = MaterialCategory.objects.get(code="THEP_HINH")

        u_bao = Unit.objects.get(code="BAO")
        u_kg = Unit.objects.get(code="KG")
        u_m3 = Unit.objects.get(code="M3")
        u_cay = Unit.objects.get(code="CAY")
        u_vien = Unit.objects.get(code="VIEN")

        materials = [
            # Xi măng
            ("XM-HT-PCB40", "Xi măng Hà Tiên PCB40", cat_xm, u_bao, "PCB40, 50kg/bao"),
            ("XM-BS-PCB30", "Xi măng Bỉm Sơn PCB30", cat_xm, u_bao, "PCB30, 40kg/bao"),
            # Thép tròn D≤10 (L4)
            ("THEP-D8", "Thép D8", cat_thep_tron_nho, u_kg, "Thép tròn D8, 0.395kg/m"),
            ("THEP-D10", "Thép D10", cat_thep_tron_nho, u_kg, "Thép tròn D10, 0.617kg/m"),
            # Thép tròn D>10 (L4)
            ("THEP-D12", "Thép D12", cat_thep_tron_lon, u_kg, "Thép tròn D12, 0.888kg/m"),
            ("THEP-D16", "Thép D16", cat_thep_tron_lon, u_kg, "Thép tròn D16, 1.58kg/m"),
            # Thép hình (L3)
            ("THEP-H-U100", "Thép hình chữ U 100", cat_thep_hinh, u_cay, "Thép U100, 6m/cây"),
            # Cát
            ("CAT-VANG", "Cát vàng", cat_cat, u_m3, "Cát vàng hạt to"),
            ("CAT-DEN", "Cát đen", cat_cat, u_m3, "Cát đen hạt nhỏ"),
            # Đá
            ("DA-1X2", "Đá 1x2", cat_da, u_m3, "Đá dăm 1x2cm"),
            ("DA-4X6", "Đá 4x6", cat_da, u_m3, "Đá dăm 4x6cm"),
            # Gạch
            ("GACH-ONG", "Gạch ống 4 lỗ", cat_gach_ong, u_vien, "Gạch ống 4 lỗ, 80x80x180mm"),
            ("GACH-DAC", "Gạch đặc", cat_gach_dac, u_vien, "Gạch thẻ đặc, 40x80x180mm"),
        ]
        for code, name, cat, unit, desc in materials:
            Material.objects.create(
                code=code, name=name, category=cat, unit=unit, description=desc
            )
        self.stdout.write(f"  Materials: {len(materials)} created")

    def _seed_conversions(self):
        if UnitConversion.objects.exists():
            return

        u_tan = Unit.objects.get(code="TAN")
        u_kg = Unit.objects.get(code="KG")
        u_m3 = Unit.objects.get(code="M3")
        u_bao = Unit.objects.get(code="BAO")
        u_cay = Unit.objects.get(code="CAY")

        cat_vang = Material.objects.get(code="CAT-VANG")  # ~1600 kg/m3
        xm_ht = Material.objects.get(code="XM-HT-PCB40")  # 50 kg/bao
        xm_bs = Material.objects.get(code="XM-BS-PCB30")  # 40 kg/bao
        thep_d10 = Material.objects.get(code="THEP-D10")  # 7.4 kg/cây

        conversions = [
            (u_tan, u_kg, 1000, None),
            (u_m3, u_kg, 1600, cat_vang),
            (u_bao, u_kg, 50, xm_ht),
            (u_bao, u_kg, 40, xm_bs),
            (u_cay, u_kg, 7.4, thep_d10),
        ]
        for from_u, to_u, factor, mat in conversions:
            UnitConversion.objects.create(
                from_unit=from_u, to_unit=to_u, factor=factor, material=mat
            )
        self.stdout.write(f"  Conversions: {len(conversions)} created")
