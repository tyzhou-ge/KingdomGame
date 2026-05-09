# 分步骤实现规划：KingdomGame

本文档将整个游戏的开发过程分解为四个清晰的、循序渐进的阶段。每个阶段都有明确的目标和可交付的成果，旨在让一个AI编程助手能够理解并逐步完成开发。

---

### **第一阶段：核心引擎与数据结构 (无图形界面)**

**目标：** 搭建游戏的核心逻辑，使其可以在后台独立运行和测试。这是整个项目最关键的地基。

**步骤：**

1.  **环境搭建**
    *   确保已安装 Python。
    *   通过 `pip install pygame` 安装 Pygame 库。

2.  **创建项目结构**
    *   创建主文件夹 `KingdomGame`。
    *   在其中创建 `src` 文件夹用于存放源代码。
    *   在 `src` 中创建以下文件：
        *   `config.py`: 用于存放 `algorithm.md` 中定义的所有游戏常量。
        *   `models.py`: 用于定义 `Tile`, `Player`, `GameState` 等核心数据类。
        *   `engine.py`: 用于实现游戏主循环和所有核心逻辑。
        *   `agents.py`: 用于定义智能体基类和各种AI实现。
        *   `main_text.py`: 作为本阶段的测试入口。

3.  **实现核心数据结构 (`models.py`)**
    *   根据 `algorithm.md` 中的定义，完整实现 `Tile`, `Player`, 和 `GameState` 类。
    *   `Tile` 类中的 `armies` 属性使用列表（List）作为队列实现。

4.  **实现游戏引擎 (`engine.py`)**
    *   创建 `GameEngine` 类。
    *   **`__init__`**:
        *   初始化 `GameState`。
        *   实现 `algorithm.md` 中定义的**首都生成算法**，为5个玩家分配首都和初始领土。
    *   **`run_turn()`**: 实现一个完整游戏回合的逻辑。此方法将按顺序调用以下私有方法：
        1.  `_generate_resources()`: 在每个玩家的领土上产出新兵。
        2.  `_get_player_decisions()`: 从每个玩家的 `agent` 获取决策指令字典。
        3.  `_execute_moves()`: 根据指令，计算所有兵力的最终目的地。
        4.  `_resolve_combats()`: 在发生冲突的格子上，调用**战斗公式**进行结算。
        5.  `_apply_attrition()`: 调用**兵力衰老与后勤压力算法**，更新所有兵力的年龄并移除到期单位。
        6.  `_check_game_over()`: 检查是否有首都易主，更新玩家失败状态，并判断游戏是否结束。

5.  **实现基础智能体 (`agents.py`)**
    *   定义一个抽象基类 `BaseAgent`，包含一个抽象方法 `get_actions(self, game_state, player_id)`，其返回类型必须是 `algorithm.md` 中定义的指令字典。
    *   实现一个 `RandomAgent(BaseAgent)`，它会为自己控制的每个格子随机选择一个合法的移动方向（up, down, left, right, stay）。

6.  **创建文本测试入口 (`main_text.py`)**
    *   创建一个主函数。
    *   初始化 `GameEngine`，并为5个玩家分配 `RandomAgent`。
    *   进入一个 `while` 循环，只要游戏没有结束，就持续调用 `engine.run_turn()`。
    *   在每回合结束后，从 `engine.game_state` 中读取地图数据，并在**终端**中打印出地图的势力归属和每个格子的总兵力。
    *   **此阶段完成的标志**：能够成功运行 `main_text.py`，并在终端看到回合数、势力范围和兵力随着游戏的进行而动态变化。

---

### **第二阶段：Pygame基础可视化**

**目标：** 将游戏状态用图形化方式渲染出来，实现动态沙盘的可视化。

**步骤：**

