# FitnessAssistant 项目介绍（按 PDF 结构映射，基于仓库实证）

## 说明
本文档参考《峡谷智囊AI游戏助手.pdf》的叙事方式组织结构，但内容仅来自当前仓库中可验证的代码、配置与测试结果，不使用猜测性信息。

## 1. 项目定位
FitnessAssistant 是一个面向健身场景的多专家 AI 助手项目，目标是在同一套服务中提供训练建议、营养建议、身体数据分析与可持续会话能力。

项目当前运行形态：
- FastAPI 后端（路由位于 src/api/routes）
- 静态前端（static/index.html + static/js/app.js）
- 本地知识增强检索（src/knowledge/rag.py）
- 多层测试与 CI（tests/run_tests.py + .github/workflows/ci.yml）

## 2. 核心能力
### 2.1 多专家协同回答
- 主控编排：OrchestratorAgent 负责意图分类与路由。
- 专家角色：FitnessCoachAgent、NutritionistAgent、DataAnalystAgent。
- 多领域问题：当命中多个领域时，执行多专家协同并合并输出。

对应实现：src/agents/orchestrator.py

### 2.2 会话记忆与用户长期数据
- 短期记忆：保存当前会话消息、上下文窗口。
- 长期记忆：保存用户画像、训练记录、身体数据历史。
- 会话隔离：chat 路由按 user_id 维护独立 MemoryManager 与 Orchestrator 实例。

对应实现：
- src/memory/manager.py
- src/api/routes/chat.py

### 2.3 工具系统与业务能力封装
- 工具注册中心可统一暴露可调用能力。
- 能力覆盖训练、营养、身体指标计算等场景。
- 对外提供 /api/chat/tools 列出可用工具。

对应实现：
- src/tools/
- src/api/routes/chat.py

### 2.4 知识库增强检索（RAG）
- 使用本地向量化与检索流程（SimpleEmbedding + VectorStore）。
- 在 chat stream 场景中，先检索上下文，再注入系统提示增强回答。
- 首次初始化时会自动构建基础健身知识文档。

对应实现：
- src/knowledge/rag.py
- src/api/routes/chat.py

### 2.5 API 交互模式
- 标准问答接口：POST /api/chat/message
- 流式接口：POST /api/chat/stream（SSE）
- 历史查询与清理：GET/DELETE /api/chat/history/{user_id}
- 业务 API：user/workout/nutrition/body 多路由。

对应目录：src/api/routes/

## 3. 关键设计与实现方案（映射 PDF 的“设计难点”章节）
### 3.1 难点一：多用户会话状态隔离
问题本质：如果只用单例会话容器，容易出现串话、历史错读或上下文污染。

当前方案：
- 以 user_id 为键维护 _memory_managers 与 _orchestrators。
- 首次访问时惰性创建，后续同 user_id 复用。
- 消息处理后写回短期记忆，保证同用户上下文连续。

实现位置：src/api/routes/chat.py

### 3.2 难点二：同步 Agent 处理与异步 Web 框架兼容
问题本质：Agent process 是同步实现，FastAPI 路由是异步协程。

当前方案：
- 在 chat_message 中使用 asyncio.to_thread 包装 orchestrator.process，避免阻塞事件循环。

实现位置：src/api/routes/chat.py

### 3.3 难点三：知识增强与纯模型回答的平衡
问题本质：仅依赖模型易忽略领域事实，仅依赖检索又可能在未命中时表现生硬。

当前方案：
- stream 路由先调用 knowledge.get_context(request.message)。
- 将检索结果拼接到 system_prompt 后再流式生成。
- 当检索为空时依然可继续模型回答，不会中断会话。

实现位置：
- src/knowledge/rag.py
- src/api/routes/chat.py

### 3.4 难点四：可验证交付与回归稳定性
问题本质：仅“能跑”不足以保证改动可持续，必须有可重复验证链路。

当前方案：
- 建立统一测试入口 tests/run_tests.py。
- 覆盖工具、LLM 客户端、Memory、Workflow、Chat、API 集成、API 异常路径、性能基线。
- 通过 GitHub Actions 在 push/PR 自动执行测试。

对应文件：
- tests/run_tests.py
- .github/workflows/ci.yml

## 4. 架构分层（工程视角）
- Agent 层：负责任务理解、意图路由、多专家协同。
- Tool 层：封装业务动作和计算逻辑，供 Agent 调用。
- Memory 层：短期会话 + 长期用户数据。
- Knowledge 层：检索增强上下文构建。
- Workflow 层：状态、节点、图和执行器机制。
- API 层：统一对外暴露 HTTP 与 SSE。

## 5. 运行与验证结果（.venv 实测）
### 5.1 全量测试
执行环境：D:/Code/Project/FitnessAssitant/.venv

执行命令：
- d:/Code/Project/FitnessAssitant/.venv/Scripts/python.exe tests/run_tests.py

结果：通过。

### 5.2 服务健康检查
启动命令：
- d:/Code/Project/FitnessAssitant/.venv/Scripts/python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8010

检查端点：
- /health

响应：
- {"status":"ok","version":"0.1.0"}

结论：项目在指定 .venv 环境可启动、可测试、可对外提供 API 服务。

## 6. PDF 框架映射说明
本文件已按 PDF 的表达逻辑进行映射：
- PDF 的“项目定位” -> 本文第 1 章
- PDF 的“核心能力” -> 本文第 2 章
- PDF 的“设计难点与实现方案” -> 本文第 3 章
- PDF 的“系统架构与流程” -> 本文第 4 章
- PDF 的“可运行性验证” -> 本文第 5 章

差异说明：
- PDF 原文强调游戏角色人格、阵容和出装链路。
- 本项目对应为健身场景的多专家协同、工具与知识增强链路。

## 7. 边界与事实约束
- 文档所有结论均可在仓库文件中定位。
- 未引入仓库外产品指标、用户量、线上 SLA 等不可证实数据。
- 如需进一步对齐 PDF 的版式粒度（例如逐页标题映射），可在现有结构上继续细分章节。 
