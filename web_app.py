import json
import os
import re

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent.react_agent import ReactAgent
from rag.vector_store import VectorStoreService
from utils.memory import memory
from utils.config_handler import agent_conf, get_abs_path

app = FastAPI(title="智慧农业播种收割RAG助手")

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


class ChatRequest(BaseModel):
    query: str


@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_path = os.path.join(static_dir, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


class SetUserIdRequest(BaseModel):
    user_id: str


@app.post("/api/set-user-id")
async def set_user_id(request: SetUserIdRequest):
    uid = request.user_id.strip()
    if not re.fullmatch(r"\d{4}", uid):
        return {"status": "error", "message": "user_id 必须为4位数字"}
    config_path = get_abs_path("config/agent.yml")
    # 读取全量 保留注释顺序
    with open(config_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = []
    for line in lines:
        if re.match(r"^\s*user_id\s*:", line):
            new_lines.append(f'user_id : "{uid}"      #用户id\n')
        else:
            new_lines.append(line)
    with open(config_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    agent_conf["user_id"] = uid
    return {"status": "success", "message": f"user_id 已更新为 {uid}"}


@app.post("/api/get-user-id")
async def get_user_id():
    return {"user_id": agent_conf.get("user_id", "1001")}


@app.post("/api/clear-session")
async def clear_session():
    user_id = agent_conf['user_id']
    memory.clear(user_id)
    return {"status": "success", "message": "对话记忆已清空"}


@app.post("/api/load-knowledge")
async def load_knowledge():
    try:
        vs = VectorStoreService()
        vs.load_document()
        return {"status": "success", "message": "知识库文档加载完成！"}
    except Exception as e:
        return {"status": "error", "message": f"加载失败: {str(e)}"}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    def event_stream():
        user_id = agent_conf['user_id']
        memory.add_message(user_id, "user", request.query)
        messages = memory.get_history(user_id)
        agent = ReactAgent()
        full_reply = ""
        try:
            for item in agent.execute_stream(messages):
                data = json.dumps(item, ensure_ascii=False)
                if item.get("type") == "final":
                    full_reply += item.get("chunk", "")
                yield f"data: {data}\n\n"
        except Exception as e:
            data = json.dumps({"type": "error", "chunk": str(e)}, ensure_ascii=False)
            yield f"data: {data}\n\n"
        finally:
            if full_reply:
                memory.add_message(user_id, "assistant", full_reply)
            data = json.dumps({"type": "done", "done": True}, ensure_ascii=False)
            yield f"data: {data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=True)
