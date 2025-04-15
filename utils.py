import os
import base64
import logging
from typing import List, Dict, Any, Optional, Tuple
import datetime
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from config import ZHIPUAI_CONFIG, IMAGE_CONFIG, ATTRIBUTE_MATCHING
from zhipuai_utils import call_zhipu_llm, analyze_image_with_zhipu

logger = logging.getLogger(__name__)


def call_llm(prompt: str, system_prompt: str = None, model: str = None) -> str:
    """
    调用大语言模型
    
    Args:
        prompt: 用户提示词
        system_prompt: 系统提示词，默认为专业电商分析助手
        model: 模型名称，默认使用配置中的模型
        
    Returns:
        str: 模型响应
    """
    try:
        if system_prompt is None:
            system_prompt = "你是一个专业的电商产品属性分析助手，请简洁直接地回答问题，仅返回所需结果。"
            
        if model is None:
            model = ZHIPUAI_CONFIG["default_model"]
            
        return call_zhipu_llm(prompt, system_prompt, model)
    except Exception as e:
        logger.error(f"LLM调用失败: {e}")
        return ""


def analyze_image(image_path: str, analysis_type: str) -> str:
    """
    分析图片获取特定信息
    
    Args:
        image_path: 图片路径
        analysis_type: 分析类型 (color, closure_type, shoe_toe_style等)
        
    Returns:
        str: 分析结果
    """
    if not image_path or not os.path.exists(image_path):
        logger.warning(f"图片路径不存在: {image_path}")
        return ""
        
    try:
        # 检查文件扩展名
        _, ext = os.path.splitext(image_path)
        if ext.lower() not in IMAGE_CONFIG["formats"]:
            logger.warning(f"不支持的图片格式: {ext}")
            return ""
        
        # 根据分析类型构建提示词
        prompts = {
            "closure_type": "这双鞋的闭合方式是什么（如系带、拉链、一脚蹬、魔术贴等）？请只回答闭合方式，不要有其他内容。",
            "shoe_toe_style": "这双鞋的鞋头款式是什么（如圆头、尖头、方头等）？请只回答鞋头款式，不要有其他内容。",
        }
        
        prompt = prompts.get(analysis_type, "描述这张图片的主要特征，请简洁回答。")
        
        # 使用智谱AI视觉模型分析图片
        result = analyze_image_with_zhipu(image_path, prompt)
        logger.info(f"图片分析结果 ({analysis_type}): {result}")
        return result
    except Exception as e:
        logger.error(f"图片分析失败: {e}")
        return ""


def find_best_attribute_match(attribute_name: str, available_attributes: List[str]) -> str:
    """
    在可用属性中找到与给定属性名称最匹配的属性
    
    Args:
        attribute_name: 要匹配的属性名称
        available_attributes: 可用的属性列表
        
    Returns:
        str: 最匹配的属性名称
    """
    # 如果属性名称在可用属性中，直接返回
    if attribute_name in available_attributes:
        return attribute_name
    
    # 检查是否有预定义的别名映射
    for main_attr, aliases in ATTRIBUTE_MATCHING["aliases"].items():
        if attribute_name in aliases and main_attr in available_attributes:
            return main_attr
    
    # 使用LLM进行语义匹配
    prompt = f"""
    在以下属性名称中，找出与"{attribute_name}"语义最接近或最相关的一项：
    {', '.join(available_attributes)}
    
    请直接返回最匹配的属性名称，不要有其他内容。
    """
    
    matched_attr = call_llm(prompt)
    
    # 确保匹配结果在可用属性中
    if matched_attr in available_attributes:
        return matched_attr
    else:
        # 找不到匹配项，返回原始属性名称
        return attribute_name


def find_best_value_match(query_value: str, available_values: List[str], attribute_type: str = None) -> str:
    """
    在可用值列表中找到与查询值最匹配的选项
    
    Args:
        query_value: 查询值
        available_values: 可用值列表
        attribute_type: 属性类型，用于特定类型的映射
        
    Returns:
        str: 最匹配的值
    """
    if not available_values:
        return ""
        
    if len(available_values) == 1:
        return available_values[0]
    
    # 检查预定义的值映射
    if attribute_type and attribute_type in ATTRIBUTE_MATCHING["value_mapping"]:
        value_map = ATTRIBUTE_MATCHING["value_mapping"][attribute_type]
        for standard_value, aliases in value_map.items():
            if query_value in aliases and standard_value in available_values:
                return standard_value
            
            # 检查部分匹配
            for alias in aliases:
                if alias in query_value and standard_value in available_values:
                    return standard_value
    
    # 使用LLM进行语义匹配
    prompt = f"""
    在以下选项中，找出与"{query_value}"语义最接近或最相关的一项：
    {', '.join(available_values)}
    
    请直接返回最匹配的选项，不要有其他内容。
    """
    
    matched_value = call_llm(prompt)
    
    # 确保匹配结果在可用值中
    if matched_value in available_values:
        return matched_value
    else:
        # 尝试再次匹配或返回第一个选项
        return available_values[0]


def get_current_season() -> str:
    """获取当前季节"""
    month = datetime.datetime.now().month
    if 3 <= month <= 5:
        return "春季"
    elif 6 <= month <= 8:
        return "夏季"
    elif 9 <= month <= 11:
        return "秋季"
    else:
        return "冬季"


def get_next_season() -> str:
    """获取下一个季节"""
    current_season = get_current_season()
    season_map = {
        "春季": "夏季",
        "夏季": "秋季",
        "秋季": "冬季",
        "冬季": "春季"
    }
    return season_map.get(current_season, "春季")


def extract_primary_material(material_str: str) -> str:
    """
    从材质字符串中提取主要材质
    例如："牛皮革+织物" -> "牛皮革"
    
    Args:
        material_str: 材质字符串
        
    Returns:
        str: 主要材质
    """
    if not material_str:
        return ""
        
    # 处理常见的分隔符
    for sep in ["+", "，", ",", "、", "/"]:
        if sep in material_str:
            return material_str.split(sep)[0].strip()
    
    return material_str.strip()


def clean_attribute_value(value: str) -> str:
    """
    清理属性值字符串
    
    Args:
        value: 属性值字符串
        
    Returns:
        str: 清理后的字符串
    """
    if not value:
        return ""
        
    # 移除常见的干扰词和格式
    value = value.replace("材质：", "").strip()
    value = value.replace("主要成分：", "").replace("类型：", "").strip()
    
    # 移除额外的标点符号
    for char in ["。", "！", "？", "；", "：", "、", "（", "）", "(", ")", "\"", "'"]:
        value = value.replace(char, "")
        
    return value.strip() 