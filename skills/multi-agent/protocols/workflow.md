# Orchestrator 工作流协议 (Orchestrator Workflow Protocol)

你当前参与的是一个**多智能体协作项目**。
你的具体工作环节、目标以及所需遵守的规则，已经在唤醒你时由调度器 (Orchestrator) 明确告知。

## 全局协作铁律 (必须遵守)
1. **状态机驱动**：所有的任务流转、状态变更、甚至发起讨论，**必须**通过调用环境内的 `agent_cli.py` 脚本来完成。
2. **环境自适应**：在运行 Python 脚本前，你需要自行探测系统环境（例如 `which python3`，或者在 NixOS 下使用 `nix-shell -p python3 --run`）来构造正确的执行命令。
3. 工具路径提示：状态机脚本通常位于 `~/.config/opencode/skills/agent_cli.py` 或项目目录 `scripts/agent_cli.py`。请使用绝对路径或正确的相对路径调用它。

## 如何开展工作
1. **获取上下文**：每次被唤醒，首先运行 `agent_cli.py context` 查看当前的整体目标、任务状态以及群聊记录 (`chat.md`)。
2. **执行指派任务**：根据 Orchestrator 分配给你的具体环节（如规划、执行、审查、头脑风暴等），发挥你的专业能力完成工作。
3. **遇到阻碍 (Blocker)**：
   - 绝不瞎编乱造或强行通过！
   - 调用 `agent_cli.py say <你的角色名> "@[目标角色] 遇到问题：XXX，需要讨论或重新规划..."`
   - 调用 `agent_cli.py set-phase discuss`，将流程挂起，把控制权交还给调度器。
   - 停止你的回答。
4. **汇报与交接**：
   - 工作完成后，必须通过 `agent_cli.py update-task <task_id> <status>` 更新你负责的任务状态。
   - 在群聊中发言：`agent_cli.py say <你的角色名> "任务 <task_id> 已完成/已审查，结论是..."`
   - **极其重要**：调用 `agent_cli.py set-phase <下一个阶段>` 推动状态机流转。
   - 停止你的回答，等待调度器下一步安排。