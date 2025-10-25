import boto3
import json
from typing import Dict, List, Optional


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

    # 9个玩家的默认模型分配（仅使用Claude系列可用模型）
    DEFAULT_MODEL_ASSIGNMENT = {
        "狼人1": "us.anthropic.claude-opus-4-20250514-v1:0",
        "狼人2": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "狼人3": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "预言家": "us.anthropic.claude-opus-4-1-20250805-v1:0",
        "女巫": "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "猎人": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "村民1": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        "村民2": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "村民3": "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    }

    def __init__(self):
        """初始化Bedrock客户端"""
        self.client = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-west-2"
        )

    def invoke_model(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 2000,
        temperature: float = 1.0,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        调用指定的LLM模型

        Args:
            model_id: 模型ID
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            max_tokens: 最大token数
            temperature: 温度参数
            system_prompt: 系统提示词

        Returns:
            模型的响应文本
        """
        try:
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
            print(f"调用模型 {model_id} 时出错: {str(e)}")
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
