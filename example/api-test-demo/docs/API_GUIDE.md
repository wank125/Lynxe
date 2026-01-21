# Lynxe API 使用指南

本文档详细介绍 Lynxe 系统的 API 接口使用方法。

## 基础信息

- **Base URL**: `http://localhost:18080`
- **Content-Type**: `application/json`

## 核心接口

### 1. 简单对话 (SSE 流式)

**端点**: `POST /api/executor/chat`

**请求**:
```json
{
  "input": "你好，请介绍一下你自己",
  "conversationId": "optional-conversation-id"
}
```

**响应** (SSE 流式):
```
data:{"type":"start"}
data:{"type":"chunk","content":"你好"}
data:{"type":"chunk","content":"！我是"}
data:{"type":"done"}
```

**示例**:
```bash
curl -s -N -X POST http://localhost:18080/api/executor/chat \
  -H "Content-Type: application/json" \
  -d '{"input": "你好"}'
```

---

### 2. 获取计划模板列表

**端点**: `GET /api/plan-template/list`

**响应**:
```json
{
  "templates": [
    {
      "id": "planTemplate-xxx",
      "title": "模板标题",
      "description": "模板描述",
      "createTime": "2026-01-21T13:51:08.777142",
      "updateTime": "2026-01-21T13:51:08.786201"
    }
  ],
  "count": 5
}
```

**示例**:
```bash
curl http://localhost:18080/api/plan-template/list
```

---

### 3. 异步执行任务

**端点**: `POST /api/executor/executeByToolNameAsync`

**请求**:
```json
{
  "toolName": "main-start-to-run",
  "serviceGroup": "example-userInteractive",
  "replacementParams": {
    "用户需求": "帮我写一个 Python Hello World"
  },
  "uploadedFiles": ["file1.pdf"],
  "uploadKey": "upload-xxx",
  "conversationId": "optional-conversation-id"
}
```

**响应**:
```json
{
  "planId": "plan-1769004459711",
  "status": "processing",
  "message": "Task submitted, processing",
  "conversationId": "conv-123",
  "toolName": "main-start-to-run",
  "planTemplateId": "planTemplate-xxx"
}
```

**参数说明**:
- `toolName`: 工具名称（必须先在前端发布为工具）
- `serviceGroup`: 服务分组
- `replacementParams`: 参数替换（用于替换 `<<param>>` 占位符）
- `uploadedFiles`: 上传的文件名列表（可选）
- `uploadKey`: 文件上传会话标识（可选）
- `conversationId`: 会话 ID（可选，用于记忆管理）

**示例**:
```bash
curl -X POST http://localhost:18080/api/executor/executeByToolNameAsync \
  -H "Content-Type: application/json" \
  -d '{
    "toolName": "main-start-to-run",
    "serviceGroup": "example-userInteractive",
    "replacementParams": {
      "用户需求": "今天天气怎么样？"
    }
  }'
```

---

### 4. 获取执行详情

**端点**: `GET /api/executor/details/{planId}`

**响应**:
```json
{
  "currentPlanId": "plan-xxx",
  "rootPlanId": "plan-xxx",
  "title": "任务标题",
  "status": "RUNNING",
  "completed": false,
  "summary": "执行摘要",
  "agentExecutionSequence": [
    {
      "stepId": "step-xxx",
      "agentName": "ConfigurableDynaAgent",
      "status": "RUNNING",
      "agentRequest": "代理请求内容"
    }
  ],
  "structureResult": "结构化结果"
}
```

**示例**:
```bash
curl http://localhost:18080/api/executor/details/plan-1769004459711
```

---

### 5. 获取步骤详情 (Think-Act 过程)

**端点**: `GET /api/executor/agent-execution/{stepId}`

**响应**:
```json
{
  "stepId": "step-xxx",
  "agentName": "ConfigurableDynaAgent",
  "status": "FINISHED",
  "agentRequest": "代理请求内容",
  "thinkActSteps": [
    {
      "thinkInput": "LLM 输入",
      "thinkOutput": "LLM 思考过程",
      "actToolInfoList": [
        {
          "name": "工具名称",
          "parameters": "工具参数",
          "result": "工具执行结果"
        }
      ]
    }
  ]
}
```

**示例**:
```bash
curl http://localhost:18080/api/executor/agent-execution/step-1769004459712_3734_57
```

---

### 6. 获取配置

**端点**: `GET /api/config/group/{groupName}`

**响应**:
```json
[
  {
    "id": 1,
    "configGroup": "lynxe",
    "configSubGroup": "browser",
    "configKey": "headless",
    "configValue": "true",
    "defaultValue": "false",
    "description": "配置描述",
    "inputType": "CHECKBOX"
  }
]
```

**示例**:
```bash
curl http://localhost:18080/api/config/group/lynxe
```

---

## Think-Act 模式说明

Lynxe 使用 Think-Act 模式执行任务：

1. **Think (思考)**: LLM 分析当前情况，决定下一步行动
2. **Act (行动)**: 调用工具执行具体操作
3. **循环**: 重复 Think-Act 直到任务完成

### Think-Act 记录结构

```json
{
  "thinkInput": "系统信息 + 当前步骤要求 + 历史记录",
  "thinkOutput": "LLM 的思考过程",
  "actToolInfoList": [
    {
      "name": "工具名称",
      "parameters": "工具参数",
      "result": "工具执行结果"
    }
  ]
}
```

---

## 实时跟踪任务执行

```bash
#!/bin/bash

PLAN_ID="plan-xxx"

while true; do
  # 获取执行详情
  DETAILS=$(curl -s "http://localhost:18080/api/executor/details/$PLAN_ID")

  # 检查状态
  STATUS=$(echo "$DETAILS" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
  COMPLETED=$(echo "$DETAILS" | grep -o '"completed":[^,}]*' | head -1 | cut -d':' -f2)

  echo "状态: $STATUS"

  # 获取所有步骤
  STEP_IDS=$(echo "$DETAILS" | grep -o '"stepId":"[^"]*"' | cut -d'"' -f4)

  for STEP_ID in $STEP_IDS; do
    # 获取步骤详情
    STEP_DETAIL=$(curl -s "http://localhost:18080/api/executor/agent-execution/$STEP_ID")

    # 显示 think 过程
    THINK_OUTPUT=$(echo "$STEP_DETAIL" | grep -o '"thinkOutput":"[^"]*"' | cut -d'"' -f4)
    echo "思考: $THINK_OUTPUT"
  done

  if [ "$COMPLETED" = "true" ]; then
    echo "任务完成！"
    break
  fi

  sleep 1
done
```

---

## 错误处理

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `Tool not found` | 工具未发布 | 在前端界面发布为工具 |
| `No static resource` | 端点不存在 | 检查 API 路径 |
| `Input message cannot be empty` | 参数为空 | 检查请求参数 |

---

## 相关文档

- [README-dev.md](../../README-dev.md) - 开发者快速入门
- [README.md](../README.md) - 测试案例说明
