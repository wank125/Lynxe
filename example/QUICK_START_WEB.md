# 快速启动 Web 监控界面

## 步骤 1: 启动后端服务

```bash
cd /Users/wangkai/sourceFromGit/Lynxe
mvn spring-boot:run
```

等待服务启动完成（看到 "Started LynxeApplication" 消息）

## 步骤 2: 打开浏览器

访问: `http://localhost:8080/task-monitor.html`

## 步骤 3: 运行示例任务

### 示例 1: simple-tool-test

1. 工具名称: `simple-tool-test`
2. 服务组: `test`
3. 参数:
```json
{
  "file_path": "/tmp/test.txt"
}
```
4. 点击 **"▶ 运行任务"**

### 示例 2: robust-file-processor

1. 工具名称: `robust-file-processor`
2. 服务组: `file-processing`
3. 参数:
```json
{
  "input_file": "/tmp/data.txt",
  "output_file": "/tmp/report.md"
}
```
4. 点击 **"▶ 运行任务"**

## 界面说明

- **🟢 绿色**: 已连接/完成
- **🔵 蓝色**: 运行中
- **🔴 红色**: 错误/停止
- **⚪ 灰色**: 未连接

## 停止任务

点击 **"⏹ 停止任务"** 按钮中断正在执行的任务。

## 技术支持

- 详细文档: [WEB_MONITOR_README.md](WEB_MONITOR_README.md)
- Python 版本: [TIMELINE_MONITOR_README.md](TIMELINE_MONITOR_README.md)
