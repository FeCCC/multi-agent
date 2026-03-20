# Orchestrator 工作流协议 (Orchestrator Workflow Protocol)

你当前参与的是一个**多智能体协作项目**。
你的具体工作环节、目标以及所需遵守的规则，已经在唤醒你时由调度器 (Orchestrator) 明确告知。

## 全局协作铁律 (必须遵守)
1. **状态机驱动**：所有的任务流转、状态变更、甚至发起讨论，**必须**通过调用环境内的 `agent_cli.py` 脚本来完成。
2. **环境自适应**：在运行 Python 脚本前，你需要自行探测系统环境（例如 `which python3`，或者在 NixOS 下使用 `nix-shell -p python3 --run`）来构造正确的执行命令。
3. 工具路径提示：状态机脚本通常位于 `~/.config/opencode/skills/agent_cli.py` 或项目目录 `scripts/agent_cli.py`。请使用绝对路径或正确的相对路径调用它。

## Todo List 规则
- 每个子代理被唤醒后，应使用 `agent_cli.py set-todos` 增量添加或更新自己负责的 todo 项。
- todo 格式：`{"id": "T{n}", "desc": "具体交付物", "assignee": "{role}", "status": "pending|in_progress|done"}`
- 不要复制阶段名作为 todo，应是可交付的具体工作（如"设计 cuckoo_slot_t 数据结构"）。
- 开始工作时将 status 设为 `in_progress`，完成后设为 `done`。

## 如何开展工作
1. **获取上下文**：每次被唤醒，首先运行 `agent_cli.py context --diff <你的角色名>` 查看自上次以来的最新群聊动态和 todo 状态。
2. **添加/更新 Todo**：根据你的职责，使用 `agent_cli.py set-todos` 添加或更新你负责的 todo 项，status 设为 `in_progress`。
3. **执行指派任务**：根据 Orchestrator 分配给你的具体环节（如规划、执行、审查等），发挥你的专业能力完成工作。
4. **遇到阻碍 (Blocker)**：
   - 绝不瞎编乱造或强行通过！
   - 调用 `agent_cli.py say <你的角色名> "@[目标角色] 遇到问题：XXX，需要讨论或重新规划..."`
   - 调用 `agent_cli.py set-phase discuss`，将流程挂起，把控制权交还给调度器。
   - 停止你的回答。
5. **汇报与交接**：
   - 工作完成后，必须通过 `agent_cli.py update-todo <todo_id> done` 更新你负责的 todo 状态。
   - 在群聊中发言：`agent_cli.py say <你的角色名> "任务 <todo_id> 已完成/已审查，结论是..."`
   - **极其重要**：调用 `agent_cli.py set-phase <下一个阶段>` 推动状态机流转。
   - 停止你的回答，等待调度器下一步安排。

## 职责边界
- 只在自己职责范围内工作，不做其他角色该做的事。
- 遇到职责外的问题，在群聊中说明，等待 Orchestrator 安排合适的角色处理。
