#!/usr/bin/env python3
"""
Multi-Agent Workflow 状态管理与群聊引擎
管理 .multi_agent_workspace/ 下的 state.json 和 chat.md。
支持子代理会话恢复 (Session Continuation) 和通用交流。
支持按消息条数截取群聊 (而非按行)。
支持 per-role 读取游标，实现增量上下文读取。
"""
import os
import re
import json
import argparse
from datetime import datetime

WORKSPACE = ".multi_agent_workspace"
STATE_FILE = os.path.join(WORKSPACE, "state.json")
CHAT_FILE = os.path.join(WORKSPACE, "chat.md")

# ---- 消息解析 ----

_MSG_RE = re.compile(r'^\*\*\[(.+?)\*\*\s*\((\d{2}:\d{2}:\d{2})\):\s*(.*)$', re.MULTILINE)

def _parse_messages():
    """解析 chat.md，返回 [{role, time, content, raw}] 列表。content 可能包含多行。"""
    if not os.path.exists(CHAT_FILE):
        return []
    with open(CHAT_FILE, 'r', encoding='utf-8') as f:
        text = f.read()

    messages = []
    # 找到所有消息头的位置
    heads = list(_MSG_RE.finditer(text))
    for i, m in enumerate(heads):
        role = m.group(1).rstrip(']')
        time = m.group(2)
        first_content = m.group(3)
        start = m.end()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        rest = text[start:end].strip('\n')
        if rest:
            content = first_content + '\n' + rest if first_content else rest
        else:
            content = first_content
        messages.append({
            'role': role,
            'time': time,
            'content': content,
        })
    return messages


def _render_messages(messages):
    """将消息列表渲染为可读文本"""
    parts = []
    for m in messages:
        parts.append(f"**[{m['role']}]** ({m['time']}): {m['content']}")
    return '\n'.join(parts)


# ---- 游标管理 ----

def _get_cursor(role):
    """获取某个 role 的读取游标（最后一条已读消息的时间戳）"""
    state = _load_state()
    if not state:
        return None
    return state.get('read_cursors', {}).get(role)


def _update_cursor(role, timestamp):
    """更新某个 role 的读取游标"""
    state = _load_state()
    if not state:
        return
    if 'read_cursors' not in state:
        state['read_cursors'] = {}
    state['read_cursors'][role] = timestamp
    _save_state(state)


def _find_cursor_index(messages, cursor_timestamp):
    """找到游标对应的消息索引，返回 -1 表示未找到"""
    if not cursor_timestamp:
        return -1
    for i in range(len(messages) - 1, -1, -1):
        if messages[i]['time'] == cursor_timestamp:
            return i
    return -1


# ---- 状态读写 ----

def _load_state():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ---- 核心命令 ----

