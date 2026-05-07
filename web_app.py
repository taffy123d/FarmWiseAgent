import json
import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent.react_agent import ReactAgent
from rag.vector_store import VectorStoreService

app = FastAPI(title="智扫通机器人智能客服")

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


class ChatRequest(BaseModel):
    query: str


@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_path = os.path.join(static_dir, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


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
        agent = ReactAgent()
        try:
            for item in agent.execute_stream(request.query):
                data = json.dumps(item, ensure_ascii=False)
                yield f"data: {data}\n\n"
        except Exception as e:
            data = json.dumps({"type": "error", "chunk": str(e)}, ensure_ascii=False)
            yield f"data: {data}\n\n"
        finally:
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
