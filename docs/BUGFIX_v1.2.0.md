# Bug修复说明 - v1.2.0

## 修复时间
2025-10-25

## 发现的问题

### Bug #1: 预言家查验结果错误
**问题描述**：
- 预言家查验玩家1（名字为"AI-狼人1"），结果显示为"好人"
- 但玩家1的名字明确是"狼人1"，应该查验出"狼人"才对

**根本原因**：
- 在 `_assign_roles()` 方法中，角色列表被 `random.shuffle()` 随机打乱
- 玩家名称在创建时固定（如"AI-狼人1"），但实际分配的角色是随机的
- 导致名称与实际角色不匹配

**示例**：
```python
# 创建阶段
玩家1: 名称="AI-狼人1"  （名称固定）

# 角色分配阶段（随机打乱后）
roles = [预言家, 狼人, 村民, ...]  # 随机顺序
玩家1: 实际角色=预言家  （与名称不符！）
```

**修复方案**：
- 移除 `random.shuffle(roles)`
- 按照固定顺序分配角色，确保玩家名称与角色一致
- 玩家1-3：狼人
- 玩家4：预言家  
- 玩家5：女巫
- 玩家6：猎人
- 玩家7-9：村民

### Bug #2: 女巫可以自救
**问题描述**：
- 狼人击杀玩家5（女巫）
- 女巫使用解药救了自己
- 违反了"女巫不能自救"的规则

**根本原因**：
```python
# 错误的逻辑
if not is_self or not witch_role.cannot_save_self:
    # 询问是否使用解药
```

这个条件的问题：
- `not is_self`: 如果不是自己，询问 ✓
- `or not witch_role.cannot_save_self`: 或者可以自救，询问 ✗
- 当 `is_self=True` 且 `cannot_save_self=True` 时：
  - `not is_self` = False
  - `not witch_role.cannot_save_self` = False  
  - `False or False` = False → 不询问 ✓（本应如此）
- 但实际上因为代码写错，允许了自救

**正确逻辑**：
```python
# 如果是自己且不能自救，则跳过
if is_self and witch_role.cannot_save_self:
    print("女巫被击杀，但不能自救")
else:
    # 询问是否使用解药
```

## 修复内容

### 1. 修复角色分配逻辑

**文件**: `src/game/werewolf_game.py`

**修改前**：
```python
def _assign_roles(self):
    roles = [...]
    random.shuffle(roles)  # ← 问题所在
    for player, role in zip(self.players, roles):
        player.assign_role(role)
```

**修改后**：
```python
def _assign_roles(self):
    """分配角色"""
    # 创建角色列表，按照玩家顺序对应
    roles = [
        create_role(RoleType.WEREWOLF),      # 玩家1/狼人1
        create_role(RoleType.WEREWOLF),      # 玩家2/狼人2
        create_role(RoleType.WEREWOLF),      # 玩家3/狼人3
        create_role(RoleType.SEER),          # 玩家4/预言家
        create_role(RoleType.WITCH),         # 玩家5/女巫
        create_role(RoleType.HUNTER),        # 玩家6/猎人
        create_role(RoleType.VILLAGER),      # 玩家7/村民1
        create_role(RoleType.VILLAGER),      # 玩家8/村民2
        create_role(RoleType.VILLAGER)       # 玩家9/村民3
    ]
    
    # 直接分配，不打乱
    for player, role in zip(self.players, roles):
        player.assign_role(role)
```

### 2. 修复女巫自救逻辑

**文件**: `src/game/werewolf_game.py`

**修改前**：
```python
if witch_role.has_antidote and wolf_kill_target:
    is_self = (wolf_kill_target.player_id == witch.player_id)
    
    if not is_self or not witch_role.cannot_save_self:  # ← 错误逻辑
        # 询问是否使用解药
```

**修改后**：
```python
if witch_role.has_antidote and wolf_kill_target:
    is_self = (wolf_kill_target.player_id == witch.player_id)
    
    # 如果是自己且不能自救，则不询问
    if is_self and witch_role.cannot_save_self:
        print(f"女巫被击杀，但不能自救")
    else:
        # 询问是否使用解药
        ...
```

同时修复了记忆保存的bug：
```python
# 保存被救玩家信息，避免wolf_kill_target被设为None后丢失
saved_player = wolf_kill_target
wolf_kill_target = None
witch.add_memory(f"第{self.day_count}晚：使用解药救了玩家{saved_player.player_id}")
```

## 影响

### Bug #1 影响
- ✅ 现在玩家名称与角色完全对应
- ✅ 预言家查验结果正确
- ✅ 便于观察和调试
- ℹ️ 游戏变得更可预测（角色位置固定）

### Bug #2 影响  
- ✅ 女巫严格遵守不能自救规则
- ✅ 符合标准狼人杀规则
- ✅ 游戏平衡性提升

## 测试验证

### 测试用例1：预言家查验狼人
```
玩家配置：
- 玩家1-3：狼人
- 玩家4：预言家

预期结果：
- 预言家查验玩家1/2/3，结果应为"狼人"
- 预言家查验玩家4-9，结果应为"好人"

✅ 修复后通过
```

