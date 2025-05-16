import os
import logging
from typing import List
import datetime
from sentence_transformers import SentenceTransformer, util
from config import OPENAI_CONFIG, IMAGE_CONFIG, ATTRIBUTE_MATCHING
from openai_utils import call_openai_llm, analyze_image_with_openai

logger = logging.getLogger(__name__)

# 加载模型
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

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
            model = OPENAI_CONFIG["default_model"]
            
        return call_openai_llm(prompt, system_prompt, model)
    except Exception as e:
        logger.error(f"LLM调用失败: {e}")
        return ""


def analyze_image(image_path: str, analysis_type: str) -> str:
    """
    分析图片获取特定信息
    
    Args:
        image_path: 图片路径
        analysis_type: 分析类型 (closure_type, shoe_toe_style, heel_shape， heel_height， opening_depth等)
        
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
            "closure_type": "这双鞋的闭合方式是什么（如系带、拉链、一脚蹬、魔术贴等)？请只回答闭合方式，不要有其他内容。",
            "shoe_toe_style": "这双鞋的鞋头款式是什么（如圆头、尖头、方头、鱼嘴、杏头等）？请只回答鞋头款式，不要有其他内容。",
            "heel_shape": "这双鞋的鞋跟款式是什么（如平跟、圆跟、方跟、尖跟、马蹄跟、坡跟、松糕跟、防水台等）？请只回答鞋跟款式，不要有其他内容。",
            "heel_height": "这双鞋的鞋跟高度是多少（如低跟，平跟、中跟，高跟，超高跟等）？请只回答鞋跟高度，不要有其他内容。",
            "opening_depth": "这双鞋的开口深度是多少（如浅口，中口，深口）？请只回答开口深度，不要有其他内容",
            "style": "这双鞋的风格是什么（如少女风，田园风，民族风，休闲风，极简风，嘻哈风，洛丽塔风，公主风，舒适，性感风等）？请只回答风格，不要有其他内容。",
            "shoe_shape": "这双鞋的款式是什么（如布鞋,单鞋,乐福鞋,豆豆鞋,穆勒鞋,牛津鞋,时尚休闲鞋,松糕鞋,摇摇鞋,休闲板鞋,帆布鞋,高帮鞋,方根高跟鞋,坡跟鞋,细跟高跟鞋,洞洞鞋,时尚休闲沙滩鞋,时装凉鞋,时尚雪地靴,雨鞋,包头拖,人字拖,一字拖, 弹力靴,袜靴,短靴,马丁靴,切尔西靴,时装靴等）？请只回答款式，不要有其他内容。"
        }
        
        prompt = prompts.get(analysis_type, "描述这张图片的主要特征，请简洁回答。")
        
        # 使用智谱AI视觉模型分析图片
        result = analyze_image_with_openai(image_path, prompt)
        logger.info(f"图片分析结果 ({analysis_type}): {result}")
        return result
    except Exception as e:
        logger.error(f"图片分析失败: {e}")
        return ""


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
    给出以下可选值:{','.join(available_values)},找出与{query_value}语义匹配相近或者与{query_value}值相等的选项;
    如果{query_value}是数字，请直接返回与{query_value}匹配的以下鞋跟高度选项:低跟1-3cm,中跟3cm-5cm,高跟6cm-8cm,超高跟8cm以上,平跟小于1cm;
    请直接返回最匹配的选项，不要返回其他多余内容。
    """
    matched_value = call_llm(prompt)
    logger.info(f"可选值: {', '.join(available_values)}")
    logger.info(f"查询值: {query_value}")
    logger.info(f"语义匹配结果: {matched_value}")
    # 如果matched_value有多个值，调用模型重新进行语义匹配
    if "," in matched_value:
        # 输入词汇
        input_word = query_value
        candidate_words = available_values
        # 生成嵌入
        input_embedding = model.encode(input_word, convert_to_tensor=True)
        candidate_embeddings = model.encode(candidate_words, convert_to_tensor=True)
        # 计算余弦相似度
        similarities = util.cos_sim(input_embedding, candidate_embeddings)[0]
        # 找到最相似的词汇
        max_index = similarities.argmax()
        matched_value = candidate_words[max_index]
    
    if matched_value in available_values:
        return matched_value
    else:
        # 返回空
        return ""


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