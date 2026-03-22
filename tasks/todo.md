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

## Phase 4: 工作流编排 (待实现)

- [ ] 实现工作流系统 (workflow/)
  - [ ] state.py - 状态管理
  - [ ] nodes.py - 工作流节点
  - [ ] graph.py - 工作流图
  - [ ] executor.py - 执行引擎

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

- [ ] 测试与验证
  - [ ] 编写测试用例
  - [ ] 边缘情况验证
  - [ ] 运行演示

## Phase 8: 项目修复与运行 (当前进行中)

- [x] 环境准备与依赖安装
  - [x] 安装Python依赖包
  - [x] 验证GLM API密钥配置
  - [x] 创建必要的数据目录结构

- [ ] 配置修复
  - [ ] 检查并修复LLM客户端配置一致性
  - [ ] 验证API端点可达性
  - [ ] 测试基础LLM功能

- [ ] 功能测试
  - [ ] 运行单元测试套件
  - [ ] 测试各个工具模块
  - [ ] 验证智能体功能

- [ ] 服务启动
  - [ ] 启动FastAPI服务
  - [ ] 测试Web界面
  - [ ] 验证API端点

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