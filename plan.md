# 分步骤实现规划：KingdomGame (v2.0)

本文档将游戏升级的开发过程分解为三个阶段，旨在让一个AI编程助手能够理解并逐步完成所有新功能的开发。

---

### **第一阶段：视觉与UI/UX增强**

**目标：** 丰富游戏画面的信息量，提供更直观的视觉反馈。

**步骤：**

1.  **修改数据结构 (`models.py`)**
    *   在 `Tile` 类中增加 `last_turn_battle_size: int = 0` 属性，用于记录战斗规模。
    *   在 `Player` 类中增加 `last_actions: dict = {}` 属性，用于存储上一回合的指令。

2.  **修改游戏引擎 (`engine.py`)**
    *   在 `_apply_attrition` 方法的开始处，添加重置所有格子 `last_turn_battle_size` 为0的逻辑。
    *   在 `_resolve_combat` 方法中，计算战斗双方的总兵力，并将其存入对应格子的 `last_turn_battle_size` 属性。
    *   在 `_get_player_decisions` 之后，将返回的 `all_actions` 存储到对应玩家的 `last_actions` 属性中。

3.  **增强渲染器 (`view.py`)**
    *   **实现颜色深度**：
        *   在 `_draw_tiles` 方法中，对于有归属的格子，根据 `algorithm.md` 中定义的**格子颜色深度算法**计算平均兵力年龄，并调整填充颜色。
    *   **实现大规模战斗高亮**：
        *   在 `_draw_tiles` 方法中，增加一个逻辑：如果一个格子的 `tile.last_turn_battle_size > LARGE_BATTLE_THRESHOLD`，则为其绘制一个红色的边框。
    *   **实现指令箭头绘制**：
        *   创建一个新方法 `_draw_action_arrows(self, actions: dict)`。
        *   此方法接收一个指令字典，遍历其中的坐标和方向，在对应的格子上绘制一个代表方向的小箭头（或三角形）。
        *   在 `get_human_actions` 函数的循环中，每次接收到新指令后，都调用此方法来实时更新屏幕上的箭头。

---

### **第二阶段：新操控模式与高级AI**

**目标：** 增加新的人机交互方式，并创建一个更具挑战性的AI对手。

**步骤：**

1.  **实现新的人类操控模式 (`main.py`)**
    *   在 `config.py` 中添加 `HUMAN_INPUT_MODE` 常量。
    *   重构 `get_human_actions` 函数，使其能够根据 `HUMAN_INPUT_MODE` 的值在两种模式间切换。
    *   **`FREE_ROAM` 模式逻辑**：
        *   决策开始时，高亮首都。
        *   在一个 `while True` 循环中监听键盘事件。
        *   如果按下 `w,a,s,d,space`，则更新当前高亮格子的指令。
        *   如果按下**方向箭头键**，则计算目标坐标，检查其是否属于当前玩家。如果合法，则更新高亮格子的坐标。
        *   如果按下 `Enter`，则跳出循环，决策结束。
        *   在函数返回前，处理**孤岛地块**的逻辑：遍历所有己方领土，找到那些无法从首都到达的格子，并为它们生成随机指令。

2.  **实现指令继承 (`main.py`)**
    *   在 `get_human_actions` 函数的开头，将 `player.last_actions` 深拷贝一份作为本回合指令的初始值。这样，所有格子都会有默认的上回合指令。

3.  **实现 `StrategicAgent` (`agents.py`)**
    *   创建一个新类 `StrategicAgent(BaseAgent)`。
    *   在其 `get_actions` 方法中，完整实现 `algorithm.md` 中为其定义的复杂决策逻辑，包括：
        *   和平扩张逻辑。
        *   首都圈绝对防御逻辑。
        *   常规边境攻防逻辑。
        *   “斩首行动”触发与执行逻辑。
    *   这需要一些辅助函数，如 `find_shortest_path` (可使用A*或BFS算法)。

4.  **更新主函数以使用新AI (`main.py`)**
    *   在 `main` 函数的玩家设置部分，将其中一个AI替换为新的 `StrategicAgent`。

---

### **第三阶段：局域网联机功能**

**目标：** 实现基于WebSockets的C/S架构，让多名玩家可以联机对战。

**步骤：**

1.  **安装依赖**
    *   `pip install websockets`
    *   `pip install asyncio`

2.  **创建服务器 (`server.py`)**
    *   导入 `asyncio`, `websockets`, `pickle`。
    *   初始化 `GameEngine`。
    *   创建一个 `main` 函数作为服务器主入口。
    *   **`handler` 函数 (异步)**：
        *   作为每个客户端连接的处理函数。
        *   在一个全局变量（如列表 `clients`）中注册新的连接。
        *   进入一个循环，等待从客户端接收消息（即指令字典）。
        *   收到指令后，将其存入一个全局的指令缓存中。
    *   **游戏主循环 (异步)**：
        *   在 `main` 函数中，首先等待直到 `len(clients) == NUM_PLAYERS`。
        *   游戏开始后，进入一个 `while not game_over` 循环。
        *   **广播阶段**：将当前的 `GameState` 序列化（`pickle.dumps`）后，遍历 `clients` 列表，发送给所有客户端。
        *   **等待决策**：等待，直到从所有存活的客户端都收到了指令。
        *   **执行回合**：在服务器的 `GameEngine` 上执行收到的所有指令。
        *   循环往复。

3.  **创建客户端 (`client.py`)**
    *   导入 `pygame`, `asyncio`, `websockets`, `pickle`。
    *   客户端的主 `main` 函数现在也必须是异步的。
    *   **`game_loop` 函数 (异步)**：
        *   连接到服务器。
        *   进入一个 `while` 循环。
        *   **接收状态**：`await websocket.recv()`，等待从服务器接收新的 `GameState`，并用 `pickle.loads` 反序列化。
        *   **渲染**：使用 `renderer.draw()` 显示收到的新状态。
        *   **决策**：检查当前轮到的玩家是否是本客户端的玩家。如果是，则调用 `get_human_actions` 或AI的 `get_actions` 来获取指令。
        *   **发送指令**：将获取到的指令字典序列化后，通过 `await websocket.send()` 发送给服务器。
        *   Pygame的事件处理需要被整合进这个异步循环中。

4.  **代码重构**
    *   `main.py` 的大部分逻辑将被迁移到 `client.py` 中。
    *   需要一个简单的方式让玩家在启动 `client.py` 时输入服务器的IP地址。

