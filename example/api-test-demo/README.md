# Lynxe API 测试案例

本目录包含 Lynxe 项目的完整 API 测试案例，演示如何调用各种接口并实时跟踪执行过程。

## 目录结构

```
api-test-demo/
├── scripts/
│   └── lynxe_test_case.sh      # 主测试脚本
├── output/
│   ├── execution_log.txt       # 执行日志
│   ├── think_process.txt       # Think 过程记录
│   ├── summary.txt             # 执行摘要
│   └── test_report.txt         # 测试报告
├── docs/
│   └── API_GUIDE.md            # API 使用指南
└── README.md                   # 本文件
```

## 快速开始

### 前置条件

确保 Lynxe Docker 容器正在运行：

```bash
docker ps | grep lynxe
```

### 运行测试

```bash
cd /Users/wangkai/sourceFromGit/Lynxe/example/api-test-demo

# 方式 1: 直接运行脚本
bash scripts/lynxe_test_case.sh

# 方式 2: 使用绝对路径
bash /Users/wangkai/sourceFromGit/Lynxe/example/api-test-demo/scripts/lynxe_test_case.sh
```

### 测试内容

测试脚本包含以下 4 个测试用例：

1. **简单对话测试** - 使用 SSE 流式响应
2. **获取计划模板列表** - 查看可用的计划模板
3. **异步任务执行并实时跟踪** - 完整的 Think-Act 过程跟踪
4. **获取系统配置** - 查看系统配置项

## API 端点说明

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/executor/chat` | POST | 简单对话 (SSE 流式) |
| `/api/plan-template/list` | GET | 获取计划模板列表 |
| `/api/executor/executeByToolNameAsync` | POST | 异步执行任务 |
| `/api/executor/details/{planId}` | GET | 获取执行详情 |
| `/api/executor/agent-execution/{stepId}` | GET | 获取步骤详情 (Think-Act) |
| `/api/config/group/{groupName}` | GET | 获取配置组 |

## 输出文件

测试运行后，会在 `output/` 目录下生成以下文件：

- **execution_log.txt**: 完整的执行日志，包含所有 API 调用和响应
- **think_process.txt**: LLM 的 Think 过程记录
- **summary.txt**: 任务执行的最终摘要
- **test_report.txt**: 测试报告汇总

## 示例输出

```
============================================
  Lynxe API 完整测试案例
============================================

--- 测试 1: 简单对话测试 (SSE 流式) ---
✓ 对话测试完成

--- 测试 2: 获取计划模板列表 ---
可用模板数量: 5
✓ 模板列表获取完成

--- 测试 3: 异步执行任务并实时跟踪 ---
任务已提交
  Plan ID: plan-1769004721560

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  步骤 1: ConfigurableDynaAgent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
状态: RUNNING
Think-Act 循环次数: 1

--- Round 1 ---
思考: 作为一个技术专家，我认为该问题...
行动: 调用工具 example-userInteractive-technical-expert-question-processor

✓ 任务完成！

--- 测试 4: 获取系统配置 ---
配置项数量: 26
✓ 配置获取完成

所有测试已完成！

输出文件位置:
  • 日志文件: /tmp/lynxe_test_output_XXX/execution_log.txt
  • Think 过程: /tmp/lynxe_test_output_XXX/think_process.txt
  • 执行摘要: /tmp/lynxe_test_output_XXX/summary.txt
```

## 常见问题

### Q: Docker 容器没有运行？
```bash
docker start lynxe
```

### Q: 端口不是 18080？
检查 Docker 容器端口映射：
```bash
docker ps | grep lynxe
```
然后修改脚本中的 `BASE_URL` 变量。

### Q: 任务执行超时？
增加脚本中的 `MAX_CHECKS` 变量值。

## 相关文档

- [README-dev.md](../../README-dev.md) - 开发者快速入门指南
- [docs/API_GUIDE.md](docs/API_GUIDE.md) - API 使用详细指南

## 更新日志

- 2026-01-21: 初始版本，包含完整的 API 测试案例