def init_workspace(goal: str):
    os.makedirs(WORKSPACE, exist_ok=True)
    state = {
        "global_goal": goal,
        "phase": "planning",
        "todos": [],
        "sessions": {},
        "read_cursors": {}
    }
    _save_state(state)

    with open(CHAT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# Multi-Agent 群聊记录\n\n**[System]**: 总体目标已确立 -> {goal}\n")

    print(f"✅ 工作区已初始化。目标: {goal}")


def say(role: str, message: str):
    """在群聊中发言"""
    if not os.path.exists(CHAT_FILE):
        print("❌ 错误：工作区未初始化")
        return
    time_str = datetime.now().strftime("%H:%M:%S")
    formatted_msg = f"\n**[{role.upper()}]** ({time_str}): {message}\n"
    with open(CHAT_FILE, 'a', encoding='utf-8') as f:
        f.write(formatted_msg)
    print(f"✅ 消息已发送至群聊。")


def get_context(last=None, diff_role=None):
    """供各个角色唤醒时读取当前上下文。

    --last N:   显示最近 N 条消息（按消息条数），默认 5，不更新游标。
    --diff ROLE: 显示该 role 上次游标处 ~ 最新消息（至少 1 条），并更新游标。
    """
    state = _load_state()
    if not state:
        print("STATUS: uninitialized")
        return

    # 兼容旧状态文件缺少 read_cursors 的情况
    if 'read_cursors' not in state:
        state['read_cursors'] = {}
        _save_state(state)

    print("=== CURRENT STATE ===")
    print(f"Phase: {state['phase']}")
    print(f"Goal: {state['global_goal']}")

    print("\n=== TODOS ===")
    if not state["todos"]:
        print("(No todos yet)")
    for t in state["todos"]:
        desc = t.get('desc', '(no description)')
        print(f"[{t['status']}] {t['id']}: {desc}")

    messages = _parse_messages()
    if not messages:
        print("\n=== CHAT ===\n(No messages yet)")
        return

    if diff_role:
        # 增量模式：从游标位置开始，至少显示 1 条
        cursor_ts = _get_cursor(diff_role)
        if cursor_ts:
            idx = _find_cursor_index(messages, cursor_ts)
            if idx >= 0:
                # 从游标那条开始（包含），显示到最新
                shown = messages[idx:]
            else:
                # 游标消息没找到（可能被截断了），显示最后 5 条
                shown = messages[-5:]
        else:
            # 没有游标，显示最后 5 条
            shown = messages[-5:]

        print(f"\n=== CHAT (diff for {diff_role}, {len(shown)} msgs) ===")
        print(_render_messages(shown))

        # 更新游标到最新消息
        _update_cursor(diff_role, messages[-1]['time'])

    elif last is not None:
        # 指定条数模式
        shown = messages[-last:]
        print(f"\n=== CHAT (last {len(shown)} msgs) ===")
        print(_render_messages(shown))
    else:
        # 默认：最近 5 条消息
        shown = messages[-5:]
        print(f"\n=== CHAT (last {len(shown)} msgs) ===")
        print(_render_messages(shown))


def reset_cursor(role: str):
    """重置某个 role 的读取游标"""
    state = _load_state()
    if not state:
        print("❌ 错误：工作区未初始化")
        return
    if 'read_cursors' in state and role in state['read_cursors']:
        del state['read_cursors'][role]
        _save_state(state)
        print(f"✅ 已重置 {role} 的读取游标。")
    else:
        print(f"ℹ️ {role} 没有已记录的游标。")


def set_phase(phase: str):
    """强制改变系统阶段 (planning, execution, review, completed, discuss)"""
    state = _load_state()
    if state:
        state["phase"] = phase
        _save_state(state)
        print(f"✅ 系统阶段已切换为: {phase}")


def set_todos(todos_json: str):
    """子代理调用：增量添加/更新 todo 项"""
    state = _load_state()
    if state:
        try:
            new_todos = json.loads(todos_json)
            existing = {t["id"]: t for t in state["todos"]}
            added, updated = 0, 0
            for t in new_todos:
                if t["id"] in existing:
                    # 更新已有项（保留 status，除非新值指定了）
                    if "status" in t:
                        existing[t["id"]]["status"] = t["status"]
                    if "desc" in t:
                        existing[t["id"]]["desc"] = t["desc"]
                    if "assignee" in t:
                        existing[t["id"]]["assignee"] = t["assignee"]
                    updated += 1
                else:
                    # 追加新项
                    if "status" not in t:
                        t["status"] = "pending"
                    state["todos"].append(t)
                    added += 1
            _save_state(state)
            print(f"✅ Todo 已更新：新增 {added}，更新 {updated}，共 {len(state['todos'])} 项。")
        except Exception as e:
            print(f"❌ JSON 解析失败: {e}")


def update_todo(todo_id: str, status: str):
    """子代理调用：更新单个 todo 状态"""
    state = _load_state()
    if not state:
        return
    for t in state["todos"]:
        if t["id"] == todo_id:
            t["status"] = status
            _save_state(state)
            print(f"✅ Todo {todo_id} 状态已更新为 {status}")
            return
    print(f"❌ 未找到 todo: {todo_id}")


def save_session(role: str, session_id: str):
    """Orchestrator 调用：保存子代理会话 ID"""
    state = _load_state()
    if state:
        state["sessions"][role] = session_id
        _save_state(state)
        print(f"✅ 已保存 {role} 的会话 ID: {session_id}")


def get_session(role: str):
    """Orchestrator 调用：获取子代理会话 ID"""
    state = _load_state()
    if state and role in state["sessions"]:
        print(state["sessions"][role])
    else:
        print("none")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")

    p_init = subparsers.add_parser("init")
    p_init.add_argument("goal")

    p_say = subparsers.add_parser("say")
    p_say.add_argument("role")
    p_say.add_argument("message")

    p_ctx = subparsers.add_parser("context")
    p_ctx.add_argument("--last", type=int, default=None, help="显示最近 N 条消息")
    p_ctx.add_argument("--diff", type=str, default=None, metavar="ROLE", help="增量读取：显示该 role 上次游标到最新消息")

    p_phase = subparsers.add_parser("set-phase")
    p_phase.add_argument("phase")

    p_todos = subparsers.add_parser("set-todos")
    p_todos.add_argument("json_str")

    # 兼容旧命令名
    p_tasks = subparsers.add_parser("set-tasks")
    p_tasks.add_argument("json_str")

    p_todo = subparsers.add_parser("update-todo")
    p_todo.add_argument("id")
    p_todo.add_argument("status")

    # 兼容旧命令名
    p_task = subparsers.add_parser("update-task")
    p_task.add_argument("id")
    p_task.add_argument("status")

    p_save_ses = subparsers.add_parser("save-session")
    p_save_ses.add_argument("role")
    p_save_ses.add_argument("session_id")

    p_get_ses = subparsers.add_parser("get-session")
    p_get_ses.add_argument("role")

    p_reset = subparsers.add_parser("reset-cursor")
    p_reset.add_argument("role")

    args = parser.parse_args()

    if args.cmd == "init": init_workspace(args.goal)
    elif args.cmd == "say": say(args.role, args.message)
    elif args.cmd == "context": get_context(last=args.last, diff_role=args.diff)
    elif args.cmd == "set-phase": set_phase(args.phase)
    elif args.cmd == "set-todos": set_todos(args.json_str)
    elif args.cmd == "update-todo": update_todo(args.id, args.status)
    # 兼容旧命令名
    elif args.cmd == "set-tasks": set_todos(args.json_str)
    elif args.cmd == "update-task": update_todo(args.id, args.status)
    elif args.cmd == "save-session": save_session(args.role, args.session_id)
    elif args.cmd == "get-session": get_session(args.role)
    elif args.cmd == "reset-cursor": reset_cursor(args.role)
    else: parser.print_help()
