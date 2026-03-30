"""
種子資料

初始化一米粒弁当専門店的商品和設定資料
"""
import uuid
from datetime import datetime

# 分類資料
CATEGORIES = [
    {
        "id": "cat-chicken",
        "name": "雞",
        "description": "雞肉類便當",
        "display_order": 1,
    },
    {
        "id": "cat-pork",
        "name": "豬",
        "description": "豬肉類便當",
        "display_order": 2,
    },
    {
        "id": "cat-beef",
        "name": "牛",
        "description": "牛肉類便當",
        "display_order": 3,
    },
    {
        "id": "cat-special",
        "name": "?",
        "description": "隱藏菜單",
        "display_order": 4,
    },
]

# 全商品共用客製化群組
# 每個商品都會自動套用這些群組
COMMON_CUSTOMIZATION_GROUPS = [
    {
        "id_suffix": "rice",
        "name": "飯量調整",
        "group_type": "single_select",
        "min_select": 0,
        "max_select": 1,
        "is_required": False,
        "sort_order": 1,
        "options": [
            {"name": "1/3飯", "option_type": "modifier", "price_adjustment": 0},
            {"name": "半飯", "option_type": "modifier", "price_adjustment": 0},
            {"name": "加飯", "option_type": "modifier", "price_adjustment": 0},
            {"name": "不飯換菜", "option_type": "modifier", "price_adjustment": 0},
        ],
    },
    {
        "id_suffix": "exclude",
        "name": "不要",
        "group_type": "multi_select",
        "min_select": 0,
        "max_select": 0,  # 0 = 不限
        "is_required": False,
        "sort_order": 2,
        "options": [
            {"name": "蔥", "option_type": "modifier", "price_adjustment": 0},
            {"name": "香菜", "option_type": "modifier", "price_adjustment": 0},
            {"name": "餐具", "option_type": "modifier", "price_adjustment": 0},
        ],
    },
    {
        "id_suffix": "extra",
        "name": "額外需求",
        "group_type": "multi_select",
        "min_select": 0,
        "max_select": 0,
        "is_required": False,
        "sort_order": 3,
        "options": [
            {"name": "加辣", "option_type": "modifier", "price_adjustment": 0},
        ],
    },
]

# 商品資料
PRODUCTS = [
    # 雞肉類
    {
        "id": "prod-chicken-1",
        "category_id": "cat-chicken",
        "name": "戰斧雞腿",
        "description": "人氣 NO.1！霸氣戰斧雞腿，外酥內嫩，份量十足",
        "price": 120,
        "daily_limit": 30,
        "display_order": 1,
        "customizations": [],
    },
    {
        "id": "prod-chicken-2",
        "category_id": "cat-chicken",
        "name": "醬燒揚雞",
        "description": "日式醬燒風味，炸雞淋上特製醬汁",
        "price": 120,
        "daily_limit": 0,
        "display_order": 2,
        "customizations": [],
    },
    # 豬肉類
    {
        "id": "prod-pork-1",
        "category_id": "cat-pork",
        "name": "相撲豬太郎",
        "description": "獨家招牌！大份量豬肉料理，吃飽吃滿",
        "price": 120,
        "daily_limit": 0,
        "display_order": 1,
        "customizations": [],
    },
    {
        "id": "prod-pork-2",
        "category_id": "cat-pork",
        "name": "嫩嫩豬柳",
        "description": "軟嫩豬柳條，口感滑嫩",
        "price": 120,
        "daily_limit": 0,
        "display_order": 2,
        "customizations": [],
    },
    {
        "id": "prod-pork-3",
        "category_id": "cat-pork",
        "name": "燒肉多多",
        "description": "香氣四溢的燒肉，肉量超多",
        "price": 120,
        "daily_limit": 0,
        "display_order": 3,
        "customizations": [],
    },
    {
        "id": "prod-pork-4",
        "category_id": "cat-pork",
        "name": "家鄉豬腳",
        "description": "傳統滷製豬腳，軟Q入味",
        "price": 120,
        "daily_limit": 0,
        "display_order": 4,
        "customizations": [],
    },
    {
        "id": "prod-pork-5",
        "category_id": "cat-pork",
        "name": "五告厚豬排",
        "description": "人氣 NO.2！超厚切豬排，外酥內多汁",
        "price": 130,
        "daily_limit": 20,
        "display_order": 5,
        "customizations": [],
    },
    {
        "id": "prod-pork-6",
        "category_id": "cat-pork",
        "name": "藍帶豬排",
        "description": "豬排內夾起司與火腿，香濃美味",
        "price": 180,
        "daily_limit": 15,
        "display_order": 6,
        "customizations": [],
    },
    # 牛肉類
    {
        "id": "prod-beef-1",
        "category_id": "cat-beef",
        "name": "牛逼菲力",
        "description": "嚴選菲力牛排，軟嫩多汁",
        "price": 150,
        "daily_limit": 10,
        "display_order": 1,
        "customizations": [],
    },
    {
        "id": "prod-beef-2",
        "category_id": "cat-beef",
        "name": "鄉村燉牛肉",
        "description": "慢燉牛肉，濃郁入味",
        "price": 120,
        "daily_limit": 0,
        "display_order": 2,
        "customizations": [],
    },
    # 隱藏菜單
    {
        "id": "prod-special-1",
        "category_id": "cat-special",
        "name": "隱藏菜單",
        "description": "不定時更新，每日限量供應",
        "price": 120,
        "daily_limit": 5,
        "display_order": 1,
        "customizations": [],
    },
]

