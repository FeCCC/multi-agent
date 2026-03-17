# Multi-Agent Workflow (Orchestrator)

## 简介
这是一个专为 OpenCode（或兼容的 CLI Agent）打造的多智能体自组织插件。
它通过轻量级的状态机引擎和虚拟群聊（Chatroom），将复杂的开发任务拆解为“规划 (Planning) -> 执行 (Execution) -> 审查 (Review)”的标准化流水线。由相互隔离的子代理 (Subagents) 协作完成，从根本上解决单体大模型在长对话中常见的上下文污染、死循环和“差不多就行”的问题。

## 核心架构

该插件放弃了臃肿的长提示词模式，而是由一个**总控调度器 (Orchestrator)** 居中指挥，并利用原生的 Subagent 机制实现角色的物理隔离。

### 1. 角色分工 (Isolated Subagents)
- **Planner (规划者)**：
  - 职责：将宏观目标拆解为带有明确验收标准的子任务。
  - 限制：绝不编写或修改业务代码。
- **Executor (执行者)**：
  - 职责：认领当前待办任务，编写代码、运行测试。
  - 限制：遇到架构级阻碍时必须挂起讨论，不得硬写烂代码。
- **Reviewer (审查者)**：
  - 职责：代码审计与质量控制。基于运行 `lint` 或 `test` 的证据做出判决。
  - 限制：绝不亲自修改代码，发现问题必须打回并强制 Executor 返工。

### 2. 工作流引擎 (The Engine)
核心引擎由随本包分发的 `agent_cli.py` 驱动，在当前工作目录下维护一个不可见的 `.multi_agent_workspace/`：
- **状态机 (`state.json`)**：记录全局目标、任务队列和当前所处的执行阶段 (Phase)。
- **虚拟群聊 (`chat.md`)**：所有子代理共享的交流大厅。打破信息孤岛，允许 Executor 请求重新规划，或让 Reviewer 留下详尽的驳回指导。

### 3. 高级特性 (Advanced Features)
- **无限调度循环 (Infinite Loop)**：一旦触发，Orchestrator 将自动进行状态判定和路由，无需人类频繁按回车确认，直到项目完成或子代理主动 `@Human` 呼叫援助。
- **环境自适应 (Environment Adaptive)**：子代理被赋予了自行探测环境（如 `nix-shell` 等）并构造正确启动命令的能力，无需死板的包裹脚本。
- **会话持久化与恢复 (Session Continuation)**：Orchestrator 在首次唤醒 Executor 和 Reviewer 时会保存其 `task_id`，并在后续的返工或新任务中**复用该会话**。这不仅保持了子代理的连贯记忆，还极大地节省了全量发送系统提示词带来的 Token 消耗（冷热启动分离）。