1.  **创建视图模块 (`view.py`)**
    *   创建 `Renderer` 类。
    *   在 `config.py` 中定义5个玩家的柔和色系RGB值，以及金色、背景色等。
    *   **`__init__`**: 初始化 Pygame 窗口、字体等。
    *   **`draw(self, game_state)`**: 主渲染函数，它会调用以下方法：
        *   `_draw_grid()`: 绘制地图网格线。
        *   `_draw_tiles(game_state)`: 遍历所有格子，根据 `tile.owner` 填充背景色，并根据 `tile.is_capital` 绘制金色边框。
        *   `_draw_armies(game_state)`: 在每个格子上渲染总兵力数字。
        *   `_draw_ui(game_state)`: 在屏幕边缘显示当前回合数等信息。

2.  **创建Pygame主入口 (`main.py`)**
    *   这是新的主程序入口。
    *   初始化 Pygame, `GameEngine`, 和 `Renderer`。
    *   创建一个主 `while` 循环，处理 Pygame 事件（如 `QUIT`）。
    *   在循环中：
        *   调用 `engine.run_turn()` 推进一回合游戏逻辑。
        *   调用 `renderer.draw(engine.game_state)` 将最新状态绘制到屏幕。
        *   调用 `pygame.display.flip()` 更新屏幕。
        *   使用 `pygame.time.Clock().tick(1)` 来控制游戏速度，例如每秒1回合。

*   **此阶段完成的标志**：运行 `main.py`，可以看到一个图形化窗口，其中地图的颜色和兵力数字随着时间自动变化。

---

### **第三阶段：交互与更复杂的智能体**

**目标：** 让游戏变得可以由人类玩，并提升AI的挑战性。

**步骤：**

1.  **实现人类智能体 (`agents.py`)**
    *   创建 `HumanAgent(BaseAgent)`。
    *   其 `get_actions` 方法将与主循环的事件处理部分交互。它需要一个机制来接收来自主循环的键盘输入。

2.  **修改主循环以支持人类玩家 (`main.py`)**
    *   在主 `while` 循环中，当轮到人类玩家决策时，暂停自动回合推进。
    *   实现 `algorithm.md` 中定义的**人类交互流程**：
        *   按顺序遍历人类玩家的领土，在 `Renderer` 中实现一个 `highlight_tile` 方法来高亮当前等待指令的格子。
        *   监听键盘事件 (`KEYDOWN`)。如果按下 `w, a, s, d, space`，则记录指令并高亮下一个格子。
        *   如果按下 `q`，则回退到上一个格子。
        *   当所有格子都获得指令后，将完整的指令字典发送给 `HumanAgent`，然后恢复自动回合推进。

3.  **实现更高级的AI (`agents.py`)**
    *   创建 `GreedyAgent(BaseAgent)`: 优先攻击能打得过的最弱的敌人。
    *   创建 `DefensiveAgent(BaseAgent)`: 优先将兵力调往与敌人接壤的前线或首都附近。

*   **此阶段完成的标志**：可以启动一场包含人类玩家和不同AI的对局，并能通过键盘完成操作。

---

### **第四阶段：打磨与扩展**

**目标：** 优化游戏体验，并探索更前沿的AI实现。

**步骤：**

1.  **优化UI/UX (`view.py`)**
    *   在界面上增加一个永久的信息面板，显示各玩家的领土数、总兵力等排名信息。
    *   为兵力移动添加简单的过渡动画（例如，一个代表兵团的小圆点从一个格子移动到另一个格子）。

2.  **实现LLM智能体 (可选，`agents.py`)**
    *   创建 `LLMAgent(BaseAgent)`。
    *   其 `get_actions` 方法需要：
        1.  实现一个 `_serialize_state(game_state, player_id)` 方法，将游戏状态转换成对LLM友好的JSON或文本格式。
        2.  设计一个优秀的Prompt模板，包含规则、当前状态和期望的输出格式。
        3.  使用 `requests` 或相关库调用一个外部LLM的API。
        4.  编写健壮的解析逻辑，处理LLM可能返回的非标准格式，并将其转换为游戏指令字典。

3.  **平衡性调整 (`config.py`)**
    *   通过大量的人机和AI对战，反复微调 `BASE_LIFESPAN`, `SUPPLY_LIMIT`, 战斗随机因子等参数，以达到最佳游戏体验。

*   **最终成果**：一个功能完整、可玩性强、具有良好可视化效果，并支持多种AI对手的策略战棋游戏。
