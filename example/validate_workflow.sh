#!/bin/bash

# Lynxe 数据分析工作流验证脚本

echo "========================================="
echo "Lynxe 数据分析工作流验证"
echo "========================================="
echo ""

# 1. 检查测试数据文件
echo "1. 检查测试数据文件..."
if [ -f "example/test-data/sales_data.csv" ]; then
    echo "✅ 测试数据文件存在"
    echo "   文件路径: example/test-data/sales_data.csv"
    echo "   记录数: $(wc -l < example/test-data/sales_data.csv)"
else
    echo "❌ 测试数据文件不存在"
    exit 1
fi
echo ""

# 2. 检查工作流是否已导入
# 2. 导入多步 Func-Agent 示例
echo "2. 导入多步 Func-Agent 示例..."
# 先清理旧模板
curl -s -X DELETE http://localhost:18080/api/plan-template/details/planTemplate-data-analysis-workflow > /dev/null
# 重新导入
IMPORT_RESPONSE=$(curl -s -X POST http://localhost:18080/api/plan-template/import-all \
  -H "Content-Type: application/json" \
  -d @example/multi-step-func-agent-examples.json)
echo "导入响应: $IMPORT_RESPONSE"

# 检查导入是否成功
WORKFLOW_CHECK=$(curl -s http://localhost:18080/api/plan-template/list-config | grep -o "data-analysis-workflow" | head -1)
if [ -n "$WORKFLOW_CHECK" ]; then
    echo "✅ 数据分析工作流已导入"
else
    echo "❌ 数据分析工作流未导入"
    exit 1
fi
echo ""

# 3. 上传测试数据
echo "3. 上传测试数据..."
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:18080/api/file-upload/upload \
  -H "Content-Type: multipart/form-data" \
  -F "files=@example/test-data/sales_data.csv")

echo "上传响应: $UPLOAD_RESPONSE"

# 提取 uploadKey
UPLOAD_KEY=$(echo $UPLOAD_RESPONSE | grep -o '"uploadKey":"[^"]*"' | cut -d'"' -f4)

if [ -n "$UPLOAD_KEY" ]; then
    echo "✅ 文件上传成功"
    echo "   Upload Key: $UPLOAD_KEY"
else
    echo "❌ 文件上传失败"
    exit 1
fi
echo ""

# 4. 执行工作流
echo "4. 执行数据分析工作流..."
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

echo "响应: $RESPONSE"

# 提取 planId
PLAN_ID=$(echo $RESPONSE | grep -o '"planId":"[^"]*"' | cut -d'"' -f4)

if [ -n "$PLAN_ID" ]; then
    echo "✅ 工作流已启动"
    echo "   Plan ID: $PLAN_ID"
else
    echo "❌ 工作流启动失败"
    echo "   错误信息: $RESPONSE"
    exit 1
fi
echo ""

# 4. 监控执行进度
echo "4. 监控执行进度..."
echo "   (每5秒检查一次状态，最多等待60秒)"
echo ""

MAX_WAIT=60
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    STATUS_RESPONSE=$(curl -s "http://localhost:18080/api/executor/details/$PLAN_ID")
    
    # 提取状态
    COMPLETED=$(echo $STATUS_RESPONSE | grep -o '"completed":[^,]*' | cut -d':' -f2)
    CURRENT_STEP=$(echo $STATUS_RESPONSE | grep -o '"currentStepIndex":[^,]*' | cut -d':' -f2)
    
    echo "   ⏱️  时间: ${ELAPSED}s | 当前步骤: $CURRENT_STEP | 完成状态: $COMPLETED"
    
    if [ "$COMPLETED" = "true" ]; then
        echo ""
        echo "✅ 工作流执行完成！"
        break
    fi
    
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo ""
    echo "⚠️  执行超时 (${MAX_WAIT}秒)"
    echo "   工作流可能仍在后台运行"
    echo "   请访问 http://localhost:18080 查看详情"
fi
echo ""

# 5. 检查输出报告
echo "5. 检查输出报告..."
if [ -f "example/test-data/analysis_report.md" ]; then
    echo "✅ 分析报告已生成"
    echo "   文件路径: example/test-data/analysis_report.md"
    echo "   文件大小: $(wc -c < example/test-data/analysis_report.md) bytes"
    echo ""
    echo "   报告预览 (前20行):"
    echo "   ----------------------------------------"
    head -20 example/test-data/analysis_report.md | sed 's/^/   /'
    echo "   ----------------------------------------"
else
    echo "⚠️  分析报告尚未生成"
    echo "   这可能是因为工作流仍在执行中"
fi
echo ""

# 6. 获取详细执行信息
echo "6. 获取执行详情..."
echo "   访问以下URL查看完整执行详情:"
echo "   http://localhost:18080/api/executor/details/$PLAN_ID"
echo ""

echo "========================================="
echo "验证完成！"
echo "========================================="
echo ""
echo "提示:"
echo "- 在 Lynxe UI 中查看执行过程: http://localhost:18080"
echo "- 点击右侧面板的'步骤执行详情'查看每个步骤的 Think-Act 记录"
echo "- 查看生成的报告: example/test-data/analysis_report.md"
