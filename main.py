#!/usr/bin/env python3
"""
狼人杀游戏 - 9人局
支持人类玩家与AI混合对战，或纯AI对战
"""

import sys
from src.utils.llm_client import LLMClient
from src.game.werewolf_game import WerewolfGame


def print_welcome():
    """打印欢迎信息"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║              狼人杀游戏 - 9人标准局                      ║
║                                                          ║
║  角色配置：                                              ║
║    - 3名狼人                                             ║
║    - 3名神职（预言家、女巫、猎人）                       ║
║    - 3名村民                                             ║
║                                                          ║
║  胜利条件：                                              ║
║    - 好人胜利：屠杀所有狼人                              ║
║    - 狼人胜利：屠杀所有神职或所有平民                    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)


def get_player_count():
    """获取人类玩家数量"""
    while True:
        try:
            print("\n请选择游戏模式：")
            print("  0 - 纯AI对战（观战模式）")
            print("  1 - 1名人类玩家 + 8名AI")
            print("  2-9 - 自定义人类玩家数量")

            choice = input("\n请输入人类玩家数量 (0-9): ").strip()

            count = int(choice)
            if 0 <= count <= 9:
                return count
            else:
                print("请输入0-9之间的数字！")
        except ValueError:
            print("请输入有效的数字！")


def main():
    """主函数"""
    print_welcome()

    # 获取人类玩家数量
    human_count = get_player_count()

    if human_count == 0:
        print("\n你选择了观战模式，将观看9名AI进行游戏。")
    elif human_count == 1:
        print("\n你将作为1名玩家参与游戏，其余8名为AI。")
    else:
        print(f"\n你选择了{human_count}名人类玩家，其余{9-human_count}名为AI。")

    input("\n按回车键开始游戏...")

    try:
        # 初始化LLM客户端
        print("\n初始化AI系统...")
        llm_client = LLMClient()

        # 创建游戏
        game = WerewolfGame(llm_client)

        # 设置游戏
        game.setup_game(human_player_count=human_count)

        input("\n按回车键开始游戏...")

        # 开始游戏
        game.start_game()

        print("\n感谢游玩！")

    except KeyboardInterrupt:
        print("\n\n游戏被中断。")
        sys.exit(0)
    except Exception as e:
        print(f"\n发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
