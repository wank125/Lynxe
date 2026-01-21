# Lynxe 内置工具列表

根据之前成功获取到的工具列表，以下是 Lynxe 系统中所有可用的内置工具：

## 工具分类概览

| 服务组 (serviceGroup) | 工具数量 | 说明 |
|---------------------|----------|------|
| `default` | 5 | 默认工具（终止、调试、bash、表单输入等） |
| `fs` | 10 | 文件系统操作（读写、搜索、分割等） |
| `fs-ext` | 8 | 外部链接文件操作 |
| `bw` | 9 | 浏览器自动化 |
| `db-service` | 6 | 数据库操作 |
| `parallel` | 4 | 并行执行 |
| `import-export` | 2 | 文档转换（Markdown、DOCX） |
| `image` | 1 | AI 图像生成 |
| `internal` | 1 | 内部思考工具 |
| `example-userInteractive` | 4 | 示例用户交互工具 |
| `customer-service-v2` | 6 | 智能客服工具 |

---

## 详细工具列表

### 1. default (默认工具)

| 工具 Key | 工具名称 | 描述 |
|----------|----------|------|
| `default-terminate` | terminate | 终止当前执行步骤并返回结构化数据 |
| `default-debug` | debug | 输出调试消息，用于记录执行过程 |
| `default-bash` | bash | 在终端中执行 bash 命令，支持交互式操作 |
| `default-form-input` | form-input | 创建交互式表单以收集用户输入 |
| `default-Default User Input Processing` | Default User Input Processing | 默认用户输入计划 |

### 2. fs (文件系统操作)

| 工具 Key | 工具名称 | 描述 |
|----------|----------|------|
| `fs-read-file-operator` | read-file-operator | 从本地文件系统读取文件内容 |
| `fs-write-file-operator` | write-file-operator | 创建新文件或完全覆盖现有文件 |
| `fs-replace-file-operator` | replace-file-operator | 在现有文件中执行精确字符串替换 |
| `fs-delete-file-operator` | delete-file-operator | 从本地文件系统删除现有文件 |
| `fs-list-files` | list-files | 列出本地文件系统中的文件和目录 |
| `fs-glob-files` | glob-files | 查找匹配 glob 模式的文件 |
| `fs-grep-files` | grep-files | 基于 ripgrep 的强大文本搜索工具 |
| `fs-count-file` | count-file | 统计文件的总行数和字符数 |
| `fs-split-file` | split-file | 将文本文件拆分为更小的片段 |

### 3. fs-ext (外部链接文件操作)

| 工具 Key | 工具名称 | 描述 |
|----------|----------|------|
| `fs-ext-read-external-link-file-operator` | read-external-link-file-operator | 从外部链接目录读取文件内容 |
| `fs-ext-write-external-link-file-operator` | write-external-link-file-operator | 在外部链接目录中创建或覆盖文件 |
| `fs-ext-replace-external-link-file-operator` | replace-external-link-file-operator | 在外部链接文件中执行字符串替换 |
| `fs-ext-delete-external-link-file-operator` | delete-external-link-file-operator | 从外部链接目录删除文件 |
| `fs-ext-list-external-link-files` | list-external-link-files | 列出外部链接目录中的文件和目录 |
| `fs-ext-glob-external-link-files` | glob-external-link-files | 在外部链接目录中查找匹配 glob 模式的文件 |
| `fs-ext-grep-external-link-files` | grep-external-link-files | 在外部链接目录中进行文本搜索 |
| `fs-ext-count-external-link-file` | count-external-link-file | 统计外部链接文件的行数和字符数 |
| `fs-ext-split-external-link-file` | split-external-link-file | 将外部链接文件拆分为更小的片段 |

### 4. bw (浏览器自动化)