# 物料資料
MATERIALS = [
    {"id": "mat-1", "name": "雞腿", "unit": "份", "current_stock": 50, "safety_stock": 10},
    {"id": "mat-2", "name": "豬排", "unit": "份", "current_stock": 40, "safety_stock": 10},
    {"id": "mat-3", "name": "菲力牛排", "unit": "份", "current_stock": 15, "safety_stock": 5},
    {"id": "mat-4", "name": "白飯", "unit": "kg", "current_stock": 20, "safety_stock": 5},
    {"id": "mat-5", "name": "高麗菜", "unit": "顆", "current_stock": 20, "safety_stock": 5},
    {"id": "mat-6", "name": "紅蘿蔔", "unit": "條", "current_stock": 30, "safety_stock": 10},
    {"id": "mat-7", "name": "蛋", "unit": "顆", "current_stock": 100, "safety_stock": 20},
    {"id": "mat-8", "name": "起司片", "unit": "片", "current_stock": 30, "safety_stock": 10},
    {"id": "mat-9", "name": "火腿片", "unit": "片", "current_stock": 30, "safety_stock": 10},
    {"id": "mat-10", "name": "豬腳", "unit": "份", "current_stock": 10, "safety_stock": 5},
]

# 店家設定
STORE_SETTINGS = [
    {"key": "store_name", "value": "一米粒 弁当専門店", "description": "店家名稱"},
    {"key": "store_phone", "value": "0909-998-952", "description": "聯絡電話"},
    {"key": "store_address", "value": "台中市中區興中街20號", "description": "店家地址"},
    {"key": "open_time", "value": "10:00", "description": "開始營業時間"},
    {"key": "close_time", "value": "16:30", "description": "結束營業時間"},
    {"key": "closed_days", "value": "saturday,sunday", "description": "公休日"},
    {"key": "delivery_enabled", "value": "true", "description": "是否啟用外送"},
    {"key": "delivery_fee", "value": "30", "description": "外送費用"},
    {"key": "free_delivery_minimum", "value": "300", "description": "滿額免運門檻"},
    {"key": "delivery_radius", "value": "3", "description": "外送範圍(公里)"},
]

