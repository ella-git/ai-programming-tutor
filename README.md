# ai-programming-tutor
为解决小组协作交流深度不足，搭建多智能体辅助协作系统，非传统客服问答角色，采用 Vue3 + FastAPI 前后端分离架构，通过 WebSocket 实现多人聊天室实时通信，结合 LangChain 构建两个不同角色的智能体参与小组交流，实现RAG知识增强问答、多轮对话、长期记忆、主动干预等，上学期已经在课堂落地，约300+学生使用。
# 多智能体辅助协编程系统

> **体验地址**  
## 一、总体架构概览

```
┌──────────────────────────────────────────────────────────┐
│                  客户端层 (Vue 3 SPA)                       │
│   Element Plus UI  ·  Vue Router  ·  Axios  ·  WebSocket  │
└──────────────────────┬───────────────────────────────────┘
                       │ HTTP REST (JSON)  /  WebSocket
                       ▼
┌──────────────────────────────────────────────────────────┐
│                反向代理层 (Vite Dev Server)                  │
│          开发：proxy /api → localhost:8000                  │
└──────────────────────┬───────────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────────┐
│                  API 服务层 (FastAPI + Uvicorn)              │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│   │ Auth     │ │ Room     │ │ Message  │ │ Upload     │  │
│   │ 路由     │ │ 路由     │ │ 路由     │ │ 路由       │  │
│   └──────────┘ └──────────┘ └──────────┘ └────────────┘  │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│   │ Agent    │ │ Knowledge│ │ Semantic │ │ Memory     │  │
│   │ 路由     │ │ 路由     │ │ 路由     │ │ 路由       │  │
│   └──────────┘ └──────────┘ └──────────┘ └────────────┘  │
└──────────┬───────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────┐
│                  业务逻辑层 (Services)                       │
│   auth_service  ·  room_service  ·  message_service        │
│   rag_service  ·  embedding_service  ·  memory_service     │
│   semantic_service  ·  summary_service  ·  document_service│
└──────────┬───────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────┐
│                   数据与基础设施层                           │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌────────────┐  │
│  │ SQLite  │  │  FAISS   │  │ 文件   │  │  Sentence  │  │
│  │ (主数据库)│  │ 向量索引  │  │ 存储   │  │Transformer │  │
│  └─────────┘  └──────────┘  └────────┘  └────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │        外部 LLM API (火山引擎 ARK 大模型)              │  │
│  │   doubao-seed-2-1-turbo · deepseek-v4-pro · glm-4  │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## 二、前端技术栈 (Vue 3)

| 类别 | 技术选型 | 说明 |
|------|----------|------|
| **框架** | Vue 3 + Composition API | `<script setup>` 语法，响应式开发 |
| **构建工具** | Vite 4 | 开发 HMR、生产构建、代理转发 |
| **路由** | Vue Router 4 | createWebHistory 模式，路由守卫实现登录拦截 |
| **状态管理** | 组件内状态 (ref/reactive) + localStorage | 无 Pinia/Vuex，轻量设计 |
| **UI 组件库** | Element Plus 2 | 全局注册完整图标库 |
| **HTTP 客户端** | Axios 1 | 请求拦截器注入 JWT，响应拦截器处理 401 |
| **实时通信** | 原生 WebSocket | 自定义重连机制（指数退避，最多 10 次） |
| **样式方案** | Scoped CSS | 组件级样式隔离 |

### 核心前端模块

```
src/
├── main.js                 # 应用入口：createApp + 注册 Element Plus + 路由
├── App.vue                 # 根组件：<router-view> + 全局重置样式
├── api/                    # Axios 封装 + 各模块 API
│   ├── index.js            # Axios 实例（拦截器 + JWT）
│   ├── auth.js / room.js / message.js
│   ├── agent.js / knowledge.js / user.js / semantic.js
├── router/index.js         # 路由配置 + 登录守卫
├── views/                  # 页面视图
│   ├── Login.vue / Register.vue
│   ├── JoinRoom.vue / ChatRoom.vue
│   ├── Setting.vue / UserManage.vue / RoomManage.vue
├── components/             # 通用组件
│   ├── KnowledgeUpload.vue
│   └── SemanticSetting.vue
└── websocket/socket.js     # WebSocket 客户端封装
```

---

## 三、后端技术栈 (FastAPI + Python 3.13)

| 类别 | 技术选型 | 说明 |
|------|----------|------|
| **语言** | Python 3.13+ | 类型注解支持完善 |
| **Web 框架** | FastAPI + Uvicorn | 异步高性能，自动 OpenAPI 文档 |
| **ORM** | SQLAlchemy 2.0 | DeclarativeBase 声明式映射 |
| **数据库** | SQLite | 嵌入式关系数据库，零运维成本 |
| **认证** | JWT (python-jose + bcrypt) | HS256 签名，24h 过期 |
| **LLM 集成** | LangChain (langchain-openai) | ChatOpenAI 接口对接火山引擎 ARK |
| **向量数据库** | FAISS (IndexFlatIP) | 内积相似度搜索，384 维 |
| **文本嵌入** | Sentence-Transformers | BAAI/bge-small-zh-v1.5 本地模型 |
| **文档解析** | LangChain Loaders | 支持 PDF、DOCX、TXT |
| **任务调度** | APScheduler | 定时生成房间对话摘要（20 分钟/次） |
| **数据导出** | Openpyxl | Excel 格式导出聊天记录（含图片） |
| **跨域** | CORSMiddleware | 允许 3000/3004/5173 端口 |

### 后端目录结构

```
backend/
├── .env                             # 环境变量（密钥、API Key、模型配置）
├── requirements.txt                 # Python 依赖清单
├── app/
│   ├── main.py                      # FastAPI 入口：生命周期、中间件、路由注册
│   ├── core/
│   │   ├── config.py                # 环境配置读取
│   │   ├── security.py              # JWT 编解码、密码哈希
│   │   ├── dependencies.py          # FastAPI 依赖注入（get_current_user）
│   │   └── exceptions.py            # 自定义异常处理器
│   ├── database/
│   │   ├── database.py              # SQLAlchemy 引擎 + Session 工厂
│   │   └── models.py                # 核心 ORM 模型（User, ChatRoom, Message 等）
│   ├── schemas/                     # Pydantic 请求/响应模型
│   ├── routers/                     # 10 个 API 路由模块
│   ├── services/                    # 业务逻辑层（9 个 Service）
│   ├── agent/                       # 认知智能体
│   ├── agents/                      # 元认知智能体
│   ├── rag/                         # RAG 检索模块（FAISS 索引 + 检索器）
│   ├── llm/                         # LLM 调用工厂
│   ├── models/                      # 知识库 & 语义分析 ORM 模型
│   ├── semantic/                    # 语义检测器 + 触发器
│   ├── websocket/                   # WebSocket 端点 + 连接管理器
│   └── tasks/                       # APScheduler 定时任务
├── data/
│   ├── app.db                       # SQLite 数据库文件
│   └── faiss/                       # FAISS 序列化索引
├── storage/knowledge_files/         # 上传的知识库文档
└── uploads/                         # 聊天上传的图片
```

---

## 四、核心架构模式

### 4.1 RAG 检索增强生成流水线

```
用户问题
   │
   ▼
