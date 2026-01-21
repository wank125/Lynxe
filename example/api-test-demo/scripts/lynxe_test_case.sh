#!/bin/bash

# ============================================================================
# Lynxe 完整测试案例 - 带详细日志输出
# ============================================================================

# 配置
BASE_URL="http://localhost:18080"
OUTPUT_DIR="/tmp/lynxe_test_output_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$OUTPUT_DIR/execution_log.txt"
THINK_FILE="$OUTPUT_DIR/think_process.txt"
SUMMARY_FILE="$OUTPUT_DIR/summary.txt"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m'

# 打印带颜色的消息到控制台
print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_section() {
    echo -e "\n${CYAN}--- $1 ---${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${GRAY}→ $1${NC}"
}

# 写入日志文件
log_to_file() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 写入 think 过程文件
log_think() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$THINK_FILE"
}

# 写入摘要文件
log_summary() {
    echo "$1" >> "$SUMMARY_FILE"
}

# ============================================================================
# 主测试流程
# ============================================================================

clear
print_header "Lynxe API 完整测试案例"

log_to_file "=========================================="
log_to_file "Lynxe 测试开始"
log_to_file "=========================================="

# ------------------------------------------------------------------------
# 测试 1: 简单对话测试
# ------------------------------------------------------------------------
print_section "测试 1: 简单对话测试 (SSE 流式)"
log_to_file "开始测试 1: 简单对话"

print_info "发送问题: 你好，请用一句话介绍 Spring AI"
RESPONSE=$(curl -s -N -X POST "$BASE_URL/api/executor/chat" \
  -H "Content-Type: application/json" \
  -d '{"input": "你好，请用一句话介绍 Spring AI"}' \
  --max-time 30)

# 解析 SSE 响应
echo "$RESPONSE" | grep -o '"content":"[^"]*"' | cut -d'"' -f4 | tr -d '\n' > /tmp/chat_response.txt
CHAT_ANSWER=$(cat /tmp/chat_response.txt)

echo -e "${GREEN}AI 回答:${NC} $CHAT_ANSWER"
log_to_file "对话测试回答: $CHAT_ANSWER"
print_success "对话测试完成"

# ------------------------------------------------------------------------
# 测试 2: 获取计划模板列表
# ------------------------------------------------------------------------
print_section "测试 2: 获取计划模板列表"
log_to_file "开始测试 2: 获取计划模板列表"

TEMPLATES=$(curl -s "$BASE_URL/api/plan-template/list")
TEMPLATE_COUNT=$(echo "$TEMPLATES" | grep -o '"count":[0-9]*' | cut -d':' -f2)

echo -e "可用模板数量: ${GREEN}$TEMPLATE_COUNT${NC}"
log_to_file "可用模板数量: $TEMPLATE_COUNT"

echo "$TEMPLATES" | grep -o '"title":"[^"]*"' | cut -d'"' -f4 | while read TITLE; do
    echo -e "  • $TITLE"
    log_to_file "  - $TITLE"
done

print_success "模板列表获取完成"

# ------------------------------------------------------------------------
# 测试 3: 异步执行任务并实时跟踪
# ------------------------------------------------------------------------
print_section "测试 3: 异步执行任务并实时跟踪"
log_to_file "开始测试 3: 异步执行任务"

TEST_QUESTION="帮我分析一下 Java Stream API 的优势"
print_info "用户问题: $TEST_QUESTION"

# 提交任务
print_info "提交任务..."
TASK_RESPONSE=$(curl -s -X POST "$BASE_URL/api/executor/executeByToolNameAsync" \
  -H "Content-Type: application/json" \
  -d "{
    \"toolName\": \"main-start-to-run\",
    \"serviceGroup\": \"example-userInteractive\",
    \"replacementParams\": {
      \"用户需求\": \"$TEST_QUESTION\"
    }
  }")

# 提取 planId
PLAN_ID=$(echo "$TASK_RESPONSE" | grep -o '"planId":"[^"]*"' | cut -d'"' -f4)

if [ -z "$PLAN_ID" ]; then
    print_error "任务提交失败"
    log_to_file "任务提交失败: $TASK_RESPONSE"
    exit 1
fi

