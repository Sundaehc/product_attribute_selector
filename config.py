import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据库配置
DB_CONFIG = {
    "mysql": {
        "host": "localhost",
        "port": 3306,
        "user": "",
        "password": "",
        "database": "",
        "charset": "utf8mb4"
    }
}

# API配置
OPENAI_CONFIG = {
    "api_key": "your_api_key",
    "default_model": "glm-4v-flash",  
    "vision_model": "glm-4v-flash",  
    "base_url": "https://open.bigmodel.cn/api/paas/v4", 
}

# 老张API配置
LAOZHANG_CONFIG = {
    "api_key": "your_api_key",
    "default_model": "deepseek-chat",    
    "base_url": "https://api.laozhang.ai/v1",
}

# 火山引擎配置
VOLCENGINE_CONFIG = {
    "api_key": "your_api_key",
    "default_model": "deepseek-r1-250120",    
}

# 日志配置
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": os.path.join(BASE_DIR, "logs", "product_attribute.log"),
}

# 图像处理配置
IMAGE_CONFIG = {
    "max_size": (512, 512), 
    "formats": [".jpg", ".jpeg", ".png", ".webp"],  
}

# 属性匹配配置
ATTRIBUTE_MATCHING = {
    "aliases": {
        "鞋面材质": ["帮面材质", "靴筒面材质", "鞋帮材质"],
        "鞋底材质": ["鞋底材质", "鞋底材料", "鞋底材料类型"],
        "鞋垫材质": ["鞋垫材质", "鞋垫材料", "鞋垫材料类型"],
        "内里材质": ["鞋面内里材质", "靴筒内里材质"],
        "闭合方式": ["鞋子闭合方式", "鞋扣方式"],
        "开口深度": ["开口深度", "开口大小"],
        "风格": ["鞋子风格"],
        "款式": ["鞋子款式"],
        "鞋头款式": ["鞋头样式", "鞋尖样式"],
        "鞋跟款式": ["鞋跟样式", "后跟样式"],
        "季节": ["适用季节", "使用季节", "上市年份季节"],
        "后跟高": ["鞋跟高度", "跟高", "鞋后跟高度"],
        "靴筒高度": ["靴筒高", "筒高"],
        "鞋底厚度": ["前底厚度", "台高", "鞋底高度", "前底高度"],
    },

    "value_mapping": {
        "材质": {
            "真皮": ["头层牛皮", "牛皮", "真牛皮", "二层牛皮(除牛反绒)","二层猪皮"],
            "人造革": ["PU", "PU革", "合成革", "人工革"],
            "织物": ["布料", "纺织物","纺织"],
        },
        "闭合方式": {
            "系带": ["鞋带", "系鞋带"],
            "魔术贴": ["粘扣", "魔鬼贴", "尼龙贴"],
            "拉链": ["侧拉链"],
            "套脚": ["一脚蹬", "懒人", "无扣", "直接套"],
        },
        "后跟高": {
            "低跟(1-3cm)": ["1cm", "2cm", "3cm", "1-3cm", "低跟"],
            "中跟(3-5cm)": ["3-5cm", "4cm", "5cm", "中跟"],
            "高跟(5-8cm)": ["5-8cm", "6cm", "7cm", "8cm", "高跟"],
            "超高跟(8cm以上)": ["8cm以上", "9cm", "10cm", "超高跟"],
            "平跟(小于1cm)": ["0cm", "0.5cm", "1cm以下", "平跟"],
        },
    },
} 