┌─────────────────────┐
│  向量化问题          │  ← SentenceTransformer (384维)
└────────┬────────────┘
         ▼
┌─────────────────────┐
│  FAISS 相似度搜索   │  ← IndexFlatIP，top_k=5
└────────┬────────────┘
         ▼
┌─────────────────────┐
│  检索知识块内容      │  ← 从 KnowledgeChunk 表获取
└────────┬────────────┘
         ▼
┌─────────────────────┐
│  拼接 LLM Prompt    │  ← 【知识库参考】段落 + 历史 + 系统提示
└────────┬────────────┘
         ▼
┌─────────────────────┐
│  LLM 生成回答       │  ← doubao-seed-2-1-turbo
└─────────────────────┘
```

**关键参数**：
- 文本块大小：500 字符，重叠 100 字符
- 嵌入维度：384
- 检索数量：top_k = 5
- 相似度算法：内积 (Inner Product)

### 4.2 多智能体架构

| 智能体 | 触发方式 | 模型 | 功能 |
|--------|----------|------|------|
| **认知智能体** (Cognitive Agent) | 聊天输入 `@认知智能体` | doubao-seed-2-1-turbo-260628 | 基于 RAG 知识库回答问题，结合房间记忆与对话历史 |
| **元认知智能体** (Metacognitive Agent) | "举手"按钮 / 语义关键词命中 | deepseek-v4-pro-260425 | 高阶分析，引导学习者反思与深度思考 |
| **摘要智能体** (Summary Agent) | APScheduler 定时触发（20 分钟） | glm-4-7-251222 | 自动生成房间对话摘要，存入 RoomMemory |

### 4.3 语义关键词检测系统

```
聊天消息
   │
   ▼
