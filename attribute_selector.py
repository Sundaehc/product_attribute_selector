import os
import sys
import logging
import argparse
import json
import datetime
from typing import List, Dict, Any, Optional, Tuple

from database import ProductDatabase
from utils import (
    call_llm, 
    analyze_image, 
    find_best_attribute_match, 
    find_best_value_match,
    get_current_season,
    get_next_season,
    extract_primary_material,
    clean_attribute_value
)
from config import ATTRIBUTE_MATCHING, IMAGE_CONFIG

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AttributeSelector:
    """产品属性选择器"""
    
    def __init__(self, db_connection=None):
        """
        初始化属性选择器
        
        Args:
            db_connection: 数据库连接对象，如果为None则创建新连接
        """
        self.db = db_connection or ProductDatabase()
        
    def select_attribute_value(self, 
                              product_number: str, 
                              attribute_name: str, 
                              available_values: List[str], 
                              image_path: Optional[str] = None) -> List[str]:
        """
        为产品选择最合适的属性值
        
        Args:
            product_number: 产品货号
            attribute_name: 属性名称
            available_values: 可用的属性值列表
            image_path: 产品图片路径
            
        Returns:
            List[str]: [产品货号, 选择的属性值]
        """
        logger.info(f"处理产品 {product_number} 的属性: {attribute_name}")
        logger.info(f"可用属性值: {available_values}")
        
        # 检查图片路径和格式
        if image_path:
            if not os.path.exists(image_path):
                logger.warning(f"图片路径不存在: {image_path}")
                image_path = None
            else:
                _, ext = os.path.splitext(image_path)
                if ext.lower() not in IMAGE_CONFIG["formats"]:
                    logger.warning(f"不支持的图片格式: {ext}，支持的格式为: {IMAGE_CONFIG['formats']}")
                    image_path = None
        
        # 清理和规范化属性名称
        attribute_name = attribute_name.strip()
        
        # 查找对应的标准属性名
        standard_attribute = self._find_standard_attribute(attribute_name)
        logger.info(f"标准化属性名称: {standard_attribute}")
        
        # 根据不同的属性类型选择不同的处理方法
        selected_value = ""
        
        # 季节相关属性处理
        if self._is_season_attribute(attribute_name):
            selected_value = self._process_season_attribute(attribute_name, available_values)
        
        # 材质相关属性处理
        elif self._is_material_attribute(standard_attribute):
            selected_value = self._process_material_attribute(product_number, standard_attribute, available_values)
        
        # 尺寸相关属性处理
        elif self._is_size_attribute(standard_attribute):
            selected_value = self._process_size_attribute(product_number, standard_attribute, available_values)
        
        # 闭合方式属性处理
        elif self._is_closure_attribute(standard_attribute):
            selected_value = self._process_closure_attribute(image_path, available_values)
        
        # 鞋头款式属性处理
        elif self._is_toe_style_attribute(standard_attribute):
            selected_value = self._process_toe_style_attribute(image_path, available_values)
        
        # 其他属性的通用处理
        else:
            selected_value = self._process_general_attribute(product_number, standard_attribute, available_values)
        
        # 如果没有找到匹配的值，使用LLM从可用值列表中选择最合适的
        if not selected_value and available_values:
            logger.info("使用通用语义匹配选择属性值")
            attr_type = standard_attribute if standard_attribute in ATTRIBUTE_MATCHING.get("value_mapping", {}) else None
            selected_value = find_best_value_match("", available_values, attr_type)
        
        # 如果仍然没有找到匹配的值，选择第一个可用值
        if not selected_value and available_values:
            logger.warning(f"未找到匹配的属性值，使用第一个可用值: {available_values[0]}")
            selected_value = available_values[0]
        
        logger.info(f"最终选择的属性值: {selected_value}")
        return [product_number, selected_value]
    
    def _find_standard_attribute(self, attribute_name: str) -> str:
        """查找标准化的属性名称"""
        # 直接匹配别名
        aliases = ATTRIBUTE_MATCHING.get("aliases", {})
        for std_attr, alias_list in aliases.items():
            if attribute_name == std_attr or attribute_name in alias_list:
                return std_attr
        
        # 使用LLM进行语义匹配
        standard_attrs = list(aliases.keys())
        prompt = f"""
        在以下属性中，找出与"{attribute_name}"语义最相似的一项:
        {', '.join(standard_attrs)}
        
        请直接返回最匹配的属性名称，不要有其他内容。
        """
        matched = call_llm(prompt)
        if matched in standard_attrs:
            return matched
        
        return attribute_name
    
    def _is_season_attribute(self, attribute_name: str) -> bool:
        """判断是否为季节相关属性"""
        season_keywords = ["季节", "适用季节", "上市年份季节"]
        return any(keyword in attribute_name for keyword in season_keywords)
    
    def _is_material_attribute(self, attribute_name: str) -> bool:
        """判断是否为材质相关属性"""
        material_keywords = ["材质", "面料", "帮面", "靴筒"]
        return any(keyword in attribute_name for keyword in material_keywords)
    
    def _is_size_attribute(self, attribute_name: str) -> bool:
        """判断是否为尺寸相关属性"""
        size_keywords = ["高度", "厚度", "后跟高", "靴筒高", "鞋跟高"]
        return any(keyword in attribute_name for keyword in size_keywords)
    
    def _is_closure_attribute(self, attribute_name: str) -> bool:
        """判断是否为闭合方式属性"""
        closure_keywords = ["闭合方式", "鞋扣"]
        return any(keyword in attribute_name for keyword in closure_keywords)
    
    def _is_toe_style_attribute(self, attribute_name: str) -> bool:
        """判断是否为鞋头款式属性"""
        toe_keywords = ["鞋头", "鞋尖"]
        return any(keyword in attribute_name for keyword in toe_keywords)
    
    def _process_season_attribute(self, attribute_name: str, available_values: List[str]) -> str:
        """处理季节相关属性"""
        if "上市年份" in attribute_name:
            current_year = str(datetime.datetime.now().year)
            current_season = get_current_season()
            
            # 寻找包含当前年份和当前季节的选项
            year_season = f"{current_year}{current_season}"
            
            for value in available_values:
                if current_year in value and current_season in value:
                    return value
            
            # 如果没有找到精确匹配，使用LLM选择最接近的
            prompt = f"""
            在以下选项中，找出与"{year_season}"最匹配的一项:
            {', '.join(available_values)}
            
            请直接返回最匹配的选项，不要有其他内容。
            """
            return call_llm(prompt)
        else:
            next_season = get_next_season()
            
            for value in available_values:
                if next_season in value:
                    return value
            
            return find_best_value_match(next_season, available_values)
    
    def _process_material_attribute(self, product_number: str, attribute_name: str, available_values: List[str]) -> str:
        """处理材质相关属性"""
        # 从数据库获取产品材质信息
        product_data = self.db.get_product_data(product_number, ["材质", "鞋面材质", "帮面材质", attribute_name])
        
        material = ""
        if attribute_name in product_data:
            material = product_data[attribute_name]
        elif "鞋面材质" in product_data:
            material = product_data["鞋面材质"]
        elif "帮面材质" in product_data:
            material = product_data["帮面材质"]
        elif "材质" in product_data:
            material = product_data["材质"]
        
        if material:
            # 提取主要材质（如果有多种材质）
            primary_material = extract_primary_material(material)
            # 在可用值中找到最匹配的
            return find_best_value_match(primary_material, available_values, "材质")
        
        return ""
    
    def _process_size_attribute(self, product_number: str, attribute_name: str, available_values: List[str]) -> str:
        """处理尺寸相关属性"""
        # 从数据库获取产品尺寸信息
        size_attributes = [
            attribute_name, "后跟高", "靴筒高度", "鞋跟高度",
            "heel_height", "tube_height", "platform_height"
        ]
        product_data = self.db.get_product_data(product_number, size_attributes)
        
        size_value = ""
        # 首先尝试直接获取属性值
        if attribute_name in product_data:
            size_value = product_data[attribute_name]
        else:
            # 根据属性名称尝试找到匹配的值
            if "后跟高" in attribute_name or "鞋跟高" in attribute_name:
                for field in ["后跟高", "鞋跟高度", "heel_height"]:
                    if field in product_data:
                        size_value = product_data[field]
                        break
            elif "靴筒高" in attribute_name:
                for field in ["靴筒高度", "tube_height"]:
                    if field in product_data:
                        size_value = product_data[field]
                        break
            elif "底厚" in attribute_name or "台高" in attribute_name:
                for field in ["鞋底厚度", "platform_height"]:
                    if field in product_data:
                        size_value = product_data[field]
                        break
        
        if size_value:
            # 清理尺寸值，确保格式正确
            size_value = clean_attribute_value(size_value)
            
            # 在可用值列表中寻找匹配的值
            return find_best_value_match(size_value, available_values)
        
        return ""
    
    def _process_closure_attribute(self, image_path: str, available_values: List[str]) -> str:
        """处理闭合方式属性"""
        if not image_path or not os.path.exists(image_path):
            logger.warning("缺少图片，无法分析闭合方式")
            return ""
        
        # 使用图像分析获取闭合方式
        closure_type = analyze_image(image_path, "closure_type")
        if closure_type:
            # 在可用值中找到最匹配的
            return find_best_value_match(closure_type, available_values, "闭合方式")
        
        return ""
    
    def _process_toe_style_attribute(self, image_path: str, available_values: List[str]) -> str:
        """处理鞋头款式属性"""
        if not image_path or not os.path.exists(image_path):
            logger.warning("缺少图片，无法分析鞋头款式")
            return ""
        
        # 使用图像分析获取鞋头款式
        toe_style = analyze_image(image_path, "shoe_toe_style")
        if toe_style:
            # 在可用值中找到最匹配的
            return find_best_value_match(toe_style, available_values)
        
        return ""
    
    
    def _process_general_attribute(self, product_number: str, attribute_name: str, available_values: List[str]) -> str:
        """处理一般属性"""
        # 从数据库获取对应属性的信息
        product_data = self.db.get_product_data(product_number, [attribute_name])
        
        if attribute_name in product_data:
            value = clean_attribute_value(product_data[attribute_name])
            return find_best_value_match(value, available_values)
        
        return ""


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="产品属性选择系统")
    parser.add_argument("product_number", help="产品货号")
    parser.add_argument("attribute_name", help="属性名称")
    parser.add_argument("available_values", help="可用属性值列表，JSON格式")
    parser.add_argument("--image", help="产品图片路径")
    
    args = parser.parse_args()
    
    try:
        # 解析可用属性值列表
        available_values = json.loads(args.available_values)
        if not isinstance(available_values, list):
            raise ValueError("available_values 必须是JSON列表")
        
        # 创建属性选择器
        selector = AttributeSelector()
        
        # 选择属性值
        result = selector.select_attribute_value(
            args.product_number,
            args.attribute_name,
            available_values,
            args.image
        )
        
        # 输出结果
        print(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        logger.error(f"处理过程中出错: {e}")
        print(json.dumps([args.product_number, ""], ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main() 