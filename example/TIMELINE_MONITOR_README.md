# Lynxe 时间轴监控工具使用指南

## 概述

`timeline_monitor.py` 是一个用于监控和可视化 Lynxe Agent 执行过程的 Python 工具。它能够：

1. **调用 API 启动任务** - 通过工具名称启动新的执行任务
2. **实时监控执行过程** - 以时间轴方式显示执行进度
3. **显示异常和修复** - 高亮显示错误和恢复操作
4. **暴露思考过程** - 展示 LLM 的 Think-Act 记录
5. **生成多种格式报告** - 支持 Console、Markdown、HTML 输出

## 安装

### 依赖

```bash
pip install requests
```

### 位置

工具位于：`example/timeline_monitor.py`

## 使用方法

### 基本用法

```bash
# 进入 example 目录
cd example

# 查看帮助信息
python3 timeline_monitor.py --help
```

### 1. 启动新任务并监控

```bash
python3 timeline_monitor.py --execute simple-tool-test --params '{"file_path": "/tmp/test.txt"}'
```

### 2. 监控已有任务

```bash
python3 timeline_monitor.py --plan-id plan-xxx
```

### 3. 生成 Markdown 报告

```bash
python3 timeline_monitor.py --plan-id plan-xxx --output markdown --output-file report.md
```

### 4. 生成 HTML 报告

```bash
python3 timeline_monitor.py --plan-id plan-xxx --output html --output-file report.html
```

### 5. 不实时监控，直接获取结果

```bash
python3 timeline_monitor.py --plan-id plan-xxx --no-monitor
```

### 6. 指定服务器地址

```bash
python3 timeline_monitor.py --execute my-tool --server http://remote-server:8080
```

## 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--execute` | `-e` | 工具名称，启动新任务 | - |
| `--plan-id` | `-p` | 监控已有任务 ID | - |
| `--params` | - | 替换参数 (JSON 格式) | - |
| `--service-group` | `-g` | 服务组名称 | - |
| `--output` | `-o` | 输出格式 (console/markdown/html) | console |
| `--output-file` | `-f` | 输出到文件 | - |
| `--poll-interval` | - | 轮询间隔（秒） | 2.0 |
| `--no-monitor` | - | 不实时监控，直接获取结果 | - |
| `--server` | `-s` | 服务器地址 | http://localhost:8080 |

## 输出格式

### 1. Console 输出 (默认)

在终端直接显示 ASCII 风格的时间轴：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
00:00                                        10.0s
│
├─ Step 1: Read File ✅ (2.5s)
│   ├─ 💭: "Need to read the file first"
│   └─ 🔧: fs-read-file-operator → Success
│
├─ Step 2: Process Data ⚠️ (3.5s)
│   ├─ 💭: "Checking data format"
│   ├─ 🔧: error-report-tool → Error found
│   └─ 🔧: fs-replace-file-operator → Fixed
│
└─ Step 3: Generate Report ✅ (1.5s)
    └─ 🔧: fs-write-file-operator → Success
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 2. Markdown 报告

生成结构化的 Markdown 报告，包含：
- 执行概览
- ASCII 时间轴
- 详细步骤记录
- Think-Act 记录
- 工具调用详情

### 3. HTML 报告

生成交互式 HTML 报告，包含：
- 美观的样式设计
- 响应式布局
- 错误高亮显示
- 可折叠的详细信息

## 图标说明

| 图标 | 含义 |
|------|------|
| ✅ | 成功完成 |
| ❌ | 执行失败 |
| ⚠️ | 包含错误 |
| 🔄 | 运行中 |
| 💭 | 思考过程 (Think) |
| 🔧 | 工具调用 (Tool) |

## 错误分析

工具会自动检测和分析错误，提供：

1. **错误分类**
   - `file_not_found` - 文件不存在
   - `validation_error` - 验证错误
   - `timeout` - 超时
   - `permission_error` - 权限错误
   - `unknown_error` - 未知错误

2. **修复建议**
   - 根据错误类型提供针对性的修复建议

## 测试工具

使用测试脚本验证工具功能（不需要后端服务运行）：

```bash
python3 example/test_timeline_monitor.py
```

测试脚本会：
1. 使用模拟数据测试 ASCII 时间轴渲染
2. 生成完整的 Markdown 报告
3. 生成 HTML 报告
4. 测试错误分析功能
5. 保存所有输出到 `/tmp/` 目录

## 示例工作流

### 使用 robust-file-processor 工作流

```bash
# 确保后端服务正在运行
# 启动 Lynxe 后端服务

# 执行增强型文件处理工作流
python3 timeline_monitor.py --execute robust-file-processor \
  --params '{"input_file": "/tmp/data.txt", "output_file": "/tmp/report.md"}' \
  --service-group file-processing
```

## 常见问题

### 1. 连接失败

```
错误: 启动任务失败: HTTPConnectionPoolHost...
```

**解决方法**：
- 确认 Lynxe 后端服务正在运行
- 使用 `--server` 参数指定正确的服务器地址
- 检查防火墙设置

### 2. 任务不存在

```
❌ 任务 plan-xxx 不存在
```

**解决方法**：
- 确认 planId 正确
- 检查任务是否已被清理
- 使用 `GET /api/executor/taskStatus/{planId}` 验证

### 3. 无执行记录

```
📭 无执行记录
```

**解决方法**：
- 任务可能还在初始化中
- 等待几秒后重试
- 使用 `--no-monitor` 查看原始响应

## API 端点

工具使用以下 API 端点：

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/executor/executeByToolNameAsync` | 启动异步任务 |
| GET | `/api/executor/details/{planId}` | 获取执行详情 |
| GET | `/api/executor/taskStatus/{planId}` | 获取任务状态 |
| POST | `/api/executor/stopTask/{planId}` | 停止任务 |

## 扩展功能

### 自定义轮询间隔

```bash
# 每 5 秒轮询一次
python3 timeline_monitor.py --plan-id plan-xxx --poll-interval 5
```

### 输出到文件

```bash
# 生成报告并保存
python3 timeline_monitor.py --plan-id plan-xxx \
  --output markdown \
  --output-file my_report.md
```

## 与现有工具对比

| 功能 | analyze_timeline.py | timeline_monitor.py |
|------|-------------------|---------------------|
| API 调用 | ❌ | ✅ |
| 实时监控 | ❌ | ✅ |
| 启动任务 | ❌ | ✅ |
| ASCII 时间轴 | ✅ | ✅ |
| Markdown 报告 | ✅ | ✅ |
| HTML 报告 | ❌ | ✅ |
| 错误分析 | ❌ | ✅ |
| Think-Act 展示 | ✅ | ✅ |

## 贡献

如有问题或建议，请提交 Issue 或 Pull Request。
