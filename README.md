# 智扫通机器人智能客服

基于 **ReAct 架构** 的扫地机器人 / 扫拖一体机器人专业智能客服系统。支持 RAG 知识库检索、实时天气适配、地理位置感知、个人使用报告生成等功能，通过 FastAPI + 原生前端提供流式对话体验。

---

## 核心能力

- **RAG 知识问答**：基于向量库检索扫地机器人使用、故障排除、选购指南、维护保养等专业资料
- **实时天气适配**：自动获取用户所在城市与天气，结合温湿度给出针对性的使用和保养建议
- **个人使用报告**：按用户 ID + 月份查询外部数据，生成个性化使用报告
- **流式对话**：AI 回复实时逐字呈现，推理过程可折叠，最终答案支持 Markdown 渲染
- **知识库管理**：支持 TXT / PDF 格式文档一键加载，MD5 自动去重

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python + FastAPI |
| AI 框架 | LangChain / LangGraph (ReAct Agent) |
| 向量数据库 | ChromaDB |
| 对话模型 | DeepSeek (`deepseek-reasoner`) |
| Embedding | DashScope (`text-embedding-v4`) |
| 前端 | 原生 HTML / CSS / JS + marked.js (Markdown 渲染) |
| 包管理 | uv |

---

## 环境准备