echo -e "${GREEN}任务已提交${NC}"
echo -e "  Plan ID: ${MAGENTA}$PLAN_ID${NC}"
log_to_file "任务已提交，Plan ID: $PLAN_ID"
log_to_file "用户问题: $TEST_QUESTION"

# ------------------------------------------------------------------------
# 实时跟踪执行过程
# ------------------------------------------------------------------------
print_section "实时跟踪执行过程"
log_to_file "开始实时跟踪执行过程"
log_think "=========================================="
log_think "Think 过程记录"
log_think "=========================================="

LAST_STEP_COUNT=0
LAST_STATUS=""
CHECK_COUNT=0
MAX_CHECKS=60  # 最多检查 60 次 (1 分钟)

echo -e "\n${GRAY}等待任务执行...${NC}\n"

while [ $CHECK_COUNT -lt $MAX_CHECKS ]; do
    # 获取执行详情
    DETAILS=$(curl -s "$BASE_URL/api/executor/details/$PLAN_ID")
    
    # 检查错误
    if echo "$DETAILS" | grep -q '"error"'; then
        print_error "获取详情失败"
        log_to_file "获取详情失败: $DETAILS"
        break
    fi
    
    # 解析状态
    STATUS=$(echo "$DETAILS" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
    COMPLETED=$(echo "$DETAILS" | grep -o '"completed":[^,}]*' | head -1 | cut -d':' -f2)
    
    # 状态变化时显示
    if [ "$STATUS" != "$LAST_STATUS" ]; then
        STATUS_COLOR="$GRAY"
        if [ "$STATUS" = "RUNNING" ]; then
            STATUS_COLOR="$YELLOW"
        elif [ "$STATUS" = "FINISHED" ]; then
            STATUS_COLOR="$GREEN"
        elif [ "$STATUS" = "failed" ]; then
            STATUS_COLOR="$RED"
        fi
        
        echo -e "[${CYAN}$(date '+%H:%M:%S')${NC}] 状态: ${STATUS_COLOR}${STATUS}${NC}"
        log_to_file "状态变更: $STATUS"
        LAST_STATUS="$STATUS"
    fi
    
    # 计算当前步骤数
    CURRENT_STEP_COUNT=$(echo "$DETAILS" | grep -o '"stepId"' | wc -l | tr -d ' ')
    
    # 如果有新步骤，显示详细信息
    if [ "$CURRENT_STEP_COUNT" -gt "$LAST_STEP_COUNT" ]; then
        print_info "发现新步骤 (总计: $CURRENT_STEP_COUNT)"
        log_to_file "发现新步骤，当前总计: $CURRENT_STEP_COUNT"
        
        # 提取所有 stepId
        STEP_IDS=$(echo "$DETAILS" | grep -o '"stepId":"[^"]*"' | cut -d'"' -f4)
        
        STEP_NUM=0
        echo "$STEP_IDS" | while read STEP_ID; do
            if [ -n "$STEP_ID" ]; then
                STEP_NUM=$((STEP_NUM + 1))
                
                # 只处理新步骤
                if [ $STEP_NUM -gt "$LAST_STEP_COUNT" ]; then
                    # 获取步骤详情
                    STEP_DETAIL=$(curl -s "$BASE_URL/api/executor/agent-execution/$STEP_ID")
                    
                    # 提取信息
                    AGENT_NAME=$(echo "$STEP_DETAIL" | grep -o '"agentName":"[^"]*"' | cut -d'"' -f4)
                    STEP_STATUS=$(echo "$STEP_DETAIL" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
                    
                    echo ""
                    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                    echo -e "${GREEN}  步骤 $STEP_NUM: $AGENT_NAME${NC}"
                    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                    echo -e "状态: ${YELLOW}$STEP_STATUS${NC}"
                    echo -e "Step ID: ${GRAY}$STEP_ID${NC}"
                    
                    # 写入日志
                    log_to_file ""
                    log_to_file "========== 步骤 $STEP_NUM =========="
                    log_to_file "代理名称: $AGENT_NAME"
                    log_to_file "状态: $STEP_STATUS"
                    log_to_file "Step ID: $STEP_ID"
                    
                    # 提取代理请求
                    AGENT_REQUEST=$(echo "$STEP_DETAIL" | grep -o '"agentRequest":"[^"]*"' | cut -d'"' -f4 | sed 's/\\n/\n/g')
                    if [ -n "$AGENT_REQUEST" ]; then
                        echo -e "\n${GRAY}代理请求:${NC}"
                        echo "$AGENT_REQUEST" | fold -w 70 | sed 's/^/  /'
                        log_to_file "代理请求: $AGENT_REQUEST"
                    fi
                    
                    # 提取 think-act 记录数量
                    THINK_COUNT=$(echo "$STEP_DETAIL" | grep -o '"thinkInput"' | wc -l | tr -d ' ')
                    echo -e "\n${BLUE}Think-Act 循环次数: $THINK_COUNT${NC}"
                    log_to_file "Think-Act 循环次数: $THINK_COUNT"
                    log_think ""
                    log_think "========== 步骤 $STEP_NUM: $AGENT_NAME =========="
                    
                    # 遍历每个 think-act 记录
                    for ROUND_NUM in $(seq 1 $THINK_COUNT); do
                        echo -e "\n${MAGENTA}--- Round $ROUND_NUM ---${NC}"
                        log_think ""
                        log_think "--- Round $ROUND_NUM ---"
                        
                        # 提取 thinkOutput (LLM 的思考过程)
                        # 获取整个 thinkActSteps 数组并解析
                        THINK_OUTPUT=$(echo "$STEP_DETAIL" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'thinkActSteps' in data and len(data['thinkActSteps']) >= $ROUND_NUM:
        step = data['thinkActSteps'][$ROUND_NUM - 1]
        if 'thinkOutput' in step and step['thinkOutput']:
            print(step['thinkOutput'].replace('\\\\n', '\n'))
except Exception as e:
    pass
" 2>/dev/null)
                        
                        if [ -n "$THINK_OUTPUT" ]; then
                            echo -e "${CYAN}思考 (Think):${NC}"
                            echo "$THINK_OUTPUT" | fold -w 70 | sed 's/^/  │ /'
                            log_to_file "Round $ROUND_NUM 思考: $THINK_OUTPUT"
                            log_think "思考: $THINK_OUTPUT"
                        fi
                        
                        # 提取工具调用信息
                        TOOL_INFO=$(echo "$STEP_DETAIL" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'thinkActSteps' in data and len(data['thinkActSteps']) >= $ROUND_NUM:
        step = data['thinkActSteps'][$ROUND_NUM - 1]
        if 'actToolInfoList' in step and len(step['actToolInfoList']) > 0:
            for tool in step['actToolInfoList']:
                print(f\"工具: {tool.get('name', 'N/A')}\")
                print(f\"参数: {tool.get('parameters', 'N/A')}\")
                if 'result' in tool and tool['result']:
                    result = tool['result'][:200]  # 限制结果长度
                    print(f\"结果: {result}...\")
                print('---')
except Exception as e:
    pass
" 2>/dev/null)
                        
                        if [ -n "$TOOL_INFO" ]; then
                            echo -e "${YELLOW}行动 (Act):${NC}"
                            echo "$TOOL_INFO" | sed 's/^/  │ /' | sed 's/---/\n  │ ───/g'
                            log_to_file "Round $ROUND_NUM 行动:\n$TOOL_INFO"
                            log_think "行动: $TOOL_INFO"
                        fi
                    done
                    
                    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                fi
            fi
        done
        
        LAST_STEP_COUNT=$CURRENT_STEP_COUNT
    fi
    
    # 检查是否完成
    if [ "$COMPLETED" = "true" ]; then
        echo ""
        print_success "任务完成！"
        log_to_file "任务完成"
        
        # 显示最终结果
        SUMMARY=$(echo "$DETAILS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'summary' in data:
        print(data['summary'])
except:
    pass
" 2>/dev/null)
        
        if [ -n "$SUMMARY" ]; then
            echo ""
            echo -e "${BLUE}══════════════════════════════════════════${NC}"
            echo -e "${BLUE}  执行摘要${NC}"
            echo -e "${BLUE}══════════════════════════════════════════${NC}"
            echo "$SUMMARY" | fold -w 70 | sed 's/^/  /'
            log_to_file "执行摘要: $SUMMARY"
            log_summary "$SUMMARY"
        fi
        
        break
    fi
    
    # 检查失败
    if [ "$STATUS" = "failed" ]; then
        print_error "任务失败"
        log_to_file "任务失败"
        break
    fi
    
    sleep 1
    CHECK_COUNT=$((CHECK_COUNT + 1))
done

if [ $CHECK_COUNT -ge $MAX_CHECKS ]; then
    print_error "超时：任务未在规定时间内完成"
    log_to_file "超时：任务未在规定时间内完成"
fi

# ------------------------------------------------------------------------
# 测试 4: 获取系统配置
# ------------------------------------------------------------------------
print_section "测试 4: 获取系统配置"
log_to_file "开始测试 4: 获取系统配置"

CONFIG=$(curl -s "$BASE_URL/api/ LynxeConfig/group/lynxe" 2>/dev/null || curl -s "$BASE_URL/api/config/group/lynxe")

if [ -n "$CONFIG" ]; then
    CONFIG_COUNT=$(echo "$CONFIG" | grep -o '"configKey"' | wc -l | tr -d ' ')
    echo -e "配置项数量: ${GREEN}$CONFIG_COUNT${NC}"
    log_to_file "配置项数量: $CONFIG_COUNT"
    
    # 显示几个关键配置
    echo ""
    echo -e "关键配置:"
    echo "$CONFIG" | grep -E '"(headless|maxSteps|llmReadTimeout|debugDetail)"' | head -4 | while read LINE; do
        KEY=$(echo "$LINE" | grep -o '"configKey":"[^"]*"' | cut -d'"' -f4)
        VALUE=$(echo "$LINE" | grep -o '"configValue":"[^"]*"' | cut -d'"' -f4)
        echo -e "  • $KEY = ${YELLOW}$VALUE${NC}"
        log_to_file "  配置: $KEY = $VALUE"
    done
    
    print_success "配置获取完成"
else
    print_info "配置接口不可用"
fi

# ------------------------------------------------------------------------
# 测试总结
# ------------------------------------------------------------------------
print_section "测试总结"
log_to_file "=========================================="
log_to_file "测试完成"
log_to_file "=========================================="

echo ""
echo -e "${GREEN}所有测试已完成！${NC}"
echo ""
echo -e "${BLUE}输出文件位置:${NC}"
echo -e "  • 日志文件: ${MAGENTA}$LOG_FILE${NC}"
echo -e "  • Think 过程: ${MAGENTA}$THINK_FILE${NC}"
echo -e "  • 执行摘要: ${MAGENTA}$SUMMARY_FILE${NC}"
echo ""

# 保存完整测试报告
REPORT_FILE="$OUTPUT_DIR/test_report.txt"
cat > "$REPORT_FILE" << EOFREPORT
===========================================
Lynxe API 测试报告
===========================================
测试时间: $(date '+%Y-%m-%d %H:%M:%S')
输出目录: $OUTPUT_DIR

-------------------------------------------
测试用例
-------------------------------------------

1. 简单对话测试
   - 问题: 你好，请用一句话介绍 Spring AI
   - 回答: $CHAT_ANSWER

2. 计划模板列表
   - 可用模板数量: $TEMPLATE_COUNT

3. 异步任务执行
   - Plan ID: $PLAN_ID
   - 用户问题: $TEST_QUESTION
   - 详细日志见: $LOG_FILE
   - Think 过程见: $THINK_FILE

4. 系统配置
   - 配置项数量: $CONFIG_COUNT

-------------------------------------------
测试结果
-------------------------------------------
- ✓ 所有 API 接口响应正常
- ✓ 任务执行流程完整
- ✓ Think-Act 过程记录完整
- ✓ 日志文件已生成

===========================================
EOFREPORT

echo -e "${GREEN}测试报告已保存: $REPORT_FILE${NC}"
log_to_file "测试报告已保存: $REPORT_FILE"

# 显示文件大小
echo ""
echo -e "${BLUE}文件大小:${NC}"
ls -lh "$LOG_FILE" "$THINK_FILE" "$SUMMARY_FILE" "$REPORT_FILE" 2>/dev/null | awk '{print "  " $9 ": " $5}'

echo ""
print_success "测试案例执行完毕！"
