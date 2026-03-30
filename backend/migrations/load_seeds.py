"""
種子資料載入腳本

將種子資料寫入資料庫
"""
import sys
from decimal import Decimal
from pathlib import Path

# 將 backend 目錄加入 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal, init_db
from app.models.product import Category, Product, CustomizationOption, CustomizationGroup
from app.models.material import Material, ProductMaterial
from migrations.seeds import CATEGORIES, PRODUCTS, MATERIALS, PRODUCT_MATERIALS, COMMON_CUSTOMIZATION_GROUPS


def seed_categories(db):
    """載入分類資料"""
    print("載入分類資料...")
    count = 0

    for cat_data in CATEGORIES:
        existing = db.query(Category).filter(Category.id == cat_data["id"]).first()
        if not existing:
            category = Category(
                id=cat_data["id"],
                name=cat_data["name"],
                description=cat_data.get("description"),
                sort_order=cat_data.get("display_order", 0),
                is_active=True,
            )
            db.add(category)
            count += 1

    db.commit()
    print(f"  已載入 {count} 個分類")


def seed_products(db):
    """載入商品資料"""
    print("載入商品資料...")
    product_count = 0
    option_count = 0

    for prod_data in PRODUCTS:
        existing = db.query(Product).filter(Product.id == prod_data["id"]).first()
        if not existing:
            product = Product(
                id=prod_data["id"],
                category_id=prod_data.get("category_id"),
                name=prod_data["name"],
                description=prod_data.get("description"),
                price=Decimal(str(prod_data["price"])),
                daily_limit=prod_data.get("daily_limit", 0),
                sort_order=prod_data.get("display_order", 0),
                is_active=True,
                is_available=True,
            )
            db.add(product)
            db.flush()  # 取得 product.id
            product_count += 1

            # 載入舊式客製化選項（向後相容）
            for idx, custom in enumerate(prod_data.get("customizations", [])):
                option = CustomizationOption(
                    product_id=prod_data["id"],
                    name=custom["name"],
                    option_type=custom.get("option_type", "modifier"),
                    price_adjustment=Decimal(str(custom.get("price_adjustment", 0))),
                    is_default=custom.get("is_default", False),
                    sort_order=idx,
                    is_active=True,
                )
                db.add(option)
                option_count += 1

    db.commit()
    print(f"  已載入 {product_count} 個商品")
    print(f"  已載入 {option_count} 個客製化選項")


def cleanup_ungrouped_options(db):
    """清除舊的未分組客製化選項（已被群組取代）"""
    print("清除舊的未分組選項...")
    deleted = db.query(CustomizationOption).filter(
        CustomizationOption.group_id.is_(None)
    ).delete(synchronize_session=False)
    db.commit()
    print(f"  已清除 {deleted} 個舊選項")


def seed_customization_groups(db):
    """為每個商品載入共用客製化群組"""
    print("載入客製化群組...")
    group_count = 0
    option_count = 0

    products = db.query(Product).all()

    for product in products:
        for grp_data in COMMON_CUSTOMIZATION_GROUPS:
            group_id = f"{product.id}-{grp_data['id_suffix']}"

            existing = db.query(CustomizationGroup).filter(
                CustomizationGroup.id == group_id
            ).first()

            if not existing:
                group = CustomizationGroup(
                    id=group_id,
                    product_id=product.id,
                    name=grp_data["name"],
                    group_type=grp_data["group_type"],
                    min_select=grp_data["min_select"],
                    max_select=grp_data["max_select"],
                    is_required=grp_data["is_required"],
                    sort_order=grp_data["sort_order"],
                    is_active=True,
                )
                db.add(group)
                db.flush()
                group_count += 1

                # 載入群組內的選項
                for idx, opt_data in enumerate(grp_data["options"]):
                    option = CustomizationOption(
                        product_id=product.id,
                        group_id=group_id,
                        name=opt_data["name"],
                        option_type=opt_data.get("option_type", "modifier"),
                        price_adjustment=Decimal(str(opt_data.get("price_adjustment", 0))),
                        is_default=False,
                        sort_order=idx,
                        is_active=True,
                    )
                    db.add(option)
                    option_count += 1

    db.commit()
    print(f"  已載入 {group_count} 個客製化群組")
    print(f"  已載入 {option_count} 個群組選項")


def seed_materials(db):
    """載入物料資料"""
    print("載入物料資料...")
    count = 0

    for mat_data in MATERIALS:
        existing = db.query(Material).filter(Material.id == mat_data["id"]).first()
        if not existing:
            material = Material(
                id=mat_data["id"],
                name=mat_data["name"],
                unit=mat_data.get("unit", "份"),
                current_stock=Decimal(str(mat_data.get("current_stock", 0))),
                safety_stock=Decimal(str(mat_data.get("safety_stock", 0))),
                unit_cost=Decimal(str(mat_data.get("unit_cost", 0))),
            )
            db.add(material)
            count += 1

    db.commit()
    print(f"  已載入 {count} 個物料")


def seed_product_materials(db):
    """載入 BOM 對應資料"""
    print("載入 BOM 對應資料...")
    count = 0

    for pm_data in PRODUCT_MATERIALS:
        # 檢查是否已存在相同對應
        existing = db.query(ProductMaterial).filter(
            ProductMaterial.product_id == pm_data["product_id"],
            ProductMaterial.material_id == pm_data["material_id"]
        ).first()

        if not existing:
            pm = ProductMaterial(
                product_id=pm_data["product_id"],
                material_id=pm_data["material_id"],
                quantity=Decimal(str(pm_data["quantity"])),
            )
            db.add(pm)
            count += 1

    db.commit()
    print(f"  已載入 {count} 個 BOM 對應")


def run_seeds():
    """執行種子資料載入"""
    print("=" * 50)
    print("開始載入種子資料...")
    print("=" * 50)

    # 初始化資料庫
    init_db()

    # 建立資料庫會話
    db = SessionLocal()

    try:
        seed_categories(db)
        seed_products(db)
        cleanup_ungrouped_options(db)
        seed_customization_groups(db)
        seed_materials(db)
        seed_product_materials(db)

        print("=" * 50)
        print("種子資料載入完成！")
        print("=" * 50)

    except Exception as e:
        print(f"\n錯誤：{e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seeds()