本项目使用 [uv](https://docs.astral.sh/uv/) 作为 Python 包管理工具，要求 **Python >= 3.13**。

```bash
# 1. 安装 uv（若尚未安装）
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 克隆项目并进入目录
cd agent-project

# 3. 同步依赖
uv sync
```

> `uv sync` 会根据 `pyproject.toml` 和 `uv.lock` 自动创建虚拟环境并安装所有依赖。

---

## 项目结构

```
agent-project/
├── agent/                      # ReAct Agent 核心
│   ├── react_agent.py          # Agent 封装（execute_stream / execute_invoke）
│   └── tools/
│       ├── agent_tools.py      # 工具定义（RAG、天气、位置、日期、用户ID、外部数据、报告上下文）
│       ├── middleware.py       # 中间件（工具监控、模型调用日志、报告提示词切换）
│       ├── Location/           # IP 定位模块
│       └── Weather/            # 天气查询模块
├── rag/                        # RAG 服务
│   ├── rag_service.py          # RAG 总结服务（检索 + 总结链路）
│   └── vector_store.py         # ChromaDB 向量存储封装（加载/检索/MD5去重）
├── model/
│   └── factory.py              # 模型工厂（ChatModel + EmbeddingModel）
├── utils/                      # 通用工具模块
│   ├── config_handler.py       # YAML 配置加载器（rag/chroma/prompts/agent）
│   ├── file_handler.py         # 文件处理（MD5、PDF/TXT 加载、文件过滤）
│   ├── logger_handler.py       # 日志管理（控制台 + 文件双输出）
│   ├── path_tool.py            # 项目路径工具（统一绝对路径）
│   └── prompt_loader.py        # 提示词文件加载器
├── config/                     # YAML 配置文件
│   ├── agent.yml               # Agent 配置（外部数据路径、调试开关、用户ID）
│   ├── chroma.yml              # ChromaDB 配置（集合名、持久路径、分片参数）
│   ├── prompts.yml             # 提示词文件路径映射
│   └── rag.yml                 # RAG 配置（对话模型、Embedding 模型）
├── prompts/                    # 提示词模板
│   ├── main_prompt.txt         # 主系统提示词（ReAct 指令 + 工具说明）
│   ├── rag_summarize.txt       # RAG 总结提示词
│   └── report_prompt.txt       # 报告生成专用提示词
├── data/                       # 数据目录
│   ├── external/               # 外部数据（如 records.csv 使用记录）
│   ├── *.txt / *.pdf           # 知识库文档（保养、故障排除、选购指南等）
├── database/
│   └── chroma_db/              # ChromaDB 持久化存储目录
├── logs/                       # 运行日志目录
├── static/                     # 前端静态资源
│   ├── index.html              # 聊天页面
│   ├── style.css               # 样式（Markdown、折叠面板、消息气泡）
│   └── app.js                  # 前端逻辑（SSE、Markdown 渲染、推理折叠）
├── web_app.py                  # FastAPI 入口（页面 + API + SSE）
├── pyproject.toml              # 项目依赖配置
├── uv.lock                     # uv 锁定文件
├── .env-example                # 环境变量模板
└── README.md                   # 本文件
```

---

## 配置说明

### 1. 环境变量（.env）

复制模板文件并填写真实密钥：

```bash
cp .env-example .env
```

`.env` 内容示例：

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
DASHSCOPE_API_KEY=sk-yyyyyyyyyyyyyyyyyyyyyy
```

| 变量 | 说明 |
|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek 对话模型 API Key |
| `DASHSCOPE_API_KEY` | 阿里云 DashScope API Key（用于 Embedding） |

### 2. config/chroma.yml（向量库配置）

```yaml
collection_name : agent               # ChromaDB 集合名
persist_directory : database/chroma_db # 持久化目录（Windows 下也可使用反斜杠）
k : 3                                  # 检索返回文档数
data_path : data                       # 知识库文档根目录
md5_hex_store : md5.text               # MD5 去重记录文件
allow_knowledge_file_type : ["txt","pdf"]  # 允许的文件类型

chunk_size : 200       # 文本分片大小
chunk_overlap : 20     # 分片重叠长度
separators : ["\n\n","\n",".","!","?","\u3002","\uff1f","\uff01"," ",""]  # 分片分隔符优先级
```

### 3. config/rag.yml（模型配置）

```yaml
chat_model_name : deepseek-reasoner    # 对话模型名称
embedding_model_name : text-embedding-v4  # Embedding 模型名称
```

### 4. config/agent.yml（Agent 配置）

```yaml
external_data_path : data/external/records.csv  # 外部使用记录数据
debug_print_all_msg : False       # 开启后在日志中打印完整消息 JSON
user_id : "1001"                  # 默认用户 ID（get_user_id 工具返回）
```

### 5. config/prompts.yml（提示词路径）

```yaml
main_prompt_path : prompts/main_prompt.txt
rag_summarize_prompt_path : prompts/rag_summarize.txt
report_prompt_path : prompts/report_prompt.txt
```

---

## 如何启动

```bash
# 开发模式（带热重载）
uv run python -m uvicorn web_app:app --host 127.0.0.1 --port 8000 --reload

# 或直接使用入口文件
uv run python web_app.py
```

启动成功后，在浏览器打开：

```
http://localhost:8000
```

---

## 如何加载知识库文档

1. **准备文档**：将 `.txt` 或 `.pdf` 格式的知识库文件放入 `data/` 目录（可包含子目录）
2. **前端加载**：打开聊天页面，点击左侧边栏的 **「加载知识库文档」** 按钮
3. **自动处理**：系统会自动完成以下操作：
   - 扫描 `data/` 目录下所有允许类型的文件
   - 通过 MD5 校验自动去重（已加载过的文件会跳过）
   - 按 `config/chroma.yml` 中的参数分片
   - 向量化后存入 `database/chroma_db/`

> 日志文件保存在 `logs/` 目录，可查看每份文档的加载状态。

---

## Agent 工具说明

| 工具 | 功能 | 使用场景 |
|------|------|---------|
| `rag_summarize` | 从向量库检索资料并总结 | 通用咨询、故障排查、选购建议 |
| `get_weather` | 查询指定城市实时天气 | 环境适配场景 |
| `get_location` | 通过 IP 获取当前城市 | 配套天气查询使用 |
| `get_current_date` | 获取当前日期 `YYYY-MM-DD` | 报告生成时确定月份 |
| `get_user_id` | 获取当前用户 ID | 报告生成场景 |
| `fetch_external_data` | 检索指定用户指定月份的使用记录 | 报告生成场景 |
| `fill_context_for_report` | 触发报告提示词切换上下文 | 报告生成前置步骤 |

---

## 中间件说明

- **monitor_tool**：工具调用监控，记录工具名、入参、执行结果；检测到 `fill_context_for_report` 时标记报告上下文
- **log_before_model**：模型调用前日志，可开启 `debug_print_all_msg` 打印完整消息列表
- **report_prompt_switch**：动态提示词切换，报告场景下自动替换为 `report_prompt.txt`

---

## 日志说明

- 控制台输出级别：`INFO`
- 文件输出级别：`DEBUG`
- 日志格式：`时间 - 模块名 - 级别 - 文件名:行号 - 消息`
- 日志文件按启动时间命名，保存在 `logs/agent_YYYY-MM-DD-HH.MM.log`

---

## 报告生成流程

当用户意图为「生成/查询个人使用报告」时，Agent 会严格执行以下固定流程：

1. `get_user_id` -> 获取用户 ID
2. `get_current_date` 或用户指定 -> 确定月份
3. `fill_context_for_report` -> 注入报告上下文（触发提示词切换）
4. `fetch_external_data` -> 检索该用户该月的使用记录
5. 模型基于报告专用提示词生成最终报告

---

## 注意事项

- 首次运行前请务必配置 `.env` 中的 API Key，否则模型无法调用
- 若更换了 Embedding 模型，建议清空 `database/chroma_db/` 并重新加载知识库
- 前端使用 CDN 引入 `marked.js`，确保运行环境可访问 `cdn.jsdelivr.net`
