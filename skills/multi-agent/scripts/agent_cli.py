#!/usr/bin/env python3
"""
Multi-Agent Workflow 状态管理与群聊引擎
管理 .multi_agent_workspace/ 下的 state.json 和 chat.md。
支持子代理会话恢复 (Session Continuation) 和通用交流。
"""
import os
import json
import argparse
from datetime import datetime

WORKSPACE = ".multi_agent_workspace"
STATE_FILE = os.path.join(WORKSPACE, "state.json")
CHAT_FILE = os.path.join(WORKSPACE, "chat.md")

def init_workspace(goal: str):
    os.makedirs(WORKSPACE, exist_ok=True)
    state = {
        "global_goal": goal,
        "phase": "planning", # planning, execution, review, completed, discuss
        "tasks": [],
        "sessions": {}       # 保存 { "executor": "ses_xxx", "reviewer": "ses_yyy" }
    }
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        
    with open(CHAT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# Multi-Agent 群聊记录\n\n**[System]**: 总体目标已确立 -> {goal}\n")
        
    if not os.path.exists(".gitignore"):
        with open(".gitignore", "w", encoding='utf-8') as f:
            f.write(".multi_agent_workspace/\n")
    else:
        with open(".gitignore", "r", encoding='utf-8') as f:
            if ".multi_agent_workspace/" not in f.read():
                with open(".gitignore", "a", encoding='utf-8') as f:
                    f.write("\n.multi_agent_workspace/\n")
    print(f"✅ 工作区已初始化。目标: {goal}")

def _load_state():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

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

def get_context():
    """供各个角色唤醒时读取当前上下文"""
    state = _load_state()
    if not state:
        print("STATUS: uninitialized")
        return

    print("=== CURRENT STATE ===")
    print(f"Phase: {state['phase']}")
    print(f"Goal: {state['global_goal']}")
    
    print("\n=== TASKS ===")
    if not state["tasks"]:
        print("(No tasks planned yet)")
    for t in state["tasks"]:
        print(f"[{t['status']}] {t['id']}: {t['desc']}")

    print("\n=== RECENT CHAT ===")
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print("".join(lines[-25:])) # 打印最近 25 行群聊

def set_phase(phase: str):
    """强制改变系统阶段 (planning, execution, review, completed, discuss)"""
    state = _load_state()
    if state:
        state["phase"] = phase
        _save_state(state)
        print(f"✅ 系统阶段已切换为: {phase}")

def set_tasks(tasks_json: str):
    """Planner 调用：更新整个任务列表"""
    state = _load_state()
    if state:
        try:
            tasks = json.loads(tasks_json)
            # 保留旧任务的状态（如果存在）
            old_tasks = {t["id"]: t for t in state["tasks"]}
            for t in tasks:
                if t["id"] in old_tasks:
                    t["status"] = old_tasks[t["id"]]["status"]
                elif "status" not in t:
                    t["status"] = "pending"
            state["tasks"] = tasks
            _save_state(state)
            print(f"✅ 任务列表已更新，共 {len(tasks)} 个任务。")
        except Exception as e:
            print(f"❌ JSON 解析失败: {e}")

def update_task(task_id: str, status: str):
    """Executor/Reviewer 调用：更新单个任务状态"""
    state = _load_state()
    if not state:
        return
    for t in state["tasks"]:
        if t["id"] == task_id:
            t["status"] = status
            _save_state(state)
            print(f"✅ 任务 {task_id} 状态已更新为 {status}")
            return
    print(f"❌ 未找到任务: {task_id}")

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

    p_phase = subparsers.add_parser("set-phase")
    p_phase.add_argument("phase")

    p_tasks = subparsers.add_parser("set-tasks")
    p_tasks.add_argument("json_str")

    p_task = subparsers.add_parser("update-task")
    p_task.add_argument("id")
    p_task.add_argument("status")

    p_save_ses = subparsers.add_parser("save-session")
    p_save_ses.add_argument("role")
    p_save_ses.add_argument("session_id")

    p_get_ses = subparsers.add_parser("get-session")
    p_get_ses.add_argument("role")

    args = parser.parse_args()

    if args.cmd == "init": init_workspace(args.goal)
    elif args.cmd == "say": say(args.role, args.message)
    elif args.cmd == "context": get_context()
    elif args.cmd == "set-phase": set_phase(args.phase)
    elif args.cmd == "set-tasks": set_tasks(args.json_str)
    elif args.cmd == "update-task": update_task(args.id, args.status)
    elif args.cmd == "save-session": save_session(args.role, args.session_id)
    elif args.cmd == "get-session": get_session(args.role)
    else: parser.print_help()