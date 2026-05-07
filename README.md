# FarmWise （慧农通---智慧农业播RAG助手）

基于 **LangChain , ReAct , RAG** 架构的农业专家智能客服系统，支持 RAG 知识库检索、实时天气适配、地理位置感知、个人使用报告生成，通过 FastAPI + 原生 HTML/JS 前端提供流式对话体验。

---

## 核心能力

- **RAG 知识问答**：基于 ChromaDB 向量库检索农作物播种收割、病虫害防治等专业知识，LLM 总结后返回
- **实时天气适配**：自动获取用户城市与实时天气，结合温湿度给出针对性的播种/收割/病虫害防治建议
- **个人使用报告**：按用户 ID + 月份查询外部使用记录，生成个性化农业作业报告
- **流式对话**：SSE 流式返回，AI 推理过程可折叠（thinking），最终答案用 marked.js 渲染 Markdown
- **知识库管理**：前端一键加载 TXT/PDF 文档入向量库，MD5 自动去重避免重复入库

---

## 技术栈

| 层级 | 技术 |
|------|------|
| Web 框架 | FastAPI + Uvicorn |
| AI 框架 | LangChain / LangGraph (ReAct Agent) |
| 对话模型 | DeepSeek (`deepseek-reasoner`) |
| Embedding | DashScope (`text-embedding-v4`) |
| 向量数据库 | ChromaDB |
| 前端 | 原生 HTML/CSS/JS + marked.js (CDN) |
| 包管理 | uv (Python >= 3.13) |

---

## 环境配置

### 1. 前置要求

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/) 包管理工具

### 2. 安装依赖

```bash
uv sync
```

### 3. 配置环境变量

复制 `.env-example` 为 `.env` 并填写真实 API Key：

```bash
cp .env-example .env
```

`.env` 文件说明：

| 变量 | 说明 |
|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek 对话模型 API Key（必填） |
| `DASHSCOPE_API_KEY` | 阿里云 DashScope API Key，用于文本 Embedding（必填） |

若缺少任一 Key，模型调用将直接失败。

---

## 项目结构

```
agtpjt/
├── agent/                        # Agent 核心
│   ├── react_agent.py            # ReAct Agent 定义，工具+中间件组装
│   └── tools/
│       ├── agent_tools.py        # 7 个工具定义（RAG、天气、定位、报告等）
│       ├── middleware.py          # 3 个中间件（监控、日志、提示词切换）
│       ├── Weather/weather.py    # 天气查询（wttr.in 主 / Open-Meteo 备）
│       └── Location/location.py  # IP 定位（ip-api.com）
├── config/                       # YAML 配置文件
│   ├── agent.yml                 # Agent 全局配置
│   ├── chroma.yml                # 向量库及文档分片参数
│   ├── rag.yml                   # 模型名称配置
│   └── prompts.yml               # 提示词文件路径
├── data/                         # 知识库文档目录
│   └── external/records.csv      # 外部使用记录数据（报告生成用）
├── database/chroma_db/           # ChromaDB 持久化目录
├── model/factory.py              # 模型工厂（单例），chat_model + embedding_model
├── prompts/                      # 提示词模板
│   ├── main_prompt.txt           # 默认系统提示词（ReAct 流程约束）
│   ├── report_prompt.txt         # 报告模式提示词（动态切换）
│   └── rag_summarize.txt         # RAG 总结提示词
├── rag/                          # RAG 管道
│   ├── rag_service.py            # 检索+LLM总结服务
│   └── vector_store.py           # 向量库加载/检索
├── static/                       # 前端静态资源
│   ├── index.html                # 聊天页面
│   ├── app.js                    # SSE 流式消费 + UI 逻辑
│   └── style.css                 # 样式
├── utils/                        # 工具模块
│   ├── config_handler.py         # 配置加载器（模块导入时自动加载为全局字典）
│   ├── memory.py                 # 对话记忆管理器（按 user_id 区分，内存级）
│   ├── prompt_loader.py          # 提示词文件加载器
│   ├── path_tool.py              # 统一绝对路径解析
│   ├── file_handler.py           # 文件读取/MD5/文档加载器
│   └── logger_handler.py         # 日志配置（控制台 INFO + 文件 DEBUG）
├── logs/                         # 运行日志
├── .env-example                  # 环境变量模板
├── pyproject.toml                # 项目依赖定义
└── web_app.py                    # FastAPI 入口，SSE 流式对话端点
```

---

## 配置说明

### `config/agent.yml` — Agent 全局配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `external_data_path` | `data/external/records.csv` | 外部使用记录 CSV 路径（报告生成数据源） |
| `debug_print_all_msg` | `False` | 开启后在控制台和日志中打印完整 messages JSON |
| `user_id` | `"1001"` | 默认用户 ID（`get_user_id` 工具返回值，无多用户认证） |

### `config/chroma.yml` — 向量库及文档分片配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `collection_name` | `agent` | ChromaDB 集合名称 |
| `persist_directory` | `database/chroma_db` | 向量库持久化目录 |
| `k` | `3` | 检索时返回的最相似文档数 |
| `data_path` | `data` | 知识库文档扫描根目录 |
| `md5_hex_store` | `md5.text` | MD5 去重记录文件路径 |
| `allow_knowledge_file_type` | `["txt","pdf"]` | 允许加载的文件类型 |
| `chunk_size` | `200` | 文本分片大小（字符数） |
| `chunk_overlap` | `20` | 相邻分片重叠长度 |
| `separators` | 见文件 | 分片分隔符优先级列表（`\n\n` → `\n` → 标点 → 空格） |