| 工具 Key | 工具名称 | 描述 |
|----------|----------|------|
| `bw-navigate-browser` | navigate-browser | 在浏览器中访问特定 URL |
| `bw-new-tab-browser` | new-tab-browser | 使用指定 URL 打开新标签页 |
| `bw-close-tab-browser` | close-tab-browser | 关闭指定标签页 |
| `bw-switch-tab-browser` | switch-tab-browser | 切换到特定标签页 |
| `bw-click-browser` | click-browser | 按索引点击元素 |
| `bw-input-text-browser` | input-text-browser | 在元素中输入文本 |
| `bw-key-enter-browser` | key-enter-browser | 在元素上按 Enter 键 |
| `bw-screenshot-browser` | screenshot-browser | 捕获当前页面的截图 |
| `bw-get-web-content-browser` | get-web-content-browser | 获取当前页面的 ARIA 快照内容 |
| `bw-download-browser` | download-browser | 点击下载链接并保存文件 |

### 5. db-service (数据库操作)

| 工具 Key | 工具名称 | 描述 |
|----------|----------|------|
| `db-service-execute-read-sql` | execute-read-sql | 执行 SELECT 查询（只读操作） |
| `db-service-execute-write-sql` | execute-write-sql | 执行写入操作（INSERT、UPDATE、DELETE 等） |
| `db-service-get-table-meta` | get-table-meta | 获取表结构、字段和索引的元数据 |
| `db-service-get-datasource-info` | get-datasource-info | 获取数据源信息 |
| `db-service-database-table-to-excel` | database-table-to-excel | 将数据库表数据转换为 Excel 格式 |
| `db-service-uuid-generate` | uuid-generate | 生成 UUID（通用唯一标识符） |
| `db-service-execute-read-sql-to-json-file-tool` | execute-read-sql-to-json-file-tool | 执行 SELECT 查询并将结果保存到 JSON 文件 |

### 6. parallel (并行执行)

| 工具 Key | 工具名称 | 描述 |
|----------|----------|------|
| `parallel-register-batch-execution` | register-batch-execution | 并行注册多个不同工具的执行 |
| `parallel-start-parallel` | start-parallel | 启动所有注册函数的并行执行 |
| `parallel-clear-pending-execution` | clear-pending-execution | 清除所有待处理的函数 |
| `parallel-file-based-parallel-tool` | file-based-parallel-tool | 从文件读取 JSON 参数并执行指定工具 |

### 7. import-export (文档转换)

| 工具 Key | 工具名称 | 描述 |
|----------|----------|------|
| `import-export-markdown-converter` | markdown-converter | 将各种文件类型转换为 Markdown 格式 |
| `import-export-markdown-to-docx` | markdown-to-docx | 将 Markdown 文件转换为 DOCX 格式 |

### 8. image (图像)

| 工具 Key | 工具名称 | 描述 |
|----------|----------|------|
| `image-image-generate` | image-generate | 使用 AI 图像生成模型根据文本提示生成图像 |

### 9. internal (内部工具)

| 工具 Key | 工具名称 | 描述 |
|----------|----------|------|
| `internal-__think_internal__` | __think_internal__ | 内部思考工具（不可选） |

### 10. example-userInteractive (示例工具)

| 工具 Key | 工具名称 | 描述 |
|----------|----------|------|
| `example-userInteractive-main-start-to-run` | main-start-to-run | 路由方法 |
| `example-userInteractive-technical-expert-question-processor` | technical-expert-question-processor | 技术专家处理问题 |
| `example-userInteractive-business-expert-question-processor` | business-expert-question-processor | 业务专家处理问题 |
| `example-userInteractive-database-expert-question-processor` | database-expert-question-processor | 数据库专家处理问题 |

---

## 在 Func-Agent 中使用工具

在 `selectedToolKeys` 中引用工具时，使用完整的 `serviceGroup-toolName` 格式：

```json
{
  "selectedToolKeys": [
    "default-terminate",
    "fs-read-file-operator",
    "fs-grep-files",
    "db-service-execute-read-sql"
  ]
}
```

**注意**:
- 不要使用不存在的工具名称（如 `knowledge-base-search`）
- 如果需要自定义工具，需要先在系统中注册
- `internal-__think_internal__` 是内部工具，不应该手动添加
