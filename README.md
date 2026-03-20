# Meta-Orchestrator: 动态多智能体工作流引擎

## 简介

Meta-Orchestrator 是 OpenCode（或兼容 CLI Agent）的高级多智能体插件。主 Agent 作为「总控大脑 (Meta-Orchestrator)」，通过状态机引擎和虚拟群聊机制，动态设计非线性工作流（支持分叉、循环、条件打回），精准调度系统内的专家级 Subagents 协同作战。

解决单体大模型在长对话中的上下文污染、死循环陷阱和敷衍问题。

## 运行要求

Orchestrator 本身不含领域知识，依赖你系统中注册的专业 Subagent 池。

**推荐配套 Agents：** [agency-agents](https://github.com/msitarzewski/agency-agents)

确保已注册 `Software Architect`、`Frontend Developer`、`Code Reviewer`、`API Tester` 等专家身份。

## 目录结构

```
skills/multi-agent/
├── SKILL.md                    # Skill 主定义（Orchestrator 行为规则）
├── protocols/
│   └── workflow.md             # 子代理通信协议（SOP）
└── scripts/
    └── agent_cli.py            # 状态管理与群聊引擎
```

## 核心架构

### 动态路由委派

Orchestrator 收到需求后：

1. **设计蓝图**：量身定制非线性路线图（如 `architecture → implementation → review`）
2. **专才匹配**：根据当前 Phase 唤醒最匹配的专家（优先使用专业类型，`general` 仅兜底）
3. **自动推进**：子代理完成后立即进入下一阶段，无需用户许可

**预设工作流启发：**
- 规划-实现-审查：`Architect → Coder → Reviewer`（通用编程）
- 测试驱动：`Coder 写测试 → Developer 实现 → Reviewer 审查`（高正确性要求）
- 原型-重构：`Coder 原型 → Reviewer 评估 → Architect 重构`（探索性项目）
- 渐进构建：`Architect 规划 → Coder 分模块实现 → Tester 集成`（多模块项目）

### 通信协议 (`protocols/workflow.md`)

子代理被唤醒后遵循以下 SOP：
- 通过 `agent_cli.py context --diff <role>` 增量读取上下文
- 通过 `agent_cli.py say` 在群聊中沟通阻碍 (Blocker)
- 通过 `agent_cli.py set-phase` 推动状态机流转或打回重做

### Todo 管理

Todo 是跨阶段的独立工作项，每个有明确交付物：
```json
{"id": "T1", "desc": "设计数据结构", "assignee": "Architect", "status": "in_progress"}
```
- 子代理通过 `set-todos` 增量添加/更新，通过 `update-todo` 标记完成
- 不复制阶段名，必须是可交付的具体工作

### 群聊引擎

`.multi_agent_workspace/` 下维护两个文件：
- **`state.json`**：全局目标、Phase、Todos、Sessions、Per-role 读取游标
- **`chat.md`**：所有子代理共享的交流大厅

### 极致省 Token 的冷热启动

| 模式 | 触发条件 | 行为 |
|------|----------|------|
| 冷启动 | `get-session` 返回 `none` | 注入 workflow.md + 任务指令，保存 session_id |
| 热启动 | `get-session` 返回 `ses_xxx` | 仅发极短唤醒词 + `context --diff`，复用原生记忆 |

## CLI 命令参考

```bash
# 初始化工作区
agent_cli.py init "项目目标"

# 群聊
agent_cli.py say <role> "消息内容"

# 上下文读取
agent_cli.py context                          # 默认最近 5 条消息
agent_cli.py context --last 10                # 最近 10 条消息
agent_cli.py context --diff <role>            # 增量读取（更新游标）

# Phase 管理
agent_cli.py set-phase <phase>                # planning / execution / review / completed / discuss

# Todo 管理
agent_cli.py set-todos '[{"id":"T1","desc":"...","assignee":"Coder","status":"pending"}]'
agent_cli.py update-todo T1 done

# 会话管理
agent_cli.py save-session <role_key> <session_id>
agent_cli.py get-session <role_key>

# 游标管理
agent_cli.py reset-cursor <role>
```

## 高级特性

- **非线性打回闭环**：Reviewer 查出漏洞 → 驳回并拉回开发阶段 → Developer 修复 → 循环直到全绿
- **环境自适应**：子代理自行探测环境（如 `nix-shell`）并构造正确启动命令
- **Per-role 游标**：每个角色独立追踪已读位置，实现真正的增量上下文读取
