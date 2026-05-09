# 游戏数据结构与算法

本文档详细定义了 `KingdomGame` 的核心数据结构、常量、算法和公式，是实现游戏引擎的基础。

## 1. 游戏常量 (Config)

这些参数应定义在统一的配置文件中，便于调整和平衡。

- `MAP_WIDTH`, `MAP_HEIGHT`: 10, 10 (地图尺寸)
- `NUM_PLAYERS`: 5 (玩家数量)
- `BASE_LIFESPAN`: 5 (兵力的基础寿命，单位：回合)
- `SUPPLY_LIMIT`: 10 (单个格子的后勤容量/舒适容量)
- `CAPITAL_MIN_DISTANCE`: 8 (首都之间需要保持的最小曼哈顿距离)

## 2. 核心数据结构 (Models)

### `Tile` (格子)
- **`owner`**: `Player` 对象或 `None`。表示当前格子的归属。
- **`armies`**: `list[int]`。一个队列（列表），`armies[i]` 代表年龄为 `i` 的兵的数量。例如 `[10, 5, 3, 0, 0]` 表示有10个0岁兵，5个1岁兵，3个2岁兵。列表长度等于 `BASE_LIFESPAN`。
- **`is_capital`**: `bool`。标记此格是否为首都。

### `Player` (玩家)
- **`id`**: `int`。唯一标识符。
- **`name`**: `str`。
- **`color`**: `tuple[int, int, int]`。RGB颜色值。
- **`capital_pos`**: `tuple[int, int]`。首都的 (x, y) 坐标。
- **`is_defeated`**: `bool`。标记玩家是否被淘汰。
- **`agent`**: `BaseAgent` 对象。控制该玩家的智能体。

### `GameState` (游戏状态)
- **`map`**: `list[list[Tile]]`。一个二维列表，构成游戏地图。
- **`players`**: `list[Player]`。游戏中的所有玩家对象。
- **`current_turn`**: `int`。当前的回合数。

## 3. 核心算法与公式

### 3.1. 首都生成算法
1.  对于第一个玩家，随机在地图上选择一个点 `(x, y)` 作为其首都。
2.  对于后续每个玩家：
    a. 随机生成一个候选首都点 `(nx, ny)`。
    b. 计算该点与所有已存在的首都之间的**曼哈顿距离** (`abs(nx-ex) + abs(ny-ey)`)。
    c. 如果**任何一个**已计算的距离小于等于 `CAPITAL_MIN_DISTANCE`，则判定该候选点不合法，返回步骤 a 重新生成。
    d. 如果所有距离都大于 `CAPITAL_MIN_DISTANCE`，则该点合法，设为当前玩家的首都。

### 3.2. 兵力衰老与后勤压力算法 (Attrition)
此过程在每回合的**末尾**结算。
1.  遍历地图上的每一个格子 `tile`。
2.  计算该格子的总兵力 `N = sum(tile.armies)`。
3.  如果 `N > SUPPLY_LIMIT` (后勤容量)，计算衰老速度：
    `aging_speed = 1 + (N - SUPPLY_LIMIT) / SUPPLY_LIMIT`
    如果计算出来是小数，那么向上取整
4.  否则，`aging_speed = 1`。
5.  将 `aging_speed` 存储为一个临时变量，用于本回合的衰老计算。
6.  **更新兵力年龄**：创建一个新的空兵力队列 `new_armies`。从最老的兵（`tile.armies`队尾）开始向前遍历，将他们移动到新的年龄位置。
7.  最后，移除所有年龄大于等于 `BASE_LIFESPAN` 的兵。
8.  在回合开始时，新产出的兵总是加入到年龄为0的位置：`tile.armies[0] += 1`。

### 3.3. 战斗公式 (Combat)
当多个国家的兵力在同一回合进入同一个格子时，触发战斗。
1.  **战斗前结算**：首先结算所有移动，确定每个冲突格子的最终攻击方和防守方。如果一个格子有多个攻击方，他们将作为一个联合力量。
2.  **计算有效兵力**：
    - 攻击方总兵力 `A` = 所有攻击方在该格子的兵力之和。
    - 防守方总兵力 `D` = 防守方在该格子的兵力。
    - `A_effective = ceil(A * random(0.7, 1.0))`
    - `D_effective = ceil(D * random(0.5, 1.0))`
    (`ceil` 为向上取整)
3.  **判定胜负**：
    - 如果 `A_effective > D_effective`，攻击方胜利。
    - 否则，防守方胜利。
4.  **计算损失**：
    - **若攻击方胜**：
        - 攻击方损失 `D_effective` 的兵力（按比例从各个攻击方部队中扣除）。
        - 防守方全灭。
        - 格子归属变更为攻击方（如果是多国联攻，则随机选择一个攻击方或按贡献度分配）。
    - **若防守方胜**：
        - 防守方损失 `A_effective` 的兵力。
        - 攻击方全灭。

## 4. 智能体接口 (Agent Interface)

### `BaseAgent` (抽象基类)
- **`get_actions(self, game_state: GameState, player_id: int) -> dict`**:
  - **输入**: 当前完整的 `game_state` 和该智能体对应的 `player_id`。
  - **输出**: 一个字典，定义了本回合的行军指令。
    - **格式**: `{'<x1>,<y1>': '<direction>', '<x2>,<y2>': '<direction>', ...}`
    - **Key**: 字符串格式的格子坐标，如 `'3,4'`。
    - **Value**: 字符串格式的移动方向，必须是 `up`, `down`, `left`, `right`, `stay` 之一。
  - **约束**: 字典的 Key 必须是该 `player_id` 拥有的所有领土格子。

### `HumanAgent` (人类玩家)
- 其 `get_actions` 方法会与 Pygame 的事件循环交互。
- 游戏会遍历该玩家的所有领土格子，依次高亮。
- 对于每个高亮的格子，等待玩家的键盘输入（`w`, `a`, `s`, `d`, `space`）。
- 收到输入后，记录指令，并高亮下一个格子。
- 支持按 `q` 键撤销上一步操作，回到上一个格子重新输入。
- 当所有格子都获得指令后，返回完整的指令字典。
