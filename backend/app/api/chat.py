# chat.py

from fastapi import APIRouter, Request
from pydantic import BaseModel
from langchain_agent.agent import TravelGraphAgent
from langchain.schema import HumanMessage, SystemMessage

router = APIRouter()

# 用户对话请求模型
class ChatRequest(BaseModel):
    user_id: str
    message: str

# 内存状态（可换成数据库持久化）
user_memory = {}
user_todo = {}

MANDATORY_FIELDS = ["目的地", "日期", "时长", "预算", "人数", "偏好"]

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    user_id = req.user_id
    message = req.message.strip()

    # 初始化用户状态
    if user_id not in user_memory:
        user_memory[user_id] = {"history": [], "slots": {}, "first_prompt": True}
        user_todo[user_id] = generate_initial_todo()

    memory = user_memory[user_id]
    todo = user_todo[user_id]

    # 更新历史
    memory["history"].append(HumanMessage(content=message))

    # 检查是否是第一次输入
    if memory["first_prompt"]:
        memory["first_prompt"] = False
        missing_fields = check_missing_fields(memory["slots"], message)
        if missing_fields:
            return {
                "type": "info",
                "message": f"你好！为了帮你定制旅游路线，我需要一些信息：{', '.join(missing_fields)}。你可以在对话右上角点击设置随时填写这些内容，或者现在直接告诉我。",
                "todo": todo
            }

    # 提取信息填充slots
    extract_slots(memory["slots"], message)

    # 如果即将生成路线，再次检查必要信息
    if "生成路线规划" in todo and is_final_step(todo):
        missing_fields = check_missing_fields(memory["slots"], message)
        if missing_fields:
            return {
                "type": "warning",
                "message": f"在生成最终旅游路线前，我还需要：{', '.join(missing_fields)}。请补充或点击右上角设置填写。",
                "todo": todo
            }

    # 执行当前任务并判断是否跳过
    response, next_step = execute_todo_step(todo, memory["slots"], message)

    return {
        "type": "success",
        "response": response,
        "next": next_step,
        "todo": todo
    }

def check_missing_fields(slots, message):
    missing = []
    for key in MANDATORY_FIELDS:
        if key not in slots:
            if key in message:
                slots[key] = message  # 简化处理
            else:
                missing.append(key)
    return missing

def extract_slots(slots, message):
    # 简化提取逻辑，可以后续加入NLP识别
    for key in MANDATORY_FIELDS:
        if key in message and key not in slots:
            slots[key] = message

def is_final_step(todo):
    return todo and todo[0]["name"] == "生成路线规划"

def generate_initial_todo():
    return [
        {"name": "信息收集", "status": "pending", "desc": "查找用户需求相关数据（例如目的地资料）"},
        {"name": "分类整理", "status": "pending", "desc": "将景点/交通/餐饮等分类"},
        {"name": "呈现建议", "status": "pending", "desc": "将推荐内容呈现给用户选择"},
        {"name": "用户反馈", "status": "pending", "desc": "根据用户选择调整推荐内容"},
        {"name": "生成路线规划", "status": "pending", "desc": "最终生成一条完整旅游路线"},
        {"name": "文档提交", "status": "pending", "desc": "将路线打包成计划文档提交给前端"}
    ]

def execute_todo_step(todo, slots, message):
    if not todo:
        return "已完成所有步骤！", None

    current = todo.pop(0)
    current["status"] = "done"
    explanation = f"完成：{current['name']} - {current['desc']}"

    if todo:
        next_step = todo[0]
        return explanation + f"\n接下来是：{next_step['name']} - {next_step['desc']}。", next_step["name"]
    else:
        return explanation + "\n已完成所有步骤。", None
