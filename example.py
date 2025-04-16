import os
import json
import logging
from attribute_selector import AttributeSelector

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
PRODUCT_NUMBER = "123456"
def main():
    # 创建属性选择器实例
    selector = AttributeSelector()
    
    # 示例1: 处理季节属性
    product_number = PRODUCT_NUMBER
    attribute_name = "季节"
    available_values = ["春季", "夏季", "秋季", "冬季", "四季"]
    image_path = None  # 不需要图片
    
    result = selector.select_attribute_value(
        product_number,
        attribute_name,
        available_values,
        image_path
    )
    
    print("示例1 - 季节属性处理结果:")
    print(json.dumps(result, ensure_ascii=False))
    print("-" * 50)
    
    # 示例2: 处理季节属性
    product_number = PRODUCT_NUMBER
    attribute_name = "上市年份季节"
    available_values = ["春季", "夏季", "秋季", "冬季", "四季"]
    image_path = None  # 不需要图片
    
    result = selector.select_attribute_value(
        product_number,
        attribute_name,
        available_values,
        image_path
    )
    
    print("示例2 - 上市年份季节属性处理结果:")
    print(json.dumps(result, ensure_ascii=False))
    print("-" * 50)
    
    # 示例3: 处理材质属性
    product_number = PRODUCT_NUMBER
    attribute_name = "靴筒材质"
    available_values = ['乙纶', '二层牛皮（除牛反绒）', '二层猪皮', '头层牛皮（除牛反绒）', '头层猪皮', '孔雀皮', '多种材质拼接', '牛剖层革', '牛反绒', '牛皮', '牛皮革', '牛皮革+织物', '珍珠鱼皮', '皮革', '磨砂皮', '织物', '织物配皮', '羊反绒（羊猄）', '羊皮（除羊反绒/羊猄）', '羊驼皮', '腹膜皮', '超纤', '高丝光反绒皮', '鳗鱼皮', '羊皮（除羊反绒，羊猄）', '袋鼠皮', '帆布', '马皮', '漆皮', '麂皮', '胶皮', '鹿皮', '鸵鸟皮', '鳄鱼皮', '蜥蜴皮', '蛇皮', '太空革', 'PU', '羊皮毛一体', '绸缎', '绒面', '棉布', '亮片布', '灯芯绒', '网布', '塑胶', '藤草', '毛线', '牛仔布', '牛皮绒面革']
    image_path = None  # 这个示例中假设数据库中有材质信息
    
    result = selector.select_attribute_value(
        product_number,
        attribute_name,
        available_values,
        image_path
    )
    
    print("示例3 - 材质属性处理结果 (通过智谱AI语义匹配):")
    print(json.dumps(result, ensure_ascii=False))
    print("-" * 50)
    
    # 示例4: 处理闭合方式属性(需要图片分析)
    # 确保有测试图片，否则会报错或返回空结果
    product_number = PRODUCT_NUMBER
    attribute_name = "闭合方式"
    available_values = ['系带', '拉链', '搭扣', '其他', '套筒', '魔术贴']
    image_path = "test_img.jpg"  # 确保此图片存在
    
    # 检查图片是否存在
    if not os.path.exists(image_path):
        logger.warning(f"测试图片不存在，请确保路径正确: {image_path}")
        print(f"示例4 - 闭合方式: 图片不存在，跳过测试")
    else:
        result = selector.select_attribute_value(
            product_number,
            attribute_name,
            available_values,
            image_path
        )
        
        print("示例4 - 闭合方式属性处理结果 (通过智谱AI视觉分析):")
        print(json.dumps(result, ensure_ascii=False))
    
    print("-" * 50)
    
    # 示例5: 处理同义属性名称
    product_number = PRODUCT_NUMBER
    attribute_name = "靴筒材质"  
    available_values =['乙纶', '二层牛皮（除牛反绒）', '二层猪皮', '头层牛皮（除牛反绒）', '头层猪皮', '孔雀皮', '多种材质拼接', '牛剖层革', '牛反绒', '牛皮', '牛皮革', '牛皮革+织物', '珍珠鱼皮', '皮革', '磨砂皮', '织物', '织物配皮', '羊反绒（羊猄）', '羊皮（除羊反绒/羊猄）', '羊驼皮', '腹膜皮', '超纤', '高丝光反绒皮', '鳗鱼皮', '羊皮（除羊反绒，羊猄）', '袋鼠皮', '帆布', '马皮', '漆皮', '麂皮', '胶皮', '鹿皮', '鸵鸟皮', '鳄鱼皮', '蜥蜴皮', '蛇皮', '太空革', 'PU', '羊皮毛一体', '绸缎', '绒面', '棉布', '亮片布', '灯芯绒', '网布', '塑胶', '藤草', '毛线', '牛仔布', '牛皮绒面革']
    image_path = None
    
    result = selector.select_attribute_value(
        product_number,
        attribute_name,
        available_values,
        image_path
    )
    
    print("示例5 - 别名属性处理结果:")
    print(json.dumps(result, ensure_ascii=False))
    print("-" * 50)
    
    # 示例6: 处理尺寸相关属性
    product_number = PRODUCT_NUMBER
    attribute_name = "后跟高"
    available_values = ["平跟(小于1cm)", "低跟(1-3cm)", "中跟(3-5cm)", "高跟(5-8cm)", "超高跟(8cm以上)"]
    image_path = None
    
    result = selector.select_attribute_value(
        product_number,
        attribute_name,
        available_values,
        image_path
    )
    
    print("示例6 - 尺寸属性处理结果:")
    print(json.dumps(result, ensure_ascii=False))
    print("-" * 50)
    
    # 示例7: 处理靴筒高度
    product_number = PRODUCT_NUMBER
    attribute_name = "靴筒高度"
    available_values = ["低筒(10cm以下)", "中筒(10-20cm)", "高筒(20-40cm)", "过膝靴(40cm以上)"]
    image_path = None
    
    result = selector.select_attribute_value(
        product_number,
        attribute_name,
        available_values,
        image_path
    )
    
    print("示例7 - 靴筒高度属性处理结果:")
    print(json.dumps(result, ensure_ascii=False))
    print("-" * 50)
    
    # 关闭数据库连接
    selector.db.close()

if __name__ == "__main__": 
    main() 