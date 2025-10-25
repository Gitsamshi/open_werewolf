from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional


class Camp(Enum):
    """阵营类型"""
    WEREWOLF = "狼人阵营"
    VILLAGER = "好人阵营"


class RoleType(Enum):
    """角色类型"""
    WEREWOLF = "狼人"
    SEER = "预言家"
    WITCH = "女巫"
    HUNTER = "猎人"
    VILLAGER = "村民"


class Role(ABC):
    """角色基类"""

    def __init__(self, role_type: RoleType, camp: Camp):
        self.role_type = role_type
        self.camp = camp

    @abstractmethod
    def get_description(self) -> str:
        """获取角色描述"""
        pass

    def get_camp(self) -> Camp:
        """获取阵营"""
        return self.camp

    def get_role_type(self) -> RoleType:
        """获取角色类型"""
        return self.role_type

    def __str__(self):
        return self.role_type.value


class Werewolf(Role):
    """狼人角色"""

    def __init__(self):
        super().__init__(RoleType.WEREWOLF, Camp.WEREWOLF)

    def get_description(self) -> str:
        return """你是狼人！
技能：
- 每晚可以和其他狼人讨论并集体决定杀死1名玩家
- 你认识所有狼人队友
- 胜利条件：屠杀所有神职或所有平民"""


class Seer(Role):
    """预言家角色"""

    def __init__(self):
        super().__init__(RoleType.SEER, Camp.VILLAGER)

    def get_description(self) -> str:
        return """你是预言家！
技能：
- 每晚可以查验1名玩家的身份（好人/狼人）
- 需要在白天引导好人阵营找出狼人
- 胜利条件：找出并放逐所有狼人"""


class Witch(Role):
    """女巫角色"""

    def __init__(self):
        super().__init__(RoleType.WITCH, Camp.VILLAGER)
        self.has_antidote = True  # 解药
        self.has_poison = True    # 毒药
        self.cannot_save_self = True  # 不能自救

    def get_description(self) -> str:
        return """你是女巫！
技能：
- 拥有解药1瓶（救活当晚被杀的人）
- 拥有毒药1瓶（毒死1名玩家）
- 每晚最多使用1瓶药，同一晚不能同时使用两瓶
- 不能自救
- 胜利条件：找出并放逐所有狼人"""

    def use_antidote(self) -> bool:
        """使用解药"""
        if self.has_antidote:
            self.has_antidote = False
            return True
        return False

    def use_poison(self) -> bool:
        """使用毒药"""
        if self.has_poison:
            self.has_poison = False
            return True
        return False


class Hunter(Role):
    """猎人角色"""

    def __init__(self):
        super().__init__(RoleType.HUNTER, Camp.VILLAGER)
        self.can_shoot = True

    def get_description(self) -> str:
        return """你是猎人！
技能：
- 被狼人杀死或被投票放逐时，可以开枪带走1名玩家
- 被女巫毒死不能开枪
- 胜利条件：找出并放逐所有狼人"""

    def disable_shoot(self):
        """禁用开枪（被女巫毒死时）"""
        self.can_shoot = False


class Villager(Role):
    """村民角色"""

    def __init__(self):
        super().__init__(RoleType.VILLAGER, Camp.VILLAGER)

    def get_description(self) -> str:
        return """你是村民！
技能：
- 无特殊技能
- 通过逻辑推理和投票找出狼人
- 胜利条件：找出并放逐所有狼人"""


def create_role(role_type: RoleType) -> Role:
    """创建角色实例的工厂方法"""
    role_mapping = {
        RoleType.WEREWOLF: Werewolf,
        RoleType.SEER: Seer,
        RoleType.WITCH: Witch,
        RoleType.HUNTER: Hunter,
        RoleType.VILLAGER: Villager
    }
    return role_mapping[role_type]()