# BOM 物料清單對應
# 定義每個商品需要消耗的物料數量
PRODUCT_MATERIALS = [
    # 戰斧雞腿
    {"product_id": "prod-chicken-1", "material_id": "mat-1", "quantity": 1},     # 雞腿 1 份
    {"product_id": "prod-chicken-1", "material_id": "mat-4", "quantity": 0.2},   # 白飯 0.2 kg
    {"product_id": "prod-chicken-1", "material_id": "mat-5", "quantity": 0.1},   # 高麗菜 0.1 顆
    {"product_id": "prod-chicken-1", "material_id": "mat-6", "quantity": 0.5},   # 紅蘿蔔 0.5 條
    
    # 醬燒揚雞
    {"product_id": "prod-chicken-2", "material_id": "mat-1", "quantity": 1},     # 雞腿 1 份
    {"product_id": "prod-chicken-2", "material_id": "mat-4", "quantity": 0.2},   # 白飯 0.2 kg
    {"product_id": "prod-chicken-2", "material_id": "mat-5", "quantity": 0.1},   # 高麗菜 0.1 顆
    
    # 相撲豬太郎
    {"product_id": "prod-pork-1", "material_id": "mat-2", "quantity": 1.5},      # 豬排 1.5 份
    {"product_id": "prod-pork-1", "material_id": "mat-4", "quantity": 0.25},     # 白飯 0.25 kg
    {"product_id": "prod-pork-1", "material_id": "mat-5", "quantity": 0.1},      # 高麗菜 0.1 顆
    
    # 嫩嫩豬柳
    {"product_id": "prod-pork-2", "material_id": "mat-2", "quantity": 1},        # 豬排 1 份
    {"product_id": "prod-pork-2", "material_id": "mat-4", "quantity": 0.2},      # 白飯 0.2 kg
    
    # 燒肉多多
    {"product_id": "prod-pork-3", "material_id": "mat-2", "quantity": 1.2},      # 豬排 1.2 份
    {"product_id": "prod-pork-3", "material_id": "mat-4", "quantity": 0.2},      # 白飯 0.2 kg
    {"product_id": "prod-pork-3", "material_id": "mat-5", "quantity": 0.1},      # 高麗菜 0.1 顆
    
    # 家鄉豬腳
    {"product_id": "prod-pork-4", "material_id": "mat-10", "quantity": 1},       # 豬腳 1 份
    {"product_id": "prod-pork-4", "material_id": "mat-4", "quantity": 0.2},      # 白飯 0.2 kg
    {"product_id": "prod-pork-4", "material_id": "mat-7", "quantity": 1},        # 蛋 1 顆 (滷蛋)
    
    # 五告厚豬排
    {"product_id": "prod-pork-5", "material_id": "mat-2", "quantity": 1.5},      # 豬排 1.5 份
    {"product_id": "prod-pork-5", "material_id": "mat-4", "quantity": 0.2},      # 白飯 0.2 kg
    {"product_id": "prod-pork-5", "material_id": "mat-7", "quantity": 1},        # 蛋 1 顆
    
    # 藍帶豬排
    {"product_id": "prod-pork-6", "material_id": "mat-2", "quantity": 1},        # 豬排 1 份
    {"product_id": "prod-pork-6", "material_id": "mat-4", "quantity": 0.2},      # 白飯 0.2 kg
    {"product_id": "prod-pork-6", "material_id": "mat-8", "quantity": 2},        # 起司片 2 片
    {"product_id": "prod-pork-6", "material_id": "mat-9", "quantity": 2},        # 火腿片 2 片
    
    # 牛逼菲力
    {"product_id": "prod-beef-1", "material_id": "mat-3", "quantity": 1},        # 菲力牛排 1 份
    {"product_id": "prod-beef-1", "material_id": "mat-4", "quantity": 0.2},      # 白飯 0.2 kg
    {"product_id": "prod-beef-1", "material_id": "mat-5", "quantity": 0.1},      # 高麗菜 0.1 顆
    
    # 鄉村燉牛肉
    {"product_id": "prod-beef-2", "material_id": "mat-3", "quantity": 1},        # 牛肉 1 份
    {"product_id": "prod-beef-2", "material_id": "mat-4", "quantity": 0.2},      # 白飯 0.2 kg
    {"product_id": "prod-beef-2", "material_id": "mat-6", "quantity": 1},        # 紅蘿蔔 1 條
]


def generate_uuid() -> str:
    """產生 UUID"""
    return str(uuid.uuid4())


if __name__ == "__main__":
    # 可以在這裡加入資料庫寫入邏輯
    print("種子資料定義完成")
    print(f"分類數量: {len(CATEGORIES)}")
    print(f"商品數量: {len(PRODUCTS)}")
    print(f"物料數量: {len(MATERIALS)}")
    print(f"BOM 對應數量: {len(PRODUCT_MATERIALS)}")
    print(f"設定數量: {len(STORE_SETTINGS)}")

