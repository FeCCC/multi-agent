# Meta-Orchestrator: 动态多智能体工作流引擎

## 简介
这是一个专为 OpenCode（或兼容的 CLI Agent）打造的高级多智能体自组织插件。
它提供了一种非线性的工作流机制，将主 Agent 作为一个**“总控大脑 (Meta-Orchestrator)”**。通过轻量级的状态机引擎和虚拟群聊（Chatroom），Orchestrator 会根据每个任务的复杂度和特性，**动态设计工作流（包含分叉、循环、条件打回）**，并精准拉起系统内建的各种专家级 Subagents（如架构师、前端专家、安全工程师等）协同作战。

该引擎从根本上解决了单体大模型在长对话中常见的上下文污染、死循环陷阱以及“差不多就行”的敷衍态度。

## 运行要求 (Prerequisites)

为了让 Orchestrator 能够“调兵遣将”，你的 OpenCode 系统中**必须安装各种专业的 Agents**。Orchestrator 本身不包含任何具体的领域知识，它依赖于你提供的专业子代理池。

**推荐配套使用的 Agents 项目集合：**
👉 [https://github.com/msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents)

（请确保你的系统中已经注册了类似 `Software Architect`, `Frontend Developer`, `Code Reviewer`, `API Tester` 等专家级代理身份）。

## 核心架构

### 1. 动态路由委派 (Dynamic Delegation)
当拿到用户需求后，Orchestrator 会执行以下路由策略：
1. **设计蓝图**：在脑海中绘制出诸如 `test_generation (TDD驱动) -> concurrent_dev (并发开发) -> security_audit (安全审计)` 的定制化路线图。
2. **专才匹配**：检查当前所处的自定义阶段，唤醒最匹配的内置专家。前端写界面，DBA 写 SQL，审查员查内存。

### 2. 纯粹的通信协议 (`protocols/workflow.md`)
被唤醒的专家 Subagent 会收到一份极简的 SOP 协议。协议不干涉它们的专业技能，只规定：
- 必须通过 `agent_cli.py context` 读取任务和群聊。
- 必须通过 `agent_cli.py say` 沟通阻碍 (Blocker)。
- 必须通过 `agent_cli.py set-phase` 和 `update-task` 推动状态机流转或打回重做。

### 3. 工作流引擎 (The Engine)
核心引擎由随本包分发的 `agent_cli.py` 驱动，在当前工作目录下维护一个不可见的 `.multi_agent_workspace/`：
- **状态机 (`state.json`)**：记录全局目标、任务队列和当前所处的执行阶段 (Phase)。
- **虚拟群聊 (`chat.md`)**：所有子代理共享的交流大厅，打破隔离导致的“信息孤岛”。

### 4. 高级特性 (Advanced Features)
- **非线性打回闭环 (Non-linear Rejection Loop)**：当 Reviewer 查出代码漏洞时，可以直接通过脚本驳回并强行将状态机拉回开发阶段，迫使 Developer 重新拉起修复，直到审计全绿。
- **极致 Token 节约的冷热启动 (Session Continuation)**：
  - **冷启动**：挑选专家 -> 注入通信协议与任务 -> 获取并保存专家的 `session_id`。
  - **热启动**：若流程打回给该专家，仅需发送极简唤醒词（"Wake up"），带上保存的 `session_id` 即可恢复其原生记忆，无需重发庞大上下文。
- **环境自适应 (Environment Adaptive)**：子代理被赋予了自行探测环境（如检测 `nix-shell` 等）并构造正确启动命令的能力，无需死板的包裹脚本。