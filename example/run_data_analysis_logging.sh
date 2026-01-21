#!/bin/bash

# run_data_analysis_logging.sh
# Executes the Data Analysis Workflow and generates a detailed timeline log.

echo "========================================="
echo "📊 Run Data Analysis & Generate Log"
echo "========================================="
echo ""

# 1. 确保模板已导入 (使用之前修复的版本)
echo "1. 刷新工作流模板..."
curl -s -X DELETE http://localhost:18080/api/plan-template/details/planTemplate-data-analysis-workflow > /dev/null
curl -s -X POST http://localhost:18080/api/plan-template/import-all \
  -H "Content-Type: application/json" \
  -d @example/multi-step-func-agent-examples.json > /dev/null
echo "✅ 模板已导入"
echo ""

# 2. 上传测试数据
echo "2. 上传测试数据 (sales_data.csv)..."
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:18080/api/file-upload/upload \
  -H "Content-Type: multipart/form-data" \
  -F "files=@example/test-data/sales_data.csv")

UPLOAD_KEY=$(echo $UPLOAD_RESPONSE | grep -o '"uploadKey":"[^"]*"' | cut -d'"' -f4)

if [ -n "$UPLOAD_KEY" ]; then
    echo "✅ 文件上传成功: $UPLOAD_KEY"
else
    echo "❌ 文件上传失败"
    echo "Response: $UPLOAD_RESPONSE"
    exit 1
fi
echo ""

# 3. 执行工作流
echo "3. 启动工作流..."
RESPONSE=$(curl -s -X POST http://localhost:18080/api/executor/executeByToolNameAsync \
  -H "Content-Type: application/json" \
  -d '{
    "toolName": "data-analysis-workflow",
    "serviceGroup": "data-analysis",
    "uploadKey": "'"$UPLOAD_KEY"'",
    "replacementParams": {
      "file_path": "sales_data.csv",
      "output_path": "analysis_report.md"
    }
  }')

PLAN_ID=$(echo $RESPONSE | grep -o '"planId":"[^"]*"' | cut -d'"' -f4)

if [ -n "$PLAN_ID" ]; then
    echo "✅ 工作流启动: $PLAN_ID"
else
    echo "❌ 启动失败"
    echo "Response: $RESPONSE"
    exit 1
fi
echo ""

# 4. 监控进度
echo "4. 等待执行完成..."
MAX_WAIT=120
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    STATUS_RESPONSE=$(curl -s "http://localhost:18080/api/executor/details/$PLAN_ID")
    
    # Check "completed" field
    COMPLETED=$(echo $STATUS_RESPONSE | sed 's/.*"completed":\([^,]*\).*/\1/')
    # Basic check if it contains true
    if [[ "$COMPLETED" == "true"* ]]; then
        echo "✅ 执行完成!"
        break
    fi
    
    echo -ne "   ⏳ 运行中... (${ELAPSED}s)\r"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done
echo ""

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo "⚠️  执行超时，尝试获取部分日志..."
fi

# 5. 获取详情并生成报告
echo "5. 生成时间线报告..."

JSON_FILE="execution_details_$PLAN_ID.json"
REPORT_FILE="execution_report_timeline.md"

# 下载 JSON
curl -s "http://localhost:18080/api/executor/details/$PLAN_ID" > "$JSON_FILE"

# 调用 Python 脚本
python3 example/analyze_timeline.py "$JSON_FILE" "$REPORT_FILE"

if [ -f "$REPORT_FILE" ]; then
    echo ""
    echo "🎉 报告生成成功: $REPORT_FILE"
    echo "----------------------------------------"
    echo "您可以使用 'cat $REPORT_FILE' 查看内容"
else 
    echo "❌ 报告生成失败"
fi

# 清理 JSON (可选)
# rm "$JSON_FILE"
