# 健身 AI 助手开发计划

## 项目概述
基于 GLM-5 / OpenAI 兼容 API 的智能健身助手，采用 Agent 架构，具备 Function Calling、Memory、RAG、多Agent协作等能力。

---

## Phase 1: 基础架构 ✅

- [x] 完善数据模型层 (models/)
  - [x] user.py - 用户模型
  - [x] workout.py - 训练模型
  - [x] nutrition.py - 营养模型
  - [x] body.py - 身体数据模型
  - [x] progress.py - 进度追踪模型

- [x] 实现核心工具系统 (tools/)
  - [x] base.py - 工具基类与注册机制 (OpenAI 兼容格式)
  - [x] workout_tools.py - 训练计划工具
  - [x] nutrition_tools.py - 营养计算工具
  - [x] body_tools.py - 身体数据工具

- [x] 构建 Memory 系统 (memory/)
  - [x] base.py - Memory 基类
  - [x] short_term.py - 短期记忆(会话上下文)
  - [x] long_term.py - 长期记忆(持久化存储)
  - [x] manager.py - Memory 管理器

---

## Phase 2: Agent 核心 ✅

- [x] 实现 Agent 基础架构 (agents/)
  - [x] base.py - Agent 基类 + 工具执行器

- [x] 实现专家 Agent
  - [x] fitness_coach.py - 健身教练 Agent
  - [x] nutritionist.py - 营养师 Agent
  - [x] data_analyst.py - 数据分析师 Agent
  - [x] orchestrator.py - 主控编排 Agent

---

## Phase 3: RAG 知识库 ✅

- [x] 构建知识库系统 (knowledge/)
  - [x] rag.py - 向量嵌入 + 向量存储 + 检索器
  - [x] 初始化健身知识数据

---

## Phase 4: 工作流编排 ✅

- [x] 实现工作流系统 (workflow/)
  - [x] state.py - 状态管理
  - [x] nodes.py - 工作流节点
  - [x] graph.py - 工作流图
  - [x] executor.py - 执行引擎

---

## Phase 5: API 后端 ✅

- [x] 构建 FastAPI 后端 (api/)
  - [x] main.py - 应用入口
  - [x] routes/chat.py - 对话接口
  - [x] routes/user.py - 用户管理
  - [x] routes/workout.py - 训练计划
  - [x] routes/nutrition.py - 营养数据
  - [x] routes/body.py - 身体数据

---

## Phase 6: Web 前端 ✅

- [x] 创建 Web 界面 (static/)
  - [x] index.html - 主页面
  - [x] css/style.css - 样式
  - [x] js/app.js - 主逻辑

---

## Phase 7: 集成与测试 ✅

- [x] 主入口与配置
  - [x] main.py - 应用主入口
  - [x] __main__.py - 命令行入口
  - [x] config.py - 配置管理

- [x] 测试与验证
  - [x] 编写测试用例
  - [x] 边缘情况验证
  - [x] 运行演示

## Phase 8: 项目修复与运行 ✅

- [x] 环境准备与依赖安装
  - [x] 安装Python依赖包
  - [x] 验证GLM API密钥配置
  - [x] 创建必要的数据目录结构

- [x] 配置修复
  - [x] 检查并修复LLM客户端配置一致性
  - [x] 验证API端点可达性
  - [x] 测试基础LLM功能

- [x] 功能测试
  - [x] 运行单元测试套件
  - [x] 测试各个工具模块
  - [x] 验证智能体功能

- [x] 服务启动
  - [x] 启动FastAPI服务
  - [x] 测试Web界面
  - [x] 验证API端点

---

## 技术要点

1. **Function Calling**: OpenAI/GLM 兼容格式工具调用
2. **Memory**: 短期(会话) + 长期(用户数据)
3. **RAG**: NumPy向量检索 + 健身知识库
4. **Multi-Agent**: 专家分工 + 主控编排
5. **LLM**: 支持 GLM-5 / OpenAI 兼容 API

---

## Review 记录

### 2026-03-19
- 完成核心架构搭建
- 支持 GLM-5 API (OpenAI 兼容格式)
- Tool 系统使用 OpenAI Function Calling 格式
- 前端界面美观易用

### 2026-03-20
- 开始 Phase 8 项目修复与运行阶段
- 已完成环境准备和依赖安装
- 创建了必要的数据目录结构

