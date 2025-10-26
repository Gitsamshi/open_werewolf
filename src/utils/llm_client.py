import boto3
import json
import time
from typing import Dict, List, Optional
from botocore.config import Config


class LLMClient:
    """LLM客户端，用于调用AWS Bedrock模型"""

    # 可用的模型列表（已移除DeepSeek和Claude 3.5 Sonnet不可用的模型）
    AVAILABLE_MODELS = [
        "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "us.anthropic.claude-opus-4-1-20250805-v1:0",
        "us.anthropic.claude-opus-4-20250514-v1:0"
    ]

    # 9个玩家的默认模型分配（打乱身份顺序，只使用Sonnet4/4.5和Opus4/4.1）
    DEFAULT_MODEL_ASSIGNMENT = {
        "狼人1": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "狼人2": "us.anthropic.claude-opus-4-1-20250805-v1:0",
        "狼人3": "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "预言家": "us.anthropic.claude-opus-4-20250514-v1:0",
        "女巫": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "猎人": "us.anthropic.claude-opus-4-1-20250805-v1:0",
        "村民1": "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "村民2": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "村民3": "us.anthropic.claude-opus-4-20250514-v1:0"
    }

    def __init__(self):
        """初始化Bedrock客户端"""
        # 配置超时和重试
        config = Config(
            read_timeout=120,  # 读取超时120秒
            connect_timeout=10,  # 连接超时10秒
            retries={
                'max_attempts': 3,  # 最大重试次数
                'mode': 'adaptive'  # 自适应重试模式
            }
        )

        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-west-2",
            config=config
        )

    def invoke_model(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 2000,
        temperature: float = 1.0,
        system_prompt: Optional[str] = None,
        max_retries: int = 2
    ) -> str:
        """
        调用指定的LLM模型（带重试机制）

        Args:
            model_id: 模型ID
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            max_tokens: 最大token数
            temperature: 温度参数
            system_prompt: 系统提示词
            max_retries: 最大手动重试次数（除了boto3自带的重试）

        Returns:
            模型的响应文本
        """
        # 构建请求体
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }

        # 添加系统提示词
        if system_prompt:
            request_body["system"] = system_prompt

        # 手动重试机制
        for attempt in range(max_retries + 1):
            try:
                # 调用模型
                response = self.client.invoke_model(
                    modelId=model_id,
                    body=json.dumps(request_body)
                )

                # 解析响应
                response_body = json.loads(response['body'].read())

                # 提取文本内容
                if "content" in response_body and len(response_body["content"]) > 0:
                    return response_body["content"][0]["text"]
                else:
                    return ""

            except Exception as e:
                error_msg = str(e)

                # 判断是否是超时错误
                is_timeout = "timeout" in error_msg.lower() or "timed out" in error_msg.lower()

                if attempt < max_retries:
                    if is_timeout:
                        print(f"⚠️ 模型 {model_id} 调用超时，正在重试 ({attempt + 1}/{max_retries})...")
                    else:
                        print(f"⚠️ 模型 {model_id} 调用失败: {error_msg}，正在重试 ({attempt + 1}/{max_retries})...")

                    # 等待一段时间后重试（指数退避）
                    wait_time = 2 ** attempt  # 1秒, 2秒, 4秒...
                    time.sleep(wait_time)
                else:
                    # 最后一次尝试失败，返回错误
                    if is_timeout:
                        print(f"❌ 模型 {model_id} 多次调用超时，已达最大重试次数")
                        print(f"   提示：该模型响应较慢，建议稍后重试或使用其他模型")
                    else:
                        print(f"❌ 调用模型 {model_id} 失败: {error_msg}")
                    return ""

        return ""

    def get_model_for_role(self, role_name: str) -> str:
        """
        获取指定角色的默认模型

        Args:
            role_name: 角色名称

        Returns:
            模型ID
        """
        return self.DEFAULT_MODEL_ASSIGNMENT.get(role_name, self.AVAILABLE_MODELS[0])