### `config/rag.yml` — 模型名称配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `chat_model_name` | `deepseek-reasoner` | LangChain 对话模型名称 |
| `embedding_model_name` | `text-embedding-v4` | DashScope Embedding 模型名称 |

> 若更换 Embedding 模型，需清空 `database/chroma_db/` 并重新加载知识库，否则旧向量与新模型维度不匹配。

### `config/prompts.yml` — 提示词路径配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `main_prompt_path` | `prompts/main_prompt.txt` | 默认系统提示词 |
| `rag_summarize_prompt_path` | `prompts/rag_summarize.txt` | RAG 总结提示词 |
| `report_prompt_path` | `prompts/report_prompt.txt` | 报告模式提示词 |

---

## 启动服务

```bash
# 开发模式（带热重载，默认端口 8088）
uv run python -m uvicorn web_app:app --port 8088 --reload
```

浏览器打开 `http://localhost:8088` 即可使用。

---

## 加载知识库文档

1. **准备文档**：将 `.txt` 或 `.pdf` 格式的文档放入 `data/` 目录（支持子目录）
2. **前端加载**：打开聊天页面，点击左侧边栏的 **「加载知识库文档」** 按钮
3. **自动处理**：系统会：
   - 扫描 `data/` 下所有 `txt`/`pdf` 文件
   - 通过 MD5 校验去重（已加载过的文件自动跳过）
   - 按 `config/chroma.yml` 中的参数分片并向量化
   - 存入 `database/chroma_db/`
4. **查看状态**：日志输出到 `logs/` 目录，每份文件的加载成功/跳过/失败均有记录

---

## Agent 工具说明

| 工具 | 入参 | 功能 | 使用场景 |
|------|------|------|---------|
| `rag_summarize` | `query: str` | 向量库检索 + LLM 总结，返回专业知识 | **通用咨询场景**：农作物播种收割建议、病虫害防治等 |
| `get_weather` | `city: str` | 查询指定城市实时天气（温湿度、降雨概率等） | **实时环境适配场景**：获取天气后结合 RAG 给出精准建议 |
| `get_location` | 无 | 通过 IP 获取当前城市名 | 配套 `get_weather` 使用，获取用户所在地城市 |
| `get_user_id` | 无 | 返回当前用户 ID | **报告生成场景**：获取用户 ID 用于检索使用记录 |
| `get_current_date` | 无 | 返回当前日期 `YYYY-MM-DD` | 报告生成时确定月份，或用户未指定月份时自动获取 |
| `fill_context_for_report` | 无 | 触发中间件标记报告上下文，切换提示词 | **报告生成前置步骤**，必须在 `fetch_external_data` 之前调用 |
| `ddsearch` | 无参 | DuckDuckGo 联网搜索 | **兜底补充**：RAG 结果不足、信息过时或可信度存疑时使用 |

### 工具调用规则

- **场景判断优先**：Agent 先判断用户意图属于「实时环境适配」「通用咨询」「个人报告查询」中的哪一种，再选择对应工具链
- **串行依赖**：后一个工具依赖前一个工具返回值时，必须串行执行，严禁并行调用
- **联网兜底**：`ddsearch` 仅在 RAG 检索结果不足时补充使用，联网信息需严格甄别

---

## 中间件说明

中间件在 LangGraph Agent 运行时注入，位于 `agent/tools/middleware.py`。

| 中间件 | 类型 | 功能 |
|--------|------|------|
| `monitor_tool` | `@wrap_tool_call` | 记录每次工具调用的名称、入参和结果；检测到 `fill_context_for_report` 调用时将 `runtime.context['report']` 置为 `True` |
| `log_before_model` | `@before_model` | 模型调用前记录当前消息数量；若 `debug_print_all_msg=True` 则输出完整 messages JSON |
| `report_prompt_switch` | `@dynamic_prompt` | 每次生成提示词前检查 `context['report']`，若为 `True` 则加载 `report_prompt.txt`，否则加载 `main_prompt.txt` |

---

## 报告生成流程

当用户明确要求「生成/查询个人使用报告」时，Agent 严格按以下固定链路串行执行：

```
get_user_id → get_current_date（或用户指定月份）→ fill_context_for_report → fetch_external_data → 模型生成报告
```

1. **`get_user_id`** — 获取当前用户 ID
2. **`get_current_date`** — 获取当前日期确定月份（用户指定月份则跳过此步）
3. **`fill_context_for_report`** — 注入报告上下文标记，触发 `monitor_tool` 中间件将 `context['report']` 置为 `True`
4. **`fetch_external_data`** — 以 `user_id` + `month` 为参数，从 `data/external/records.csv` 检索该用户该月的农业作业记录
5. **模型生成报告** — `report_prompt_switch` 中间件检测到上下文标记后自动切换至 `prompts/report_prompt.txt`，模型基于报告专用提示词生成最终报告

---

## 对话记忆

- 内存级管理，按 `user_id` 区分会话
- 基于 token 估算自动裁剪（阈值 128K），超出时移除最早消息
- 不持久化，重启后清空
- 前端「清空对话记忆」按钮可手动清除当前用户记忆

---

## 注意事项

- 首次运行前务必配置 `.env` 中的两个 API Key
- 若更换 Embedding 模型，需清空 `database/chroma_db/` 并重新加载知识库
- 前端 marked.js 通过 CDN 引入（`cdn.jsdelivr.net`），确保网络可访问
- Windows 下天气模块有 GBK 编码修复逻辑，不要删除