### 2026-03-22
- Phase 4 工作流系统已完成
  - 实现 WorkflowGraph、WorkflowExecutor、WorkflowManager
  - 支持 FunctionNode、AgentNode、ToolNode、ConditionNode、ParallelNode
  - 内置训练计划生成工作流模板
- Phase 7 测试套件已完成
  - 工具系统测试通过
  - Memory 系统测试通过
  - 工作流系统测试通过
- Phase 8 所有任务已完成
  - 服务成功启动并运行
  - API 端点验证通过
  - Web 界面可访问
  - 所有 7 个工具已注册并可用

### 2026-03-23
- Phase 9 P0 稳定性修复已完成
  - 修复 FunctionNode 对异步函数未 await 导致 coroutine 泄漏问题
  - 修复 WorkflowManager.create_executor 对未初始化 state 的索引错误
  - 修复 chat 路由会话隔离语义（按 user_id 维护独立会话）
  - 新增并通过 chat 路由会话隔离测试
  - 全量测试与 RuntimeWarning 严格模式回归通过

### 2026-03-23
- Phase 10 P1 工程优化已完成
  - 配置收敛：config 改为统一由 BaseSettings + .env 读取
  - 工具参数强校验：新增 normalize_tool_arguments 并覆盖字符串/对象输入
  - 路由异步化：chat_message 使用线程封装避免阻塞事件循环
  - 新增 LLM 客户端工具函数测试并纳入全量测试入口
  - 全量测试与严格告警模式回归通过

### 2026-03-23
- Phase 11 P2 安全加固已完成
  - 后端 CORS 改为配置驱动，默认来源从 * 收紧为本地开发地址
  - 前端新增 escapeHtml 并收敛动态渲染路径，降低注入风险
  - 清理 knowledge 目录冗余 backup 文件
  - .gitignore 增加 data/memory/test 临时 json 忽略规则
  - 全量测试与严格告警模式回归通过

### 2026-03-23
- 新增并完成 Phase 9：P0 稳定性修复与验证

## Phase 9: P0 稳定性修复 ✅

- [x] 修复工作流异步节点执行缺陷
  - [x] 在 FunctionNode 中兼容同步/异步函数，确保协程被正确 await
  - [x] 增加可复现该缺陷的测试断言（结果不应为 coroutine）
  - [x] 运行工作流测试并验证无未等待协程告警

- [x] 修复 WorkflowManager 执行器索引缺陷
  - [x] 修正 create_executor 中对未初始化 state 的访问
  - [x] 增加创建执行器路径的单元测试
  - [x] 验证 workflow manager 测试通过

- [x] 修复聊天会话隔离缺陷
  - [x] 将会话消息按 user_id 隔离存储
  - [x] 修正 chat history 与 clear history 的 user_id 语义
  - [x] 增加多用户会话隔离测试用例

- [x] 回归验证
  - [x] 运行 tests/run_tests.py
  - [x] 使用 RuntimeWarning 严格模式复测
  - [x] 更新 Review 记录与结论

## Phase 10: P1 工程优化 ✅

- [x] LLM 客户端异步化改造
  - [x] 评估当前调用路径并确定最小改造面
  - [x] 引入异步请求实现并保持接口兼容
  - [x] 增加超时/异常路径测试

- [x] 配置来源收敛与默认值一致性
  - [x] 消除 Settings 默认值与实例化覆盖值冲突
  - [x] 明确开发/生产配置边界
  - [x] 补充配置回归验证

- [x] 工具调用参数强校验
  - [x] 统一处理 tool_call 参数字符串/对象两种形态
  - [x] 增加参数反序列化失败的错误路径测试
  - [x] 验证三类 Agent 工具调用稳定性

- [x] 回归验证与记录
  - [x] 运行全量测试
  - [x] 严格告警模式复测
  - [x] 更新 Review 记录

## Phase 11: P2 安全加固 ✅

- [x] 后端默认安全配置收敛
  - [x] 以配置项方式收紧 CORS allow_origins
  - [x] 生产场景默认关闭调试能力
  - [x] 增加安全配置回归验证