┌─────────────────────────────┐
│  SentenceTransformer 编码   │  ← 生成 384 维向量
└─────────────┬───────────────┘
              ▼
┌─────────────────────────────┐
│  与所有关键词向量计算余弦相似度│  ← 阈值 0.6
└─────────────┬───────────────┘
              ▼
       ┌──────┴──────┐
       ▼              ▼
    匹配成功        未匹配
       │              │
       ▼              ▼
  触发元认知        正常处理
  智能体干预
```

### 4.4 REST + WebSocket 混合通信

- **REST API**（前缀 `/api/*`）：认证、房间管理、消息查询、知识库 CRUD、智能体触发
- **WebSocket**（`/ws/chat/{room_id}`）：
  - 实时文本/图片/智能体消息推送
  - 系统通知（用户加入/离开）
  - 智能体输入状态实时推送
  - 断线自动重连（最多 10 次，间隔从 1s 递增到 10s）

### 4.5 实验支撑设计

- 房间编码规则：001~009 = 实验组（PBL 提示词），010~016 = 对照组（通用提示词）
- Agent Prompt 按 `agent_type` 动态加载，支持运行时上传更新
- 支持 300+ 学生并发实验

---

## 五、数据模型概览

### 5.1 核心业务表

| 表名 | 主要字段 | 说明 |
|------|----------|------|
| `users` | id, username (唯一索引), password_hash, created_time | 用户账户 |
| `chat_rooms` | id, room_code (唯一索引), creator_id, status, created_time | 聊天房间 |
| `room_members` | id, room_id, user_id, join_time, is_online | 房间成员 |
| `messages` | id, room_id, user_id, username, content, message_type(text/image/agent), created_time | 聊天消息 |
| `agent_prompts` | id, agent_type (唯一), prompt_content, filename, version | 智能体系统提示词 |
| `room_memory` | id, room_id (唯一), summary, updated_time | 房间长期摘要记忆 |

### 5.2 知识库向量表

| 表名 | 说明 |
|------|------|
| `knowledge_files` | 上传的知识文档元信息 |
| `knowledge_chunks` | 文档分块后的文本片段 |
| `knowledge_embeddings` | 384 维向量嵌入（JSON 存储） |
| `semantic_keywords` | 语义检测关键词 |
| `semantic_keyword_embeddings` | 关键词向量 |
| `semantic_analysis_config` | 语义分析间隔配置 |

---

## 六、安全设计

- **密码保护**：bcrypt 哈希存储，全程不存明文
- **JWT 鉴权**：HS256 签名，24 小时有效期，Bearer Token 传输
- **请求拦截**：Axios 拦截器自动注入 Token，401 自动清除并跳转登录
- **CSRF 防护**：Token 非 Cookie 存储，非浏览器自动携带
- **CORS 白名单**：仅允许指定前端域名跨域
- **文件上传限制**：仅允许图片类型，存储于独立目录

---

## 七、部署架构

```
┌────────────────────────────────────────┐
│            Linux 服务器 (39.96.180.126)  │
│                                          │
│  ┌──────────────┐  ┌─────────────────┐  │
│  │  Nginx/其他   │  │  uvicorn 进程    │  │
│  │  反向代理     │─▶│  (FastAPI)      │  │
│  │  :5000        │  │  :8000          │  │
│  └──────────────┘  └─────────────────┘  │
│                     ┌─────────────────┐  │
│                     │  静态文件服务     │  │
│                     │  (Vite 构建输出)  │  │
│                     └─────────────────┘  │
└────────────────────────────────────────┘
```

- **无容器化**：未使用 Docker，手动部署
- **开发模式**：`uvicorn app.main:app --reload`
- **前端构建**：`vite build` → `dist/` 目录

---

## 八、关键技术亮点

1. **端到端 RAG 流水线**：从文档上传、解析分块、本地向量化、FAISS 索引构建到 LLM 增强检索的全链路自研实现
2. **双智能体协作**：认知智能体负责知识问答，元认知智能体负责高阶思维引导，形成教学闭环
3. **语义实时检测**：基于 Embedding 余弦相似度的关键词检测系统，无需额外 NLP 服务
4. **轻量化架构**：单 SQLite + 本地 Embedding 模型 + FAISS，无需外部中间件即可运行，适合教育场景低成本部署
5. **教育实验支持**：房间分组、动态 Prompt 加载、定时摘要生成，满足教育实验研究需求
6. **前后端分离**：Vue 3 SPA + FastAPI 纯 API 后端，职责清晰，易于扩展
---
