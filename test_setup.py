#!/usr/bin/env python3
"""
环境测试脚本
用于验证AWS Bedrock连接和模型可用性
"""

import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


def test_aws_credentials():
    """测试AWS凭证"""
    print("测试AWS凭证...")
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✓ AWS凭证有效")
        print(f"  账户ID: {identity['Account']}")
        print(f"  ARN: {identity['Arn']}")
        return True
    except NoCredentialsError:
        print("✗ 未找到AWS凭证")
        print("  请配置AWS凭证（使用aws configure或设置环境变量）")
        return False
    except Exception as e:
        print(f"✗ AWS凭证测试失败: {str(e)}")
        return False


def test_bedrock_access():
    """测试Bedrock访问权限"""
    print("\n测试Bedrock访问...")
    try:
        bedrock = boto3.client('bedrock', region_name='us-west-2')
        bedrock.list_foundation_models()
        print("✓ Bedrock服务可访问")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'AccessDeniedException':
            print("✗ 无权访问Bedrock服务")
            print("  请确保你的AWS账户有Bedrock权限")
        else:
            print(f"✗ Bedrock访问测试失败: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ Bedrock访问测试失败: {str(e)}")
        return False


def test_model_availability():
    """测试模型可用性"""
    print("\n测试模型可用性...")

    models_to_test = [
        "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "us.anthropic.claude-sonnet-4-20250514-v1:0",
        "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        "us.anthropic.claude-opus-4-1-20250805-v1:0",
        "us.anthropic.claude-opus-4-20250514-v1:0",
    ]

    bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-west-2')
    available_count = 0

    for model_id in models_to_test:
        try:
            # 尝试一个简单的调用
            import json
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "hi"}]
                })
            )
            print(f"✓ {model_id} 可用")
            available_count += 1
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                print(f"✗ {model_id} 无访问权限")
            elif error_code == 'ResourceNotFoundException':
                print(f"✗ {model_id} 不存在")
            else:
                print(f"✗ {model_id} 测试失败: {error_code}")
        except Exception as e:
            print(f"✗ {model_id} 测试失败: {str(e)}")

    if available_count > 0:
        print(f"\n✓ 测试了{len(models_to_test)}个模型，{available_count}个可用")
        return True
    else:
        print(f"\n✗ 没有可用的模型")
        return False


def main():
    """主函数"""
    print("="*60)
    print("狼人杀游戏 - 环境配置测试")
    print("="*60)
    print()

    all_tests_passed = True

    # 测试AWS凭证
    if not test_aws_credentials():
        all_tests_passed = False

    # 测试Bedrock访问
    if not test_bedrock_access():
        all_tests_passed = False

    # 测试模型可用性
    if not test_model_availability():
        all_tests_passed = False

    # 总结
    print("\n" + "="*60)
    if all_tests_passed:
        print("✓ 所有测试通过！可以开始游戏了。")
        print("\n运行游戏：python main.py")
    else:
        print("✗ 部分测试失败，请检查上述错误并修复。")
    print("="*60)

    return 0 if all_tests_passed else 1


if __name__ == "__main__":
    sys.exit(main())