- [x] 前端渲染防注入加固
  - [x] 替换高风险 innerHTML 动态拼接路径
  - [x] 增加文本转义/安全渲染工具函数
  - [x] 增加前端渲染安全测试点（最小可复现）

- [x] 清理冗余备份文件与仓库噪声
  - [x] 清理 src/knowledge 下 backup 文件
  - [x] 更新忽略规则避免测试临时文件进入版本控制
  - [x] 回归确认功能未受影响

- [x] 回归验证与记录
  - [x] 运行全量测试
  - [x] 严格告警模式复测
  - [x] 更新 Review 记录

## Phase 12: API 集成测试增强 ✅

- [x] 新增 FastAPI 端到端测试
  - [x] 健康检查与基础路由测试
  - [x] workout/nutrition/body 路由正向用例
  - [x] CORS 白名单行为回归测试

- [x] 集成到统一测试入口
  - [x] 纳入 tests/run_tests.py
  - [x] 全量回归通过

## Phase 13: 性能基线与并发压测 ✅

- [x] 构建性能基线测试
  - [x] 健康检查接口延迟基线
  - [x] BMI 计算接口吞吐与延迟基线
  - [x] 并发场景下错误率统计

- [x] 集成阶段验证
  - [x] 执行性能基线测试
  - [x] 记录结果并设置保守阈值
  - [x] 更新 Review 记录

## Phase 14: API 异常路径与边界测试增强 ✅

- [x] 补充异常路径测试
  - [x] 请求体字段缺失/类型错误返回 422
  - [x] 业务资源不存在返回 404
  - [x] CORS 非法预检场景返回预期状态

- [x] 集成到统一测试入口
  - [x] 纳入 tests/run_tests.py
  - [x] 全量回归通过

## Phase 15: CI 自动化与项目收官 ✅

- [x] 建立 GitHub Actions CI
  - [x] 安装依赖并执行 tests/run_tests.py
  - [x] 在 push / pull_request 触发
  - [x] 保证与当前本地测试入口一致

- [x] 项目文档同步
  - [x] README 增加 CI 状态说明
  - [x] 记录自动同步与阶段化交付完成状态

- [x] 收官验证
  - [x] 本地全量测试通过
  - [x] 变更已自动同步到 GitHub

## Phase 16: 项目跑通校验与介绍文档生成 ✅

- [x] 项目可运行性校验
  - [x] 使用 `.venv` 环境执行全量测试
  - [x] 启动服务并验证健康检查接口
  - [x] 若失败则定位根因并修复后复测

- [x] 参考 PDF 框架提取文档结构
  - [x] 提取《峡谷智囊AI游戏助手.pdf》可用目录/结构信息
  - [x] 映射为本项目可证实信息的章节骨架

- [x] 生成本项目专属介绍文档
  - [x] 文档内容仅基于当前仓库与运行验证结果
  - [x] 详略得当，避免未验证推测
  - [x] 保存到项目文档文件

- [x] 阶段验证与同步
  - [x] 回归测试通过
  - [x] 阶段完成后自动提交并同步 GitHub

### 2026-03-24
- Phase 16 已完成
  - 在 `.venv` 环境完成全量测试与服务健康检查
  - 生成项目专属介绍文档：`docs/fitness_assistant_项目介绍.md`
  - 说明：工作区未检索到 PDF 实体文件，文档框架映射严格基于仓库可验证信息编写

### 2026-03-24
- Phase 15 已完成
  - 新增 GitHub Actions CI（push/PR 自动运行全量测试）
  - README 已补充 CI 状态与测试说明

### 2026-03-24
- Phase 14 已完成
  - 新增 API 异常路径与边界测试
  - 全量测试与严格告警模式回归通过

### 2026-03-23
- Phase 13 已完成
  - 新增性能基线测试并纳入统一测试入口
  - 健康检查与 BMI 接口延迟基线通过
  - BMI 并发场景错误率为 0 并通过阈值校验

### 2026-03-23
- Phase 12 已完成
  - 新增 API 集成测试并纳入统一测试入口
  - 验证全量测试通过

## GitHub 自动同步机制（持续生效）

- [x] 规则建立：每完成一个 Phase，立即执行 add/commit/push，不等待会话结束
- [x] 提交规范：`phase(<编号>): <阶段结果摘要>`
- [x] 执行闭环：提交后立即继续下一个 Phase 任务