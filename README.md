# Fitness AI Assistant

![CI](https://github.com/Sanery1/FitnessAssistant/actions/workflows/ci.yml/badge.svg)

一个基于 Claude AI 的智能健身助手，提供个性化训练计划、动作指导、营养建议等功能。

## 功能特性

- 训练计划生成 - 根据用户目标生成个性化训练计划
- 动作指导 - 提供健身动作的标准姿势和注意事项
- 营养建议 - 提供饮食和营养相关建议
- 进度追踪 - 记录和追踪用户的健身进度
- 身体数据管理 - 记录和分析身体数据

## 安装

```bash
pip install -r requirements.txt
```

## 配置

1. 复制 `.env.example` 为 `.env`
2. 填入你的 Anthropic API Key

## 运行

```bash
python -m src.main
```

## 测试

```bash
python tests/run_tests.py
```

项目采用阶段化交付流程，每个阶段完成后会自动执行 Git 提交与 GitHub 同步。
