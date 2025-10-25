"""
游戏配置示例

如果你想自定义AI模型分配，可以修改 src/utils/llm_client.py 中的 DEFAULT_MODEL_ASSIGNMENT
"""

# 默认的AI模型分配方案（仅使用Claude系列可用模型）
DEFAULT_MODEL_ASSIGNMENT = {
    "狼人1": "us.anthropic.claude-opus-4-20250514-v1:0",
    "狼人2": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "狼人3": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "预言家": "us.anthropic.claude-opus-4-1-20250805-v1:0",
    "女巫": "us.anthropic.claude-sonnet-4-20250514-v1:0",
    "猎人": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "村民1": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "村民2": "us.anthropic.claude-opus-4-20250514-v1:0",
    "村民3": "us.anthropic.claude-sonnet-4-20250514-v1:0"
}

# 可选的模型分配方案1：全部使用Claude Opus
OPUS_ONLY_ASSIGNMENT = {
    "狼人1": "us.anthropic.claude-opus-4-20250514-v1:0",
    "狼人2": "us.anthropic.claude-opus-4-1-20250805-v1:0",
    "狼人3": "us.anthropic.claude-opus-4-20250514-v1:0",
    "预言家": "us.anthropic.claude-opus-4-1-20250805-v1:0",
    "女巫": "us.anthropic.claude-opus-4-20250514-v1:0",
    "猎人": "us.anthropic.claude-opus-4-1-20250805-v1:0",
    "村民1": "us.anthropic.claude-opus-4-20250514-v1:0",
    "村民2": "us.anthropic.claude-opus-4-1-20250805-v1:0",
    "村民3": "us.anthropic.claude-opus-4-20250514-v1:0"
}

# 可选的模型分配方案2：混合使用不同级别的Claude模型
MIXED_ASSIGNMENT = {
    "狼人1": "us.anthropic.claude-opus-4-20250514-v1:0",
    "狼人2": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "狼人3": "us.anthropic.claude-sonnet-4-20250514-v1:0",
    "预言家": "us.anthropic.claude-opus-4-1-20250805-v1:0",
    "女巫": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "猎人": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    "村民1": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "村民2": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "村民3": "us.anthropic.claude-haiku-4-5-20251001-v1:0"
}

# 可选的模型分配方案3：成本优化（使用更便宜的模型）
COST_OPTIMIZED_ASSIGNMENT = {
    "狼人1": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "狼人2": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "狼人3": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "预言家": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "女巫": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "猎人": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "村民1": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "村民2": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "村民3": "us.anthropic.claude-haiku-4-5-20251001-v1:0"
}

# 说明：
# 1. Opus系列：最强大，推理能力最好，成本最高
# 2. Sonnet系列：平衡性能和成本，主力模型
# 3. Haiku系列：快速且经济，适合简单角色
#
# 注意：已移除DeepSeek和Claude 3.5 Sonnet模型，因为它们在当前区域不可用
