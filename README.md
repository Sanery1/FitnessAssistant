# Fitness AI Assistant

![CI](https://github.com/Sanery1/FitnessAssistant/actions/workflows/ci.yml/badge.svg)

一个基于 GLM/OpenAI 兼容 API 的智能健身助手，采用多 Agent 架构，提供个性化训练计划、动作指导、营养建议、进度追踪等功能。

## 功能特性

- **训练计划生成** - 根据用户目标生成个性化训练计划
- **动作指导** - 提供健身动作的标准姿势和注意事项
- **营养建议** - 提供饮食和营养相关建议
- **进度追踪** - 记录和追踪用户的健身进度
- **身体数据管理** - 记录和分析身体数据（BMI、体脂率等）
- **RAG 知识增强** - 本地健身知识库，检索增强回答质量
- **多 Agent 协同** - 健身教练、营养师、数据分析师多专家协作

## 安装

```bash
pip install -r requirements.txt
```

## 配置

1. 复制 `.env.example` 为 `.env`
2. 填入你的 API Key（支持 GLM / OpenAI 兼容接口）

## 运行

```bash
python -m src.main
```

服务启动后访问：
- Web 界面：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`

## 测试

```bash
python tests/run_tests.py
```

---

## 项目结构

```
FitnessAssistant/
├── src/                        # 核心源码
│   ├── main.py                 # FastAPI 应用入口，CORS、路由注册、启动事件
│   ├── config.py               # 统一配置（pydantic-settings + .env）
│   ├── __main__.py             # 命令行入口
│   │
│   ├── agents/                 # 多 Agent 架构
│   │   ├── base.py             # BaseAgent 基类、AgentRole/State 枚举、AgentResponse
│   │   ├── orchestrator.py     # OrchestratorAgent：意图分类 + 路由 + 多专家协调
│   │   ├── fitness_coach.py    # FitnessCoachAgent：训练计划与动作指导
│   │   ├── nutritionist.py     # NutritionistAgent：营养建议与热量计算
│   │   └── data_analyst.py     # DataAnalystAgent：数据分析与进度追踪
│   │
│   ├── tools/                  # Function Calling 工具系统
│   │   ├── base.py             # Tool 基类、ToolRegistry 单例、tool 装饰器
│   │   ├── workout_tools.py    # 训练工具：generate_workout_plan、get_exercise_info
│   │   ├── nutrition_tools.py  # 营养工具：calculate_calories、analyze_nutrition
│   │   └── body_tools.py       # 身体工具：calculate_bmi、calculate_body_fat
│   │
│   ├── memory/                 # 记忆系统
│   │   ├── base.py             # MemoryItem 基类
│   │   ├── short_term.py       # ShortTermMemory：会话消息 + 上下文窗口
│   │   ├── long_term.py        # LongTermMemory：JSON 文件持久化存储
│   │   └── manager.py          # MemoryManager：统一接口，整合短/长期记忆
│   │
│   ├── knowledge/              # RAG 知识增强
│   │   └── rag.py              # SimpleEmbedding、VectorStore、KnowledgeBase、内置知识初始化
│   │
│   ├── workflow/               # 工作流编排
│   │   ├── state.py            # WorkflowState：节点状态与全局数据
│   │   ├── nodes.py            # FunctionNode、AgentNode、ToolNode、ConditionNode、ParallelNode
│   │   ├── graph.py            # WorkflowGraph：DAG 建模 + 拓扑排序 + 内置训练计划工作流模板
│   │   └── executor.py         # WorkflowExecutor、WorkflowManager：执行引擎
│   │
│   ├── api/                    # HTTP API 层
│   │   └── routes/
│   │       ├── chat.py         # POST /message（asyncio.to_thread）、SSE /stream、/history
│   │       ├── user.py         # 用户管理 CRUD
│   │       ├── workout.py      # 训练计划 CRUD
│   │       ├── nutrition.py    # 营养数据接口
│   │       └── body.py         # 身体数据接口（BMI、体脂等）
│   │
│   ├── services/
│   │   └── llm_client.py       # LLM 客户端（GLM/OpenAI 兼容，支持 httpx 异步）
│   │
│   └── models/                 # Pydantic 数据模型
│       ├── user.py             # 用户画像模型
│       ├── workout.py          # 训练记录模型
│       ├── nutrition.py        # 营养数据模型
│       ├── body.py             # 身体指标模型
│       └── progress.py         # 进度追踪模型
│
├── static/                     # Web 前端（单页应用）
│   ├── index.html              # 主页面
│   ├── css/style.css           # 样式
│   └── js/app.js               # 前端逻辑（escapeHtml 防注入）
│
├── data/                       # 运行时数据目录
│   ├── knowledge/              # 知识库向量索引（index.json、vectors.json）
│   └── memory/                 # 用户长期记忆 JSON 文件
│
├── tests/                      # 测试套件
│   ├── run_tests.py            # 统一测试入口
│   ├── test_tools.py           # 工具层单元测试
│   ├── test_memory.py          # 记忆系统测试
│   ├── test_workflow.py        # 工作流测试
│   ├── test_chat.py            # 聊天路由测试（含多用户会话隔离）
│   ├── test_llm_client.py      # LLM 客户端测试
│   ├── test_api_integration.py # FastAPI 端到端集成测试
│   ├── test_api_edge_cases.py  # API 边界与异常路径测试
│   └── test_performance_baseline.py  # 性能基线与并发压测
│
├── docs/
│   └── fitness_assistant_项目介绍.md  # 项目详细介绍文档
│
├── tasks/
│   ├── todo.md                 # 开发计划与阶段进度
│   └── lessons.md              # 开发教训记录
│
├── .github/
│   └── workflows/ci.yml        # GitHub Actions CI（push/PR 自动测试）
│
├── requirements.txt            # Python 依赖
├── .env.example                # 环境变量模板
└── CLAUDE.md                   # AI 助手工作规范
```

## 架构概览

```
用户请求
    │
    ▼
FastAPI (src/main.py)
    │  CORS / 路由分发
    ▼
API Routes (src/api/routes/)
    │  chat / user / workout / nutrition / body
    │
    ├─── Knowledge (RAG)          ← 检索健身知识，注入 system prompt
    │
    ├─── MemoryManager            ← 短期会话 + 长期用户数据（按 user_id 隔离）
    │
    └─── OrchestratorAgent        ← 意图分类 + 路由
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
FitnessCoach  Nutritionist  DataAnalyst
    │              │              │
    └──────────────┴──────────────┘
              │
         ToolRegistry              ← Function Calling 工具注册中心
         (workout / nutrition / body tools)
              │
         LLM Client (GLM / OpenAI)
```

## 技术栈

| 层次 | 技术 |
|------|------|
| Web 框架 | FastAPI + uvicorn |
| LLM | GLM / OpenAI 兼容模型（默认 glm-4-plus，可通过配置切换） |
| 数据模型 | Pydantic v2 |
| 配置管理 | pydantic-settings + python-dotenv |
| HTTP 客户端 | httpx（异步） |
| 向量检索 | NumPy（轻量本地实现） |
| 持久化 | JSON 文件（memory / knowledge） |
| 测试 | Python unittest |
| CI | GitHub Actions |

项目采用阶段化交付流程，每个阶段完成后会自动执行 Git 提交与 GitHub 同步。
