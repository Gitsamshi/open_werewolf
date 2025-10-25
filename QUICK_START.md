# 快速开始指南

## 5分钟快速上手

### 1. 检查环境
```bash
python3 --version  # 需要 Python 3.8+
```

### 2. 安装依赖
```bash
pip install boto3
```

### 3. 配置AWS（三选一）

**方式A - AWS CLI（推荐）**
```bash
aws configure
```

**方式B - 环境变量**
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-west-2
```

**方式C - .env文件**
```bash
cp .env.example .env
# 编辑.env文件填入凭证
```

### 4. 测试环境（可选）
```bash
python test_setup.py
```

### 5. 开始游戏
```bash
# 方式1: 使用脚本
./run.sh

# 方式2: 直接运行
python main.py
```

## 游戏模式选择

启动后选择：
- **0** = 观看9个AI对战
- **1** = 你 + 8个AI
- **2-9** = 自定义人数

## 基本操作

### 如果你是人类玩家

**夜晚行动**
```
请输入玩家编号: 3
```

**白天发言**
```
请输入发言: 我是预言家，昨晚查验3号是狼人
```

**投票**
```
请输入玩家编号: 3
```

## 角色快速参考

| 角色 | 技能 | 目标 |
|------|------|------|
| 狼人 | 每晚杀1人 | 杀光神职或平民 |
| 预言家 | 每晚查1人 | 找出狼人 |
| 女巫 | 解药+毒药各1 | 找出狼人 |
| 猎人 | 死时开枪 | 找出狼人 |
| 村民 | 无技能 | 找出狼人 |

## 常用命令

```bash
# 测试环境
python test_setup.py

# 开始游戏
python main.py

# 查看帮助
cat README.md

# 查看规则
cat GAMEPLAY.md

# 查看FAQ
cat FAQ.md
```

## 故障排除

### 问题：没有AWS凭证
```bash
aws configure
```

### 问题：模型不可用
检查区域是否为 us-west-2

### 问题：游戏卡住
按 Ctrl+C 中断，重新开始

## 成本提示

**省钱配置**
- 使用 Haiku 或 DeepSeek 模型
- 修改 `src/utils/llm_client.py` 中的模型分配

**默认配置**
- 一局游戏约 $0.10 - $1.00（取决于模型和游戏时长）

## 下一步

- 📖 阅读 [README.md](README.md) 了解详细信息
- 🎮 阅读 [GAMEPLAY.md](GAMEPLAY.md) 学习游戏策略
- ❓ 遇到问题查看 [FAQ.md](FAQ.md)
- ⚙️ 查看 [config_example.py](config_example.py) 自定义配置

## 享受游戏！

记住：
- 🎯 好人要找出狼人
- 🐺 狼人要隐藏身份
- 🧠 多观察，多思考
- 🎉 享受游戏过程
