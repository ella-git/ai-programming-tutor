# ai-programming-tutor
基于大模型与RAG的协作式编程学习辅助平台，支持python编码，同伴交流、AI问答、知识库检索等。
# 基于 RAG 架构的智能协作与元认知辅助系统

> **声明**  
> 本项目源码设置为**私有（Private）**，本页面仅用于功能演示、架构展示及技术交流。
<img width="1920" height="905" alt="image" src="https://github.com/user-attachments/assets/fb5e3c4d-07de-4d31-9097-fa97b943a68b" />

## 🧰 核心技术栈

| 模块 | 技术 |
|------|------|
| 后端框架 | Python / Flask（轻量级高并发架构） |
| 大语言模型 | Kimi-k2-250905 / Doubao-seed-character / GLM-4（通过 OpenAI SDK 适配） |
| 向量数据库 | FAISS（高效向量相似度检索，384 维 L2 索引） |
| 本地嵌入模型 | Sentence-Transformers `paraphrase-multilingual-MiniLM-L12-v2`（本地加载，保护隐私） |
| 数据持久化 | SQLite（用户/消息记录） & Openpyxl（结构化聊天记录导出，含图片嵌入） |
| 多线程 | Python `threading`（后台总结线程、日志清理线程、聊天记录清理线程） |

---

## 1. 系统架构展示

### 1.1 RAG（检索增强生成）工作流

本项目实现了完整的 RAG 闭环，有效解决了大模型"幻觉"问题。

文档（`.docx` / `.txt`）上传后，系统自动执行：

1. **文本分块**（chunk_size=300，overlap=50，滑动窗口切割）
2. **本地向量化**（MiniLM-L12-v2 模型，生成 384 维向量）
3. **写入 FAISS 索引** + **SQLite 持久化**
4. 用户提问时，先向 FAISS 检索 Top-K 相关片段，拼接为 `【知识库参考】` 追加到 Prompt 中，再调用大模型生成回答

> 检索与问答均发生在本地嵌入层，向量化过程不依赖任何外部 API，保障数据安全。


---

### 1.2 多线程智能体（Agent）逻辑

系统通过 `threading` 实现三条后台守护线程，确保主请求链路不被阻塞：

| 线程 | 职责 | 触发间隔 |
|------|------|---------|
| `summary_worker` | 定期扫描所有活跃聊天室，调用**元认知智能体**生成对话总结 | 可动态配置（默认 60 秒） |
| `chat_db_cleaner_worker` | 删除数据库中超过 48 小时的聊天记录 | 每小时 |
| `log_cleaner_worker` | 当日志文件超过 5MB 时自动清空 | 每小时 |

启动时还会从数据库恢复最近 12 小时的聊天记录到内存，实现**重启不丢消息**。


---

## 2. 功能演示

### 🎬 功能一：AI 编程问答（RAG 增强）

**特点：** 用户在编程学习页面发起提问，系统先检索知识库 Top-2 相关片段，拼接为上下文后调用 `Kimi-k2-250905` 生成回答；支持多轮对话历史记忆（按用户 ID 维护独立 history）。

**演示重点：** 提问时 AI 回答中出现 `【知识库参考】` 引用内容，体现 RAG 检索效果。

<img width="1915" height="918" alt="image" src="https://github.com/user-attachments/assets/8dcb56b3-6faf-46a4-8cf2-4d3b50cd4456" />


---

### 🎬 功能二：主动引导辅助

**特点：** 用户点击"举手"按钮触发 **认知** 智能体，系统也可以根据**房间号自动匹配不同 Prompt 策略**（例如：实验组 001-009 使用 PBL 引导提示词，对照组 010-016 使用通用提示词），结合当前聊天上下文和知识库，调用 `glm-4-7-251222` 生成针对性引导回复，并在回复中 `@` 触发用户。

**演示重点：** 点击举手按钮 → AI 针对当前上下文给出个性化引导性回复，而非直接给答案。

<img width="1920" height="905" alt="f4f59705c23d1a10c7d2705c2fd4975a" src="https://github.com/user-attachments/assets/e11dda71-0feb-40e2-9229-d67e3fe28db9" />

<img width="1901" height="915" alt="image" src="https://github.com/user-attachments/assets/5df9d307-53f6-457d-b2c4-a8c0aa2f77e7" />
---

### 🎬 功能三：元认知智能总结

**特点：** 后台线程 ** 根据管理员配置的时间间隔，自动抓取聊天室最近 X 条消息，结合知识库检索，调用 `doubao-seed-character-251128` 生成阶段性学习总结并推送至聊天室。总结仅在有新消息时触发，避免重复生成。

**演示重点：** 多人对话后，AI 代理人自动在聊天室中弹出对话总结摘要。
<img width="1905" height="901" alt="image" src="https://github.com/user-attachments/assets/55ace331-de8b-4d05-9b89-5f015c8f81f1" />




---

### 🎬 功能四：多角色权限与数据导出

**特点：**  
- 完整的登录注册体系（Flask-Login + SQLAlchemy），支持会话持久化  
- 管理员页面可导出：**注册用户名单**（Excel，含注册时间统计 Sheet）、**聊天室完整记录**（Excel，图片直接嵌入单元格，80×80px）、**编程问答记录**（含 MD5 去重，自动清理 24h 前记录）  
- 聊天室支持图片上传（16MB 限制，格式白名单校验），图片以时间戳+随机串命名存储

<img width="1905" height="879" alt="image" src="https://github.com/user-attachments/assets/0d72ca9e-5c52-4133-9d6c-308cefcc99a0" />



---

## 3. 技术亮点

**数据一致性保证：** 采用 `hashlib.md5` 对聊天记录进行去重（key 为 `user_id + question + answer` 的哈希值），防止前端重复提交；SQLite 使用绝对路径 + 连接池 `pool_pre_ping`，确保跨环境数据库稳定访问。

**内存 + 数据库双写架构：** 聊天室消息采用"写时双存"策略——每条消息同时写入 SQLite 数据库（`chat_messages` 表）和内存字典（`chat_rooms`）。内存保证实时读取性能，数据库保障持久化；服务重启时自动从数据库恢复最近 12 小时的聊天记录到内存

**双组实验设计：**  智能体根据房间号划分实验组（001-009）与对照组（010-016），分别加载不同 Prompt 策略，支持从 `.docx` 文件动态上传更新提示词，无需重启服务。

**本地化模型部署：** SentenceTransformer 采用本地绝对路径加载（`pretrained_model/` 目录），向量化全程不依赖外部 API，保障实验数据隐私安全。

**自动运维机制：** 三条守护线程分别负责总结生成、聊天记录清理（48h）、日志文件清理（5MB 上限），系统可长期无人值守稳定运行。

**代理人开关控制：** 管理员可通过接口对任意聊天室独立关闭元认知代理人（SSRL），关闭后该房间的后台总结线程跳过，满足不同实验条件的控制需求。

---
