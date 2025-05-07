import base64
import logging
import time
import requests
from openai import OpenAI
from typing import  Optional, List, Dict, Any
from config import OPENAI_CONFIG

logger = logging.getLogger(__name__)


class OpenAI:
    """OpenAI API客户端"""
    
    def __init__(self, api_key=None, base_url=None):
        """
        初始化OpenAI客户端
        
        Args:
            api_key: API密钥，如不提供则从配置中获取
            base_url: API基础URL，如不提供则从配置中获取
        """
        self.api_key = api_key or OPENAI_CONFIG["api_key"]
        self.base_url = base_url or OPENAI_CONFIG["base_url"]
        self.chat = ChatCompletions(self.api_key, self.base_url)


class ChatCompletions:
    
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        
    def _get_auth_headers(self):
        """获取包含认证信息的请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def create(self, model: str, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        创建聊天请求
        
        Args:
            model: 模型名称
            messages: 消息列表
            **kwargs: 其他参数，如temperature等
            
        Returns:
            Dict[str, Any]: OpenAI响应结果
        """
        url = f"{self.base_url}/chat/completions"
        
        # 构建请求数据
        data = {
            "model": model,
            "messages": messages,
        }
        
        # 添加其他参数
        if "temperature" in kwargs:
            data["temperature"] = kwargs["temperature"]
        
        if "max_tokens" in kwargs:
            data["max_tokens"] = kwargs["max_tokens"]
        
        # 发送请求
        try:
            response = requests.post(url, headers=self._get_auth_headers(), json=data)
            response.raise_for_status()
            result = response.json()
            
            # 构造与OpenAI格式类似的响应
            transformed_response = {
                "id": result.get("id", ""),
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        },
                        "finish_reason": result.get("choices", [{}])[0].get("finish_reason", "stop")
                    }
                ],
                "usage": result.get("usage", {})
            }
            
            return transformed_response
            
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            # 返回一个空响应结构以保持接口一致性
            return {
                "id": "",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": ""
                        },
                        "finish_reason": "error"
                    }
                ],
                "usage": {},
                "error": str(e)
            }


def encode_image_to_base64(image_path: str) -> Optional[str]:
    """
    将图像编码为base64字符串
    
    Args:
        image_path: 图像文件路径
        
    Returns:
        Optional[str]: base64编码的图像字符串，如果失败则返回None
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"图像编码失败: {e}")
        return None


def call_openai_llm(prompt: str, system_prompt: str = None, model: str = None) -> str:
    """
    调用OpenAI大语言模型
    
    Args:
        prompt: 用户提示词
        system_prompt: 系统提示词
        model: 模型名称，默认使用配置中的模型
        
    Returns:
        str: 模型响应
    """
    try:
        if model is None:
            model = OPENAI_CONFIG["default_model"]
            
        messages = []
        
        # 添加系统消息
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        # 添加用户消息
        messages.append({"role": "user", "content": prompt})
        
        # 初始化客户端
        client = OpenAI(
            api_key=OPENAI_CONFIG["api_key"],
            base_url=OPENAI_CONFIG["base_url"]
        )
        
        # 发送请求
        response = client.chat.create(
            model=model,
            messages=messages,
            temperature=0.0,
            max_tokens=1000
        )
        
        result = response["choices"][0]["message"]["content"]
        return result.strip()
        
    except Exception as e:
        logger.error(f"OpenAI调用失败: {e}")
        return ""


def analyze_image_with_openai(image_path: str, prompt: str) -> str:
    """
    使用OpenAI分析图片
    
    Args:
        image_path: 图片路径
        prompt: 提示词
        
    Returns:
        str: 分析结果
    """
    try:
        # 将图片编码为base64
        image_base64 = encode_image_to_base64(image_path)
        if not image_base64:
            return ""
        
        # 构建消息
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
        
        # 初始化客户端
        client = OpenAI(
            api_key=OPENAI_CONFIG["api_key"],
            base_url=OPENAI_CONFIG["base_url"]
        )
        
        # 调用OpenAI视觉模型
        response = client.chat.create(
            model=OPENAI_CONFIG["vision_model"],
            messages=messages,
            max_tokens=100
        )
        
        result = response["choices"][0]["message"]["content"]
        return result.strip()
        
    except Exception as e:
        logger.error(f"OpenAI图像分析失败: {e}")
        return "" 