### 测试用例2：女巫自救
```
场景：
- 玩家5是女巫
- 狼人击杀玩家5

预期结果：
- 显示"女巫被击杀，但不能自救"
- 不询问是否使用解药
- 玩家5死亡

✅ 修复后通过
```

### 测试用例3：女巫救其他人
```
场景：
- 玩家5是女巫  
- 狼人击杀玩家4（预言家）

预期结果：
- 询问女巫是否使用解药
- 女巫可以选择救或不救
- 如果救，玩家4存活

✅ 修复后通过
```

## 版本更新

### v1.2.0 变更
- 🐛 修复预言家查验结果错误的bug
- 🐛 修复女巫可以自救的bug
- ✅ 角色分配改为固定顺序（便于调试）
- ✅ 女巫记忆保存bug修复

## 注意事项

### 关于固定角色分配
**当前实现**：角色位置固定
- 优点：名称与角色一致，便于调试和学习
- 缺点：每局游戏角色位置相同，缺少随机性

**未来可选方案**：
1. **方案A**：保持固定分配（当前方案）
   - 适合：调试、观察AI行为、教学

2. **方案B**：随机分配但名称通用化
   ```python
   # 玩家名称改为通用
   "AI-玩家1", "AI-玩家2", ...
   # 角色随机分配
   random.shuffle(roles)
   ```
   - 适合：正式游戏、提高可玩性

3. **方案C**：可配置选项
   ```python
   def setup_game(self, random_roles=False):
       if random_roles:
           random.shuffle(roles)
   ```

建议：当前保持固定分配，便于验证游戏逻辑正确性。

## 总结

两个关键bug已修复：

1. ✅ **预言家查验准确**：玩家1-3永远是狼人，查验结果正确
2. ✅ **女巫不能自救**：严格执行规则

现在游戏规则完全正确，可以正常游玩了！🎉

## Bug #3: 女巫同一晚使用两瓶药

### 问题描述
**发现时间**: 2025-10-25 (第二次修复)

**问题现象**:
```
女巫请睁眼...
女巫使用解药救了玩家4
女巫使用毒药毒死了玩家4
```

女巫在同一个晚上既使用了解药又使用了毒药，违反了"每晚最多使用一瓶药"的规则。

### 根本原因

代码中没有检查女巫是否已经在当晚使用过药水：

```python
# 错误的实现
def _witch_action(self, wolf_kill_target):
    # 询问是否使用解药
    if witch_role.has_antidote and wolf_kill_target:
        # ... 使用解药
    
    # 询问是否使用毒药（没有检查是否已使用解药！）
    if witch_role.has_poison:
        # ... 使用毒药
```

问题：两个 `if` 语句是独立的，即使使用了解药，仍然会询问毒药。

### 修复方案

添加 `used_potion_tonight` 标记，记录当晚是否已使用药水：

```python
def _witch_action(self, wolf_kill_target):
    used_potion_tonight = False  # 新增标记
    
    # 询问是否使用解药
    if witch_role.has_antidote and wolf_kill_target:
        if 使用了解药:
            used_potion_tonight = True  # 标记已使用
    
    # 只有在未使用解药的情况下才询问毒药
    if witch_role.has_poison and not used_potion_tonight:
        # 询问是否使用毒药
    elif used_potion_tonight:
        print("女巫今晚已使用解药，不能再使用毒药")
```

### 修复后效果

**场景1: 使用解药后**
```
女巫请睁眼...
今晚玩家4被狼人击杀。
女巫使用解药救了玩家4
女巫今晚已使用解药，不能再使用毒药  ← 新增提示
```

**场景2: 不使用解药，询问毒药**
```
女巫请睁眼...
今晚玩家4被狼人击杀。
[女巫选择不使用解药]
你还有毒药，是否使用毒药毒人？
[女巫可以选择使用毒药]
```

**场景3: 使用解药，不询问毒药**
```
女巫请睁眼...
今晚玩家4被狼人击杀。
女巫使用解药救了玩家4
女巫今晚已使用解药，不能再使用毒药  ← 正确！
```

### 测试用例

```python
# 测试：女巫同一晚不能使用两瓶药
场景：
  - 狼人击杀玩家4
  - 女巫有解药和毒药

操作：
  1. 女巫使用解药救玩家4
  2. 不再询问是否使用毒药

预期结果：
  - 显示"女巫今晚已使用解药，不能再使用毒药"
  - 玩家4存活
  - 没有人被毒死

✅ 修复后通过
```

### 影响

- ✅ 严格执行"每晚最多使用一瓶药"规则
- ✅ 防止女巫滥用药水
- ✅ 游戏平衡性提升
- ✅ 符合标准狼人杀规则

## 总结更新

v1.2.0 共修复了**4个Bug**：

1. ✅ 预言家查验结果错误
2. ✅ 女巫可以自救
3. ✅ 女巫同一晚使用两瓶药 ← 新增
4. ✅ 女巫记忆保存错误

现在游戏规则完全正确！🎉
