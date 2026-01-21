# Lynxe Web 实时监控工具

## 概述

Lynxe Web 实时监控工具是一个基于 **SSE (Server-Sent Events)** 的 Web 界面，用于实时监控 Agent 任务执行过程。

## 新增功能

### 1. 后端 SSE 端点

**位置**: [LynxeController.java:1572](src/main/java/com/alibaba/cloud/ai/lynxe/runtime/controller/LynxeController.java#L1572)

**端点**: `GET /api/executor/stream/{planId}`

**功能**:
- 实时推送任务执行进度
- 每 1 秒轮询一次状态变化
- 仅在有新步骤或状态变化时推送数据
- 支持长连接（5 分钟超时）

**SSE 事件类型**:

| 事件类型 | 说明 |
|---------|------|
| `connected` | 连接建立成功 |
| `progress` | 执行进度更新（包含新步骤） |
| `done` | 任务完成 |
| `error` | 错误信息 |

### 2. Web 前端界面

**位置**: [task-monitor.html](src/main/resources/static/task-monitor.html)

**访问地址**: `http://localhost:8080/task-monitor.html`

## 使用方法

### 启动后端服务

确保 Lynxe 后端服务正在运行：

```bash
# 在项目根目录
mvn spring-boot:run
```

### 访问 Web 界面

1. 打开浏览器访问: `http://localhost:8080/task-monitor.html`

2. 填写表单:
   - **工具名称**: 要执行的工具（如 `simple-tool-test`）
   - **服务组** (可选): 服务组名称（如 `test`）
   - **参数** (JSON 格式): 工具参数

3. 点击 **"▶ 运行任务"** 按钮

4. 实时查看执行时间轴:
   - 状态指示器显示当前连接状态
   - 进度条显示执行进度
   - 时间轴实时更新每个步骤
   - 显示 Think-Act 循环详情
   - 工具调用状态（成功/失败）

### 示例配置

**simple-tool-test**:
```json
{
  "file_path": "/tmp/test.txt"
}
```

**robust-file-processor**:
```json
{
  "input_file": "/tmp/data.txt",
  "output_file": "/tmp/report.md"
}
```

## 界面功能

### 控制面板
- 输入工具名称和参数
- 启动/停止任务按钮
- 表单验证

### 状态栏
- 连接状态指示器（灰色=未连接，蓝色=运行中，绿色=完成，红色=错误）
- 状态文本消息
- Plan ID 显示

### 时间轴
- 实时更新的步骤列表
- 每个步骤显示:
  - 步骤名称和 ID
  - 执行时长
  - Think-Act 循环详情
  - 工具调用列表
- 状态图标:
  - ✅ 成功
  - ⚠️ 有错误
  - ❌ 失败

### 进度追踪
- 步骤计数器
- 可视化进度条

## API 规范

### 启动任务

```http
POST /api/executor/executeByToolNameAsync
Content-Type: application/json

{
  "toolName": "simple-tool-test",
  "replacementParams": {
    "file_path": "/tmp/test.txt"
  },
  "serviceGroup": "test"
}
```

**响应**:
```json
{
  "planId": "plan-xxx",
  "status": "processing",
  "message": "Task submitted, processing"
}
```

### SSE 流

```http
GET /api/executor/stream/{planId}
Accept: text/event-stream
```

**事件数据示例**:

```javascript
// 连接事件
data: {"type":"connected","planId":"plan-xxx"}

// 进度更新
data: {"type":"progress","planId":"plan-xxx","stepCount":1,"newSteps":[...]}

// 完成事件
data: {"type":"done","planId":"plan-xxx","finalResult":"..."}

// 错误事件
data: {"type":"error","message":"Plan not found"}
```

### 停止任务

```http
POST /api/executor/stopTask/{planId}
```

## 与 Python 工具对比

| 功能 | Python 工具 | Web 界面 |
|------|------------|----------|
| API 调用 | ✅ | ✅ |
| 实时监控 | ✅ 轮询 | ✅ SSE 推送 |
| 启动任务 | ✅ | ✅ |
| 进度可视化 | ✅ 终端 | ✅ Web UI |
| 时间轴显示 | ✅ | ✅ |
| Think-Act 展示 | ✅ | ✅ |
| 交互式控制 | ❌ | ✅ |
| 浏览器访问 | ❌ | ✅ |
| 报告导出 | ✅ MD/HTML | ❌ |

## 技术架构

### 后端
- **Spring Boot SSE**: 使用 `SseEmitter` 实现服务端推送
- **异步轮询**: 每秒轮询执行状态变化
- **变化检测**: 仅在有新数据时推送，减少网络流量

### 前端
- **原生 JavaScript**: 无需框架依赖
- **EventSource API**: 标准 SSE 客户端
- **响应式设计**: 适配不同屏幕尺寸
- **实时渲染**: DOM 动态更新

## 故障排除

### 连接失败

**症状**: SSE 连接无法建立

**解决方法**:
1. 确认后端服务正在运行
2. 检查浏览器控制台错误
3. 确认防火墙设置

### 任务不存在

**症状**: 显示 "Plan not found" 错误

**解决方法**:
1. 确认 planId 正确
2. 检查任务是否已被清理
3. 使用 `GET /api/executor/details/{planId}` 验证

### 进度不更新

**症状**: 时间轴没有新步骤出现

**解决方法**:
1. 检查后端日志确认任务在执行
2. 确认 SSE 连接仍然活跃
3. 刷新页面重新连接

## 开发说明

### 添加新工具

1. 创建工具配置 JSON（参考 [robust-file-processor.json](robust-file-processor.json)）
2. 在 Web 界面输入工具名称
3. 提供必要的参数

### 自定义样式

修改 [task-monitor.html](src/main/resources/static/task-monitor.html) 中的 CSS:

```css
/* 主题颜色 */
body {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

/* 状态指示器颜色 */
.status-indicator.connected {
    background: #22c55e;
}
```

### 扩展功能

可以添加的功能:
- 保存历史记录
- 导出报告
- 批量执行
- 更多可视化选项
- WebSocket 替代 SSE（双向通信）

## 许可

Apache License 2.0
