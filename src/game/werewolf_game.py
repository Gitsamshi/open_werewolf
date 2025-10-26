import random
from typing import List, Optional, Dict
from src.models.roles import Role, RoleType, Camp, create_role, Witch, Hunter
from src.players.player import Player, HumanPlayer, AIPlayer
from src.utils.llm_client import LLMClient


class WerewolfGame:
    """狼人杀游戏主类"""

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.players: List[Player] = []
        self.day_count = 0
        self.game_over = False
        self.winner = None
        self.last_words_queue: List[Player] = []  # 遗言队列
        self.last_night_first_death: Optional[Player] = None  # 昨晚第一个死亡的玩家（用于确定发言顺序）
        self.last_night_deaths: List[Player] = []  # 昨晚所有死亡的玩家（用于宣布死亡）

        # 警长系统
        self.sheriff: Optional[Player] = None  # 当前警长
        self.sheriff_election_done = False  # 警长竞选是否已完成

    def setup_game(self, human_player_count: int = 0):
        """
        设置游戏

        Args:
            human_player_count: 人类玩家数量（0-9）
        """
        print("\n" + "="*60)
        print("狼人杀游戏 - 9人局")
        print("="*60)

        # 创建玩家
        self._create_players(human_player_count)

        # 分配角色
        self._assign_roles()

        # 显示游戏信息
        self._show_game_info()

    def _create_players(self, human_player_count: int):
        """创建玩家"""
        ai_player_count = 9 - human_player_count

        # 创建人类玩家
        for i in range(human_player_count):
            player = HumanPlayer(i + 1, f"人类玩家{i + 1}")
            self.players.append(player)

        # 创建AI玩家
        # 注意：为了避免信息泄露，玩家名字不能包含身份信息
        role_names = ["狼人1", "狼人2", "狼人3", "预言家", "女巫", "猎人", "村民1", "村民2", "村民3"]
        for i in range(ai_player_count):
            player_id = human_player_count + i + 1
            role_name = role_names[i]
            model_id = self.llm_client.get_model_for_role(role_name)

            player = AIPlayer(
                player_id=player_id,
                name=f"AI-玩家{player_id}",  # 只显示编号，不显示身份
                model_id=model_id,
                llm_client=self.llm_client
            )
            self.players.append(player)

    def _assign_roles(self):
        """分配角色（随机打乱）"""
        # 创建角色列表
        roles = [
            create_role(RoleType.WEREWOLF),      # 狼人1
            create_role(RoleType.WEREWOLF),      # 狼人2
            create_role(RoleType.WEREWOLF),      # 狼人3
            create_role(RoleType.SEER),          # 预言家
            create_role(RoleType.WITCH),         # 女巫
            create_role(RoleType.HUNTER),        # 猎人
            create_role(RoleType.VILLAGER),      # 村民1
            create_role(RoleType.VILLAGER),      # 村民2
            create_role(RoleType.VILLAGER)       # 村民3
        ]

        # 随机打乱角色列表
        random.shuffle(roles)

        # 分配角色给玩家
        for player, role in zip(self.players, roles):
            player.assign_role(role)

    def _show_game_info(self):
        """显示游戏信息"""
        print("\n玩家列表：")
        for player in self.players:
            player_type = "人类" if isinstance(player, HumanPlayer) else "AI"
            print(f"  玩家{player.player_id} - {player.name} ({player_type})")

        # 显示人类玩家的角色
        for player in self.players:
            if isinstance(player, HumanPlayer):
                print(f"\n{'='*60}")
                print(f"你的角色信息：")
                print(f"{'='*60}")
                print(player.role.get_description())
                print(f"\n你的座位号是：{player.player_id}")

                # 如果是狼人，显示队友
                if player.is_werewolf():
                    werewolves = [p for p in self.players if p.is_werewolf()]
                    print("\n你的狼人队友是：")
                    for w in werewolves:
                        if w.player_id != player.player_id:
                            print(f"  玩家{w.player_id} - {w.name}")

    def start_game(self):
        """开始游戏"""
        print("\n" + "="*60)
        print("游戏开始！")
        print("="*60)

        # 游戏主循环
        while not self.game_over:
            self.day_count += 1
            print(f"\n{'#'*60}")
            print(f"第 {self.day_count} 天")
            print(f"{'#'*60}")

            # 夜晚阶段
            self._night_phase()

            # 检查游戏是否结束
            if self._check_game_over():
                break

            # 白天阶段
            self._day_phase()

            # 检查游戏是否结束
            if self._check_game_over():
                break

        # 游戏结束
        self._show_game_result()

    def _night_phase(self):
        """夜晚阶段"""
        print("\n" + "-"*60)
        print("夜晚降临，所有人请闭眼...")
        print("-"*60)

        # 狼人行动
        wolf_kill_target = self._werewolves_action()

        # 预言家行动
        self._seer_action()

        # 女巫行动（返回修改后的wolf_kill_target和poison_target）
        wolf_kill_target, witch_poison_target = self._witch_action(wolf_kill_target)

        # 处理夜晚死亡（分步处理，确保正确的胜负判定）
        self._process_night_deaths_with_victory_check(wolf_kill_target, witch_poison_target)

    def _werewolves_action(self) -> Optional[Player]:
        """狼人行动"""
        print("\n狼人请睁眼...")

        werewolves = [p for p in self.players if p.is_alive and p.is_werewolf()]
        if not werewolves:
            return None

        alive_non_werewolves = [p for p in self.players if p.is_alive and not p.is_werewolf()]
        if not alive_non_werewolves:
            return None

        # 狼人讨论战术
        print(f"\n{'='*60}")
        print(f"🐺 狼人夜间战术讨论（狼人队伍：{', '.join([f'玩家{w.player_id}' for w in werewolves])}）")
        print(f"{'='*60}")
        
        # 第一阶段：每个狼人发表战术建议和目标建议
        wolf_suggestions = {}  # 存储每个狼人的建议
        
        for wolf in werewolves:
            context = {
                "options": [f"玩家{p.player_id}" for p in alive_non_werewolves],
                "werewolves": [f"玩家{w.player_id}" for w in werewolves],
                "alive_players": [f"玩家{p.player_id}" for p in self.players if p.is_alive]
            }

            # 如果只有一个狼人，简化提示
            if len(werewolves) == 1:
                prompt = f"""现在是狼人行动阶段。你是唯一的存活狼人。

存活的非狼人玩家：
{chr(10).join([f'  玩家{p.player_id} - {p.name}' for p in alive_non_werewolves])}

⚠️ 重要：狼人每晚必须击杀一名玩家，请从上述非狼人玩家中选择一名。
请先简要说明你的战术考虑（50字以内），然后给出目标编号（如：战术：优先刀神职。目标：4）："""
            else:
                prompt = f"""现在是狼人行动阶段。
你的狼人队友有：{', '.join([f'玩家{w.player_id}' for w in werewolves if w.player_id != wolf.player_id])}

存活的非狼人玩家：
{chr(10).join([f'  玩家{p.player_id} - {p.name}' for p in alive_non_werewolves])}

⚠️ 重要：狼人每晚必须击杀一名玩家，请从上述非狼人玩家中选择一名。
请先简要说明你的战术考虑（50字以内），然后给出目标编号（如：战术：优先刀神职。目标：4）："""

            decision = wolf.make_decision(prompt, context)
            target = self._parse_player_id(decision, alive_non_werewolves)
            
            wolf_suggestions[wolf.player_id] = {
                "decision": decision,
                "target": target
            }
            
            # 显示每个狼人的讨论
            print(f"\n玩家{wolf.player_id}（狼人）的战术建议：")
            print(f"  {decision}")
            if target:
                print(f"  → 建议击杀：玩家{target.player_id}")
            else:
                print(f"  ⚠️ 未明确目标")

        # 第二阶段：统计投票，决定最终目标
        print(f"\n{'-'*60}")
        print("狼人投票决策：")
        
        vote_count = {}  # 统计每个目标的得票数
        for wolf_id, suggestion in wolf_suggestions.items():
            target = suggestion["target"]
            if target:
                if target.player_id not in vote_count:
                    vote_count[target.player_id] = []
                vote_count[target.player_id].append(wolf_id)
                print(f"  玩家{wolf_id} 投票给 玩家{target.player_id}")
            else:
                print(f"  玩家{wolf_id} 的投票解析失败")
        
        # 选择得票最多的目标
        final_target = None
        if vote_count:
            max_votes = max(len(v) for v in vote_count.values())
            candidates = [pid for pid, voters in vote_count.items() if len(voters) == max_votes]
            
            if len(candidates) > 1:
                print(f"\n  平票！候选目标：{candidates}")
                import random
                chosen_id = random.choice(candidates)
                print(f"  随机选择：玩家{chosen_id}")
                final_target = next(p for p in alive_non_werewolves if p.player_id == chosen_id)
            else:
                final_target = next(p for p in alive_non_werewolves if p.player_id == candidates[0])
        
        # 如果仍然没有有效目标，随机选择（确保狼人必须杀人）
        if not final_target:
            import random
            final_target = random.choice(alive_non_werewolves)
            print(f"\n  ⚠️ 所有狼人都未做出有效选择，随机选择玩家{final_target.player_id}")

        print(f"\n{'='*60}")
        print(f"🎯 最终决策：狼人选择击杀 玩家{final_target.player_id}")
        print(f"{'='*60}")

        # 添加到狼人记忆
        for wolf in werewolves:
            if isinstance(wolf, AIPlayer):
                wolf.add_memory(f"第{self.day_count}晚：狼人击杀了玩家{final_target.player_id}")

        # 如果有多个狼人，继续讨论明天白天的战术
        if len(werewolves) > 1:
            print(f"\n{'-'*60}")
            print(f"🗣️ 狼人继续讨论明天白天的战术...")
            print(f"{'-'*60}")
            
            alive_players_tomorrow = [p for p in self.players if p.is_alive and p.player_id != final_target.player_id]
            
            # 让每个狼人制定明天的战术计划
            for wolf in werewolves:
                context = {
                    "werewolves": [f"玩家{w.player_id}" for w in werewolves],
                    "alive_players": [f"玩家{p.player_id}" for p in alive_players_tomorrow],
                    "day": self.day_count + 1,
                    "target_killed": final_target.player_id
                }
                
                # 计算明天的局势
                alive_wolves_tomorrow = len([w for w in werewolves if w.is_alive])
                alive_goods_tomorrow = len([p for p in alive_players_tomorrow if not p.is_werewolf()])
                
                # 第一天增加上警战术讨论
                sheriff_strategy = ""
                if self.day_count == 0:
                    sheriff_strategy = """
⚠️ 明天是第一天，有警长竞选（上警）！

上警战术要点：
1. **谁应该上警**：
   - 如果有狼计划悍跳预言家，**必须上警**争夺警徽
   - 其他狼可以选择性上警（做倒钩或深水）
   - **不要全狼都上警或都不上警**（容易暴露）
   - 通常1-2名狼上警比较合理
2. **上警后怎么做**：
   - 悍跳狼：竞选发言时假装预言家，报首夜查验
   - 倒钩狼：上警装好人，支持真预言家获取信任
3. **如何协调**：
   - 提前约定谁悍跳、谁深水、谁倒钩
   - 避免多狼同时跳预言家（会自爆）

"""
                
                prompt = f"""你们刚决定今晚击杀玩家{final_target.player_id}。现在讨论明天（第{self.day_count + 1}天）白天的战术。

你的狼人队友有：{', '.join([f'玩家{w.player_id}' for w in werewolves if w.player_id != wolf.player_id])}

明天存活的玩家预计有：{', '.join([f'玩家{p.player_id}' for p in alive_players_tomorrow])}
明天的局势：预计{alive_wolves_tomorrow}狼 vs {alive_goods_tomorrow}好人
{sheriff_strategy}
⚠️ 战术判断：
- 如果明天狼人数量 ≥ 好人数量，可以考虑**狼人冲锋**（不伪装，直接集票推神职）
- 如果明天能一票推掉关键神职直接获胜，就不需要继续伪装了
- 如果局势还需要隐蔽，继续使用伪装战术

请简要制定明天的战术计划（150字以内），包括：
1. {'**上警决策**：你是否上警？为什么？（悍跳/倒钩/深水）' if self.day_count == 0 else '判断明天是否需要狼人冲锋？还是继续伪装？'}
2. 你的伪装策略（悍跳预言家/女巫/猎人？还是装村民？）
3. 如果悍跳神职，你计划给谁发金水/查杀？（可以给狼队友发金水，或查杀好人）
4. 是否配合队友使用狼打狼战术？（狼查杀狼/狼打狼）
5. 你建议明天推哪个玩家？为什么？

请简要说明你的白天战术："""

                decision = wolf.get_speech(prompt, context)
                
                print(f"\n玩家{wolf.player_id}（狼人）的明天战术计划：")
                print(f"  {decision}")
                
                # 将战术讨论添加到所有狼人的记忆（狼人之间共享信息）
                for other_wolf in werewolves:
                    if isinstance(other_wolf, AIPlayer):
                        other_wolf.add_memory(f"第{self.day_count}晚狼队讨论明天战术-玩家{wolf.player_id}：{decision[:150]}")
            
            print(f"\n{'-'*60}")
            print("🌙 狼人战术讨论完毕，闭眼...")
            print(f"{'-'*60}")

        return final_target

    def _seer_action(self):
        """预言家行动"""
        print("\n预言家请睁眼...")

        seers = [p for p in self.players
                if p.is_alive and p.role.get_role_type() == RoleType.SEER]

        if not seers:
            return

        seer = seers[0]
        other_players = [p for p in self.players if p.is_alive and p.player_id != seer.player_id]

        if not other_players:
            return

        context = {
            "options": [f"玩家{p.player_id}" for p in other_players]
        }

        prompt = f"""现在是预言家行动阶段。

存活的其他玩家：
{chr(10).join([f'  玩家{p.player_id} - {p.name}' for p in other_players])}

请选择要查验的玩家（只需回答玩家编号，如：1）："""

        decision = seer.make_decision(prompt, context)
        target = self._parse_player_id(decision, other_players)

        if target:
            is_werewolf = target.is_werewolf()
            result = "狼人" if is_werewolf else "好人"
            print(f"预言家查验玩家{target.player_id}，结果是：{result}")

            # 添加到预言家记忆
            if isinstance(seer, AIPlayer):
                seer.add_memory(f"第{self.day_count}晚：查验玩家{target.player_id}，是{result}")

            if isinstance(seer, HumanPlayer):
                print(f"\n>>> 查验结果：玩家{target.player_id} 是 {result} <<<\n")

    def _witch_action(self, wolf_kill_target: Optional[Player]) -> tuple[Optional[Player], Optional[Player]]:
        """
        女巫行动

        Returns:
            tuple[Optional[Player], Optional[Player]]: (修改后的wolf_kill_target, poison_target)
            - 如果女巫使用解药，wolf_kill_target变为None
            - poison_target是女巫毒死的玩家（如果有）
        """
        print("\n女巫请睁眼...")

        witches = [p for p in self.players
                  if p.is_alive and p.role.get_role_type() == RoleType.WITCH]

        if not witches:
            return wolf_kill_target, None

        witch = witches[0]
        witch_role: Witch = witch.role

        poison_target = None
        used_potion_tonight = False  # 标记今晚是否已使用药水
        knows_kill_target = False  # 标记女巫是否知道刀口信息

        # 询问是否使用解药（只有在有解药且有人被刀时才询问）
        if witch_role.has_antidote and wolf_kill_target:
            # 检查是否是自己
            is_self = (wolf_kill_target.player_id == witch.player_id)

            # 如果是自己且不能自救，则不询问
            if is_self and witch_role.cannot_save_self:
                print(f"女巫被击杀，但不能自救")
                # 女巫被自己刀了但不能自救，不告知具体信息
            else:
                # 只有在询问解药时才告知刀口信息
                knows_kill_target = True
                info = f"今晚玩家{wolf_kill_target.player_id}被狼人击杀。"

                prompt = f"""{info}
你还有解药，是否使用解药救人？（回答：是 或 否）"""

                decision = witch.make_decision(prompt, {})

                if "是" in decision or "yes" in decision.lower():
                    if witch_role.use_antidote():
                        print(f"女巫使用解药救了玩家{wolf_kill_target.player_id}")
                        saved_player = wolf_kill_target  # 保存被救玩家信息
                        wolf_kill_target = None  # 取消击杀
                        used_potion_tonight = True  # 标记已使用药水

                        if isinstance(witch, AIPlayer):
                            witch.add_memory(f"第{self.day_count}晚：使用解药救了玩家{saved_player.player_id}")
                else:
                    # 女巫选择不救，记录她知道了刀口但选择不救
                    if isinstance(witch, AIPlayer):
                        witch.add_memory(f"第{self.day_count}晚：得知玩家{wolf_kill_target.player_id}被刀，选择不用解药")

        # 询问是否使用毒药（只有在今晚未使用解药的情况下才能使用）
        if witch_role.has_poison and not used_potion_tonight:
            other_players = [p for p in self.players
                           if p.is_alive and p.player_id != witch.player_id]

            # 如果女巫不知道刀口信息，则不告诉她
            if knows_kill_target:
                info = f"今晚玩家{wolf_kill_target.player_id}被狼人击杀。"
                prompt = f"""{info}
你还有毒药，是否使用毒药毒人？（回答玩家编号，或回答：否）

存活的其他玩家：
{chr(10).join([f'  玩家{p.player_id} - {p.name}' for p in other_players])}"""
            else:
                # 女巫不知道刀口，不告诉她具体信息
                prompt = f"""你还有毒药，是否使用毒药毒人？（回答玩家编号，或回答：否）
注意：你没有解药了（或选择不查看刀口），所以不知道今晚谁被刀。

存活的其他玩家：
{chr(10).join([f'  玩家{p.player_id} - {p.name}' for p in other_players])}"""

            decision = witch.make_decision(prompt, {"options": [f"玩家{p.player_id}" for p in other_players]})

            if "否" not in decision and "no" not in decision.lower():
                poison_target = self._parse_player_id(decision, other_players)

                if poison_target:
                    if witch_role.use_poison():
                        print(f"女巫使用毒药毒死了玩家{poison_target.player_id}")

                        if isinstance(witch, AIPlayer):
                            witch.add_memory(f"第{self.day_count}晚：使用毒药毒死了玩家{poison_target.player_id}")
        elif used_potion_tonight:
            print("女巫今晚已使用解药，不能再使用毒药")

        return wolf_kill_target, poison_target

    def _process_night_deaths_with_victory_check(self, wolf_kill_target: Optional[Player],
                                                 witch_poison_target: Optional[Player]):
        """处理夜晚死亡（分步检查胜负，确保正确的胜利判定）"""
        deaths = []

        # 第一步：处理狼人击杀
        if wolf_kill_target and wolf_kill_target.is_alive:
            wolf_kill_target.die("wolf_kill")
            deaths.append(wolf_kill_target)

            # 狼刀后立即检查游戏是否结束（狼人优先）
            if self._check_game_over():
                # 游戏已结束，记录死亡信息但不继续处理女巫毒人
                self.last_night_deaths = deaths.copy()
                if deaths:
                    self.last_night_first_death = deaths[0]
                if self.day_count == 0:
                    self.last_words_queue.extend(deaths)
                return

        # 第二步：处理女巫毒人（仅在游戏未结束时）
        if witch_poison_target and witch_poison_target.is_alive:
            witch_poison_target.die("poison")
            deaths.append(witch_poison_target)
            # 猎人被毒死不能开枪
            if witch_poison_target.role.get_role_type() == RoleType.HUNTER:
                hunter_role: Hunter = witch_poison_target.role
                hunter_role.disable_shoot()

        # 保存昨晚所有死亡的玩家（用于宣布死亡）
        self.last_night_deaths = deaths.copy()

        # 记录第一个死亡的玩家（用于确定发言顺序）
        if deaths:
            self.last_night_first_death = deaths[0]
        else:
            self.last_night_first_death = None

        # 遗言规则：只有首夜死亡的玩家才有遗言，第二夜及之后的夜晚死亡没有遗言
        if self.day_count == 0:  # 首夜
            # 首夜死亡的玩家有遗言
            self.last_words_queue.extend(deaths)
        # else: 第二夜及之后的夜晚死亡，不加入遗言队列

    def _process_night_deaths(self, wolf_kill_target: Optional[Player],
                             witch_poison_target: Optional[Player]):
        """处理夜晚死亡（旧版本，保留用于兼容性）"""
        deaths = []

        if wolf_kill_target and wolf_kill_target.is_alive:
            wolf_kill_target.die("wolf_kill")
            deaths.append(wolf_kill_target)

        if witch_poison_target and witch_poison_target.is_alive:
            witch_poison_target.die("poison")
            deaths.append(witch_poison_target)
            # 猎人被毒死不能开枪
            if witch_poison_target.role.get_role_type() == RoleType.HUNTER:
                hunter_role: Hunter = witch_poison_target.role
                hunter_role.disable_shoot()

        # 保存昨晚所有死亡的玩家（用于宣布死亡）
        self.last_night_deaths = deaths.copy()

        # 记录第一个死亡的玩家（用于确定发言顺序）
        if deaths:
            self.last_night_first_death = deaths[0]
        else:
            self.last_night_first_death = None

        # 遗言规则：只有首夜死亡的玩家才有遗言，第二夜及之后的夜晚死亡没有遗言
        if self.day_count == 0:  # 首夜
            # 首夜死亡的玩家有遗言
            self.last_words_queue.extend(deaths)
        # else: 第二夜及之后的夜晚死亡，不加入遗言队列

    def _day_phase(self):
        """白天阶段"""
        print("\n" + "-"*60)
        print("天亮了...")
        print("-"*60)

        # 宣布昨晚死亡信息
        self._announce_deaths()

        # 遗言
        self._last_words()

        # 遗言环节后检查游戏是否结束（猎人可能开枪带走关键玩家）
        if self._check_game_over():
            return

        # 检查是否有足够的活人
        alive_players = [p for p in self.players if p.is_alive]
        if len(alive_players) < 2:
            return

        # 首日白天：警长竞选
        if self.day_count == 1 and not self.sheriff_election_done:
            self._sheriff_election()

        # 发言阶段
        self._speech_phase()

        # 投票放逐
        self._vote_phase()

    def _announce_deaths(self):
        """宣布死亡信息"""
        # 使用保存的昨晚死亡列表
        night_deaths = self.last_night_deaths
        # 有遗言的玩家（在遗言队列中）
        deaths_with_last_words = [p for p in self.last_words_queue]

        if not night_deaths:
            print("\n昨晚是平安夜，没有人死亡。")
        else:
            print(f"\n昨晚死亡的玩家：")
            for player in night_deaths:
                # 判断是否有遗言
                has_last_words = player in deaths_with_last_words
                if has_last_words:
                    print(f"  玩家{player.player_id} - {player.name}")
                else:
                    print(f"  玩家{player.player_id} - {player.name} (无遗言)")

        # 广播给所有AI玩家
        for player in self.players:
            if isinstance(player, AIPlayer) and player.is_alive:
                death_info = "昨晚是平安夜" if not night_deaths else \
                    f"昨晚死亡：{', '.join([f'玩家{p.player_id}' for p in night_deaths])}"
                player.add_memory(f"第{self.day_count}天白天：{death_info}")

    def _last_words(self):
        """遗言环节"""
        while self.last_words_queue:
            player = self.last_words_queue.pop(0)

            print(f"\n玩家{player.player_id}的遗言：")

            context = {"is_last_words": True}

            # 获取存活玩家列表（用于遗言中推荐投票目标）
            alive_players = [p for p in self.players if p.is_alive]
            alive_player_ids = [p.player_id for p in alive_players]

            # 根据角色给出不同的遗言提示
            if player.is_werewolf():
                prompt = f"""⚠️ 你是玩家{player.player_id}，你已经死亡。现在请发表你的遗言。

当前存活的玩家：{', '.join([f'玩家{pid}' for pid in alive_player_ids])}

⚠️ 关键提醒：你是狼人，遗言是为团队服务的最后机会！
- ❌ 绝对不要承认自己是狼人！
- ❌ 绝对不要透露或暗示队友身份！
- ❌ 不要推荐投你自己（你已经死了！）
- ✅ 坚持你之前的伪装身份到底
- ✅ 误导好人，保护队友
- ✅ 制造混乱，为狼队争取胜利机会
- ✅ 推荐投票目标时，只能从存活玩家中选择

请发表遗言（继续扮演你之前的角色）："""
            else:
                prompt = f"""⚠️ 你是玩家{player.player_id}，你已经死亡。现在请发表你的遗言。

当前存活的玩家：{', '.join([f'玩家{pid}' for pid in alive_player_ids])}

你可以：
- 透露你的身份和信息
- 给存活的玩家提供线索
- 表达你的推理和怀疑
- 推荐投票目标（只能从存活玩家中选择）

⚠️ 注意：不要推荐投你自己（你已经死了！）"""

            last_words = player.get_speech(prompt, context)
            print(f"  {last_words}")

            # 广播给所有AI玩家
            for p in self.players:
                if isinstance(p, AIPlayer) and p.is_alive:
                    p.add_memory(f"玩家{player.player_id}遗言：{last_words[:100]}")  # 截取前100字

            # 警徽传递
            if self.sheriff and player.player_id == self.sheriff.player_id:
                self._sheriff_pass_badge(player)

            # 猎人技能
            if player.role.get_role_type() == RoleType.HUNTER:
                hunter_role: Hunter = player.role
                if hunter_role.can_shoot:
                    self._hunter_shoot(player)

                    # 猎人开枪后立即检查游戏是否结束
                    if self._check_game_over():
                        return

    def _hunter_shoot(self, hunter: Player):
        """猎人开枪"""
        print(f"\n猎人玩家{hunter.player_id}可以开枪带走一名玩家！")

        alive_players = [p for p in self.players if p.is_alive]
        if not alive_players:
            return

        context = {"options": [f"玩家{p.player_id}" for p in alive_players]}
        prompt = f"""你是猎人，现在可以开枪带走一名玩家。

存活的玩家：
{chr(10).join([f'  玩家{p.player_id} - {p.name}' for p in alive_players])}

请选择要射击的玩家（只需回答玩家编号，如：1）："""

        decision = hunter.make_decision(prompt, context)
        target = self._parse_player_id(decision, alive_players)

        if target:
            print(f"猎人开枪射击玩家{target.player_id}")
            target.die("shoot")
            # 遗言规则：白天被猎人枪杀的玩家有遗言
            self.last_words_queue.append(target)

            # 广播
            for p in self.players:
                if isinstance(p, AIPlayer) and p.is_alive:
                    p.add_memory(f"猎人玩家{hunter.player_id}开枪带走了玩家{target.player_id}")

    def _speech_phase(self):
        """发言阶段"""
        print("\n" + "-"*60)
        print("发言阶段")
        print("-"*60)

        alive_players = [p for p in self.players if p.is_alive]

        # 确定发言顺序：如果昨晚有人死亡，从死者右边的玩家开始发言
        if self.last_night_first_death:
            # 找到死者在所有玩家中的位置
            death_index = -1
            for i, p in enumerate(self.players):
                if p.player_id == self.last_night_first_death.player_id:
                    death_index = i
                    break

            if death_index != -1:
                # 从死者右边（+1位置）开始，循环到所有玩家
                # 找到第一个存活的玩家作为发言起点
                start_index = (death_index + 1) % len(self.players)
                reordered_players = []

                # 从起点开始遍历，只添加存活的玩家
                for i in range(len(self.players)):
                    current_index = (start_index + i) % len(self.players)
                    player = self.players[current_index]
                    if player.is_alive:
                        reordered_players.append(player)

                alive_players = reordered_players
                print(f"（从玩家{self.last_night_first_death.player_id}的右边开始发言）")

        # 警长归票权：警长最后发言
        if self.sheriff and self.sheriff.is_alive and self.sheriff in alive_players:
            alive_players.remove(self.sheriff)
            alive_players.append(self.sheriff)
            print(f"（警长玩家{self.sheriff.player_id}拥有归票权，将最后发言）")

        for idx, player in enumerate(alive_players):
            print(f"\n玩家{player.player_id}发言：")

            # 计算发言顺序信息
            current_position = idx + 1
            total_alive = len(alive_players)
            players_spoke_before = [p.player_id for p in alive_players[:idx]]
            players_to_speak_after = [p.player_id for p in alive_players[idx+1:]]

            # 构建发言顺序说明
            if players_spoke_before:
                spoke_before_text = f"\n已发言的玩家：{', '.join([f'玩家{pid}' for pid in players_spoke_before])}"
            else:
                spoke_before_text = "\n⚠️ 你是第一个发言的玩家"

            if players_to_speak_after:
                to_speak_after_text = f"\n未发言的玩家：{', '.join([f'玩家{pid}' for pid in players_to_speak_after])}"
            else:
                to_speak_after_text = "\n⚠️ 你是最后一个发言的玩家"

            context = {
                "alive_players": [f"玩家{p.player_id}" for p in alive_players],
                "day": self.day_count,
                "position": current_position,
                "total": total_alive
            }

            prompt = f"""现在是第{self.day_count}天的发言阶段。

存活的玩家：{', '.join([f'玩家{p.player_id}' for p in [p for p in self.players if p.is_alive]])}

⚠️ 发言顺序（你是第{current_position}/{total_alive}位发言）：{spoke_before_text}{to_speak_after_text}

⚠️ 重要：
- 只有在你之前发言的玩家，你才知道他们说了什么
- 在你之后发言的玩家，你不可能知道他们会说什么
- 不要分析或提到还未发言玩家的观点

请发表你的观点：
- 分享你的信息和推理
- 指出你怀疑的对象
- 为自己辩护（如果需要）
- 可以回应之前发言的玩家"""

            speech = player.get_speech(prompt, context)
            print(f"  {speech}")

            # 广播给其他AI玩家
            for p in self.players:
                if isinstance(p, AIPlayer) and p.is_alive and p.player_id != player.player_id:
                    p.add_memory(f"第{self.day_count}天玩家{player.player_id}发言：{speech[:100]}")

    def _vote_phase(self):
        """投票放逐阶段"""
        print("\n" + "-"*60)
        print("投票放逐阶段")
        print("-"*60)

        alive_players = [p for p in self.players if p.is_alive]
        votes: Dict[int, List[int]] = {p.player_id: [] for p in alive_players}

        # 每个玩家独立秘密投票（不知道别人投了谁）
        print("\n所有玩家正在秘密投票...")
        
        for player in alive_players:
            votable_players = [p for p in alive_players if p.player_id != player.player_id]

            # 不使用序号，直接列出玩家编号
            context = {"votable_player_ids": [p.player_id for p in votable_players]}
            prompt = f"""现在是投票阶段。

⚠️ 注意：这是秘密投票，你不知道其他玩家投了谁。

存活的玩家：{', '.join([f'玩家{p.player_id}' for p in alive_players])}
你可以投票的玩家编号：{', '.join([str(p.player_id) for p in votable_players])}

⚠️ 投票策略：
**首要目标**：选择最有利于你的阵营获胜的投票！

**常规情况下保持逻辑一致**：
- 如果你给某人发了金水，通常不能投他（会暴露）
- 如果你给某人发了查杀，通常应该投他
- 如果你质疑某人，投票要一致
- 投票与发言矛盾会暴露身份

**特殊情况可以打破逻辑**：
- ✅ 如果这一票能让你的阵营直接获胜，立刻投！不管逻辑！
- ✅ 狼人冲锋：最后几轮可以直接集票推神职，不用伪装
- ✅ 弃车保帅：自己被怀疑时，可以自爆吸引火力

**判断优先级**：获胜 > 战术需要 > 保持逻辑一致性

请投票放逐一名玩家（直接回答玩家编号）："""

            decision = player.make_decision(prompt, context)
            target = self._parse_player_id(decision, votable_players)

            if target:
                votes[target.player_id].append(player.player_id)
                # 不立即显示投票结果，保持秘密
            else:
                # 投票失败也不立即显示，避免泄露信息
                pass
        
        # 所有人投票完毕后，统一公布结果
        print("\n投票结束，公布结果：")
        for player in alive_players:
            # 显示每个人投给了谁
            voted_for = None
            for target_id, voters in votes.items():
                if player.player_id in voters:
                    voted_for = target_id
                    break
            
            if voted_for:
                print(f"  玩家{player.player_id} 投票给 玩家{voted_for}")
            else:
                print(f"  ⚠️ 玩家{player.player_id} 的投票无效")

        # 统计票数（考虑警长1.5倍投票权）
        print("\n投票结果：")
        vote_counts: Dict[int, float] = {}  # 使用浮点数统计票数

        for player_id, voters in votes.items():
            total_votes = 0.0
            for voter_id in voters:
                # 检查投票者是否是警长
                if self.sheriff and voter_id == self.sheriff.player_id:
                    total_votes += 1.5  # 警长的票算1.5票
                else:
                    total_votes += 1.0
            vote_counts[player_id] = total_votes

            if voters:
                sheriff_marker = ""
                if self.sheriff and self.sheriff.player_id in voters:
                    sheriff_marker = " (包含警长1.5票)"
                print(f"  玩家{player_id}: {total_votes}票{sheriff_marker} (来自 {voters})")

        # 找出得票最多的玩家
        max_votes = max(vote_counts.values()) if vote_counts else 0
        if max_votes == 0:
            print("\n没有人被放逐")
            return

        max_voted_players = [pid for pid, count in vote_counts.items() if count == max_votes]

        if len(max_voted_players) > 1:
            print(f"\n平票！玩家 {max_voted_players} 将进行PK")
            # 简化处理：随机选一个
            exiled_id = random.choice(max_voted_players)
        else:
            exiled_id = max_voted_players[0]

        exiled_player = next(p for p in self.players if p.player_id == exiled_id)
        print(f"\n玩家{exiled_id}被放逐")

        exiled_player.die("vote")
        # 遗言规则：白天被投票出局的玩家有遗言
        self.last_words_queue.append(exiled_player)

        # 广播
        for p in self.players:
            if isinstance(p, AIPlayer) and p.is_alive:
                p.add_memory(f"第{self.day_count}天：玩家{exiled_id}被投票放逐")

        # 处理遗言和猎人技能
        self._last_words()

    def _check_game_over(self) -> bool:
        """检查游戏是否结束"""
        alive_players = [p for p in self.players if p.is_alive]
        alive_werewolves = [p for p in alive_players if p.is_werewolf()]
        alive_villagers = [p for p in alive_players if not p.is_werewolf()]

        # 狼人全部死亡，好人胜利
        if not alive_werewolves:
            self.game_over = True
            self.winner = Camp.VILLAGER
            return True

        # 统计好人中的神职和平民
        alive_gods = [p for p in alive_villagers
                     if p.role.get_role_type() in [RoleType.SEER, RoleType.WITCH, RoleType.HUNTER]]
        alive_villagers_only = [p for p in alive_villagers
                               if p.role.get_role_type() == RoleType.VILLAGER]

        # 神职全部死亡或平民全部死亡，狼人胜利
        if not alive_gods or not alive_villagers_only:
            self.game_over = True
            self.winner = Camp.WEREWOLF
            return True

        return False

    def _sheriff_election(self):
        """警长竞选"""
        print("\n" + "="*60)
        print("警长竞选（上警）")
        print("="*60)

        alive_players = [p for p in self.players if p.is_alive]

        # 第一阶段：询问所有玩家是否要上警
        print("\n请决定是否参与警长竞选...")
        candidates = []
        
        # 随机打乱玩家顺序，增加随机性
        import random
        shuffled_players = alive_players.copy()
        random.shuffle(shuffled_players)

        for player in shuffled_players:
            context = {"is_sheriff_election": True}
            
            # 根据角色给出不同的上警建议
            current_candidates_count = len(candidates)
            current_candidates_info = f"\n当前已有 {current_candidates_count} 人上警。" if current_candidates_count > 0 else "\n目前还没有人上警。"
            
            role_guidance = ""
            if player.role.get_role_type() == RoleType.SEER:
                role_guidance = f"""
⚠️ 你是预言家：
- 建议上警争夺警徽，引导好人阵营
- 警徽可以增加你的发言权重
- 如果已有2-3人上警，可以考虑竞争；如果太多人（5+）上警可能不上"""
            elif player.role.get_role_type() in [RoleType.WITCH, RoleType.HUNTER]:
                role_guidance = f"""
⚠️ 你是神职（女巫/猎人）：
- 可以选择性上警，但要考虑暴露风险
- 如果上警人数较少（0-2人），可以考虑上警
- 如果已有3+人上警，建议不上警保护自己"""
            elif player.role.get_role_type() == RoleType.VILLAGER:
                role_guidance = f"""
⚠️ 你是村民：
- 可以选择性上警，混淆狼人视野
- 如果上警人数少（0-1人），可以考虑上警
- 如果已有3+人上警，建议不上警"""
            elif player.is_werewolf():
                role_guidance = f"""
⚠️ 你是狼人：
- 如果计划悍跳预言家，建议上警争夺警徽
- 如果不悍跳，根据上警人数决定（2-3人上警时可以考虑）
- 注意：狼队友的决策（避免全狼上警或都不上警）"""
            
            prompt = f"""现在是警长竞选阶段。
{current_candidates_info}

⚠️ 警长权利：
- 拥有1.5倍投票权（你的一票相当于1.5票）
- 拥有归票权（最后发言，引导投票方向）
- 死亡时可以选择将警徽传给其他玩家

⚠️ 警长风险：
- 成为狼人优先攻击目标
- 如果是神职，容易暴露身份
- 如果表现不佳，容易被怀疑
{role_guidance}

⚠️ 上警一般原则：
- 神职牌（特别是预言家）优先上警，但要考虑竞争情况
- 狼人如果要悍跳预言家，通常需要上警
- 避免全员上警或全员不上警（容易暴露阵营）
- **通常3-4人上警较为合理，已有5+人上警时建议不上警**
- 根据当前上警人数灵活决策

请问你是否要参与警长竞选（上警）？
请回答：是 或 否"""

            decision = player.make_decision(prompt, context)

            # 解析决策
            decision_lower = decision.strip().lower()
            wants_to_run = any(keyword in decision_lower for keyword in ["是", "yes", "上警", "参与", "竞选"])

            if wants_to_run:
                candidates.append(player)
                print(f"  玩家{player.player_id} 选择上警")
            else:
                print(f"  玩家{player.player_id} 选择不上警")

        if not candidates:
            print("\n没有玩家选择上警，本局无警长。")
            self.sheriff_election_done = True
            return

        if len(candidates) == 1:
            self.sheriff = candidates[0]
            print(f"\n只有玩家{self.sheriff.player_id}上警，自动当选警长！")
            self._announce_sheriff_elected(self.sheriff)
            self.sheriff_election_done = True
            return

        # 第二阶段：竞选发言
        print(f"\n上警玩家：{', '.join([f'玩家{p.player_id}' for p in candidates])}")
        print("\n竞选发言阶段")
        print("-"*60)

        for candidate in candidates:
            print(f"\n玩家{candidate.player_id}竞选发言：")

            context = {"is_sheriff_campaign": True}
            prompt = f"""你已选择上警竞选警长。现在请发表你的竞选发言。

上警的玩家：{', '.join([f'玩家{p.player_id}' for p in candidates])}

竞选发言要点：
- 说明你为什么适合当警长
- 可以暗示或明示自己的身份（例如：我有身份、我是神、我是预言家等）
- 展示你的推理能力和判断
- 获得其他玩家的信任

请发表竞选发言（100-150字）："""

            speech = candidate.get_speech(prompt, context)
            print(f"  {speech}")

            # 广播给其他玩家
            for p in self.players:
                if isinstance(p, AIPlayer) and p.is_alive and p.player_id != candidate.player_id:
                    p.add_memory(f"警长竞选：玩家{candidate.player_id}发言：{speech[:80]}")

        # 第2.5阶段：退水环节（发言后、投票前）
        print("\n" + "-"*60)
        print("退水环节（候选人可以选择退出竞选）")
        print("-"*60)

        withdrawn_candidates = []

        for candidate in candidates:
            context = {"is_withdraw_decision": True}
            
            # 统计当前退水人数
            withdrawn_count = len(withdrawn_candidates)
            withdrawn_info = f"\n目前已有 {withdrawn_count} 人退水。" if withdrawn_count > 0 else "\n目前还没有人退水。"
            
            prompt = f"""竞选发言已结束，现在是退水环节。你可以选择退出警长竞选（退水）。

当前上警玩家：{', '.join([f'玩家{p.player_id}' for p in candidates])}（共{len(candidates)}人）
{withdrawn_info}

⚠️ 退水考虑因素：
- 如果你是真预言家，通常不应该退水
- 如果你是其他神职或村民，根据场上情况决定
- **退水会让你看起来可疑**，除非有充分理由，否则不建议退水
- 如果已有多人退水，更不应该轻易退水

⚠️ 通常情况：大部分候选人不会退水，除非有特殊原因

请问你是否要退水（退出竞选）？
请回答：退水 或 不退"""

            decision = candidate.make_decision(prompt, context)

            # 解析决策
            decision_lower = decision.strip().lower()
            wants_to_withdraw = any(keyword in decision_lower for keyword in ["退水", "退出", "退", "withdraw", "quit"])

            if wants_to_withdraw:
                withdrawn_candidates.append(candidate)
                print(f"  玩家{candidate.player_id} 选择退水")

                # 广播给其他玩家
                for p in self.players:
                    if isinstance(p, AIPlayer) and p.is_alive:
                        p.add_memory(f"警长竞选：玩家{candidate.player_id}退水")
            else:
                print(f"  玩家{candidate.player_id} 不退水")

        # 更新候选人列表（移除退水的玩家）
        candidates = [c for c in candidates if c not in withdrawn_candidates]

        if not candidates:
            print("\n所有候选人都退水了，本局无警长。")
            self.sheriff_election_done = True
            return

        if len(candidates) == 1:
            self.sheriff = candidates[0]
            print(f"\n退水后只剩一名候选人，玩家{self.sheriff.player_id}自动当选警长！")
            self._announce_sheriff_elected(self.sheriff)
            self.sheriff_election_done = True
            return

        print(f"\n退水后剩余候选人：{', '.join([f'玩家{p.player_id}' for p in candidates])}")

        # 第三阶段：投票选举
        print("\n" + "-"*60)
        print("警长投票阶段")
        print("-"*60)

        non_candidates = [p for p in alive_players if p not in candidates]

        if not non_candidates:
            # 所有人都上警，没有警下玩家可以投票 → 警徽流失
            print(f"\n所有玩家都上警，无警下玩家投票，警徽流失！本局无警长。")
            self.sheriff = None
            self.sheriff_election_done = True
            return

        # 未上警的玩家投票
        votes: Dict[int, List[int]] = {p.player_id: [] for p in candidates}

        print("\n未上警的玩家（警下）正在投票...")

        for voter in non_candidates:
            context = {"sheriff_candidates": [p.player_id for p in candidates]}
            prompt = f"""现在进行警长投票。你是警下玩家（未上警），需要投票选出警长。

候选人：{', '.join([f'玩家{p.player_id}' for p in candidates])}

请根据他们的竞选发言，选择你认为最适合担任警长的玩家。

请投票给一名候选人（直接回答玩家编号）："""

            decision = voter.make_decision(prompt, context)
            target = self._parse_player_id(decision, candidates)

            if target:
                votes[target.player_id].append(voter.player_id)

        # 统计票数
        print("\n投票结果：")
        for candidate in candidates:
            voter_ids = votes[candidate.player_id]
            print(f"  玩家{candidate.player_id}: {len(voter_ids)}票")

        # 找出得票最多的候选人
        max_votes = max(len(votes[c.player_id]) for c in candidates)
        winners = [c for c in candidates if len(votes[c.player_id]) == max_votes]

        if len(winners) == 1:
            self.sheriff = winners[0]
        else:
            # 平票，随机选一个
            self.sheriff = random.choice(winners)
            print(f"\n警长选举平票，随机选出警长：玩家{self.sheriff.player_id}")

        self._announce_sheriff_elected(self.sheriff)
        self.sheriff_election_done = True

    def _announce_sheriff_elected(self, sheriff: Player):
        """宣布警长当选"""
        print(f"\n{'='*60}")
        print(f"🎖️ 玩家{sheriff.player_id} 当选警长！")
        print(f"{'='*60}")

        # 广播给所有AI玩家
        for p in self.players:
            if isinstance(p, AIPlayer) and p.is_alive:
                p.add_memory(f"玩家{sheriff.player_id}当选警长")

    def _sheriff_pass_badge(self, dead_sheriff: Player):
        """警长死亡后传递警徽"""
        print(f"\n警长玩家{dead_sheriff.player_id}死亡，可以选择将警徽传递给其他玩家...")

        alive_players = [p for p in self.players if p.is_alive]

        if not alive_players:
            print("没有存活玩家可以继承警徽")
            self.sheriff = None
            return

        context = {"is_sheriff_passing": True}
        prompt = f"""⚠️ 你是警长，你已经死亡。现在你可以选择将警徽传递给一名存活的玩家。

存活的玩家：{', '.join([f'玩家{p.player_id}' for p in alive_players])}

⚠️ 警徽传递策略：
- 如果你是好人阵营，传给你认为最可信的好人或神职
- 如果你是狼人阵营，传给你的狼队友或伪装好的队友
- 也可以选择不传（撕毁警徽），回答"不传"或"撕掉"

请选择继承警徽的玩家（直接回答玩家编号，或"不传"）："""

        decision = dead_sheriff.make_decision(prompt, context)

        # 解析决策
        decision_lower = decision.strip().lower()
        if any(keyword in decision_lower for keyword in ["不传", "撕掉", "撕毁", "no", "none", "撕"]):
            print(f"\n警长选择撕毁警徽，本局不再有警长")
            self.sheriff = None

            # 广播
            for p in self.players:
                if isinstance(p, AIPlayer) and p.is_alive:
                    p.add_memory(f"警长玩家{dead_sheriff.player_id}撕毁警徽")
        else:
            target = self._parse_player_id(decision, alive_players)

            if target:
                self.sheriff = target
                print(f"\n{'='*60}")
                print(f"🎖️ 警徽传递给玩家{target.player_id}！")
                print(f"{'='*60}")

                # 广播
                for p in self.players:
                    if isinstance(p, AIPlayer) and p.is_alive:
                        p.add_memory(f"警徽从玩家{dead_sheriff.player_id}传递给玩家{target.player_id}")
            else:
                print(f"\n警长未做出有效选择，警徽撕毁")
                self.sheriff = None

    def _show_game_result(self):
        """显示游戏结果"""
        print("\n" + "="*60)
        print("游戏结束！")
        print("="*60)

        if self.winner == Camp.VILLAGER:
            print("\n好人阵营获胜！")
        elif self.winner == Camp.WEREWOLF:
            print("\n狼人阵营获胜！")

        print("\n角色揭示：")
        for player in self.players:
            status = "存活" if player.is_alive else f"死亡({player.death_reason})"
            print(f"  玩家{player.player_id} - {player.name}: {player.role.get_role_type().value} [{status}]")

    def _parse_player_id(self, text: str, valid_players: List[Player]) -> Optional[Player]:
        """从文本中解析玩家ID"""
        import re
        
        # 清理文本（转小写，去除多余空格）
        text = text.strip().lower()
        
        # 策略1：提取所有数字，尝试每一个
        numbers = re.findall(r'\d+', text)
        
        for num_str in numbers:
            try:
                player_id = int(num_str)
                for player in valid_players:
                    if player.player_id == player_id:
                        return player
            except ValueError:
                continue
        
        # 策略2：尝试匹配中文数字
        chinese_nums = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9
        }
        for chinese, num in chinese_nums.items():
            if chinese in text:
                for player in valid_players:
                    if player.player_id == num:
                        return player
        
        return None
