#!/usr/bin/env python3
"""
Lynxe Agent 高级时间轴可视化工具

功能：
1. 实时监控 agent 执行过程
2. 时间轴方式显示调用过程
3. 显示执行进度和当前步骤
4. 显示异常处理和修复工具调用
5. 暴露思考过程 (Think-Act)
6. 支持 ASCII/Markdown/HTML 输出

使用示例：
    # 启动新任务并监控
    python advanced_timeline_visualizer.py --execute complex-data-workflow --params '{"input_path": "/tmp/data.txt", "output_path": "/tmp/report.md"}'

    # 监控已有任务
    python advanced_timeline_visualizer.py --plan-id plan-xxx

    # 生成可视化报告
    python advanced_timeline_visualizer.py --plan-id plan-xxx --output html --output-file report.html
"""

import argparse
import json
import sys
import time
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum

try:
    import requests
except ImportError:
    print("错误: 需要安装 requests 库")
    print("请运行: pip install requests")
    sys.exit(1)


# =============================================================================
# 状态枚举
# =============================================================================

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    ERROR_RECOVERY = "error_recovery"


class ToolStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"


# =============================================================================
# API 客户端
# =============================================================================

class LynxeClient:
    """Lynxe API 客户端"""

    def __init__(self, base_url: str = "http://localhost:18080"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def import_template(self, template_file: str) -> bool:
        """导入工作流模板"""
        with open(template_file, 'r') as f:
            template_data = json.load(f)

        # 获取模板标题
        if isinstance(template_data, list):
            template_data = template_data[0]

        template_id = template_data.get("planTemplateId", "")
        if template_id:
            # 删除已存在的模板
            requests.delete(f"{self.base_url}/api/plan-template/details/{template_id}")

        # 导入新模板
        res = requests.post(
            f"{self.base_url}/api/plan-template/import-all",
            json=[template_data] if not isinstance(template_data, list) else template_data,
            headers={"Content-Type": "application/json"}
        )
        return res.status_code == 200

    def upload_file(self, file_path: str) -> Optional[str]:
        """上传文件"""
        try:
            with open(file_path, 'rb') as f:
                files = {'files': (file_path.split('/')[-1], f)}
                res = requests.post(f"{self.base_url}/api/file-upload/upload", files=files)
            if res.status_code == 200:
                return res.json().get('uploadKey')
        except Exception as e:
            print(f"上传文件失败: {e}")
        return None

    def execute_async(
        self,
        tool_name: str,
        replacement_params: Optional[Dict[str, Any]] = None,
        upload_key: Optional[str] = None,
        service_group: Optional[str] = None
    ) -> Optional[str]:
        """启动异步任务"""
        url = f"{self.base_url}/api/executor/executeByToolNameAsync"
        payload = {"toolName": tool_name}

        if replacement_params:
            payload["replacementParams"] = replacement_params
        if upload_key:
            payload["uploadKey"] = upload_key
        if service_group:
            payload["serviceGroup"] = service_group

        try:
            res = requests.post(url, json=payload, timeout=30)
            if res.status_code == 200:
                return res.json().get('planId')
        except requests.RequestException as e:
            print(f"启动任务失败: {e}")
        return None

    def get_execution_details(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """获取执行详情"""
        url = f"{self.base_url}/api/executor/details/{plan_id}"
        try:
            res = requests.get(url, timeout=30)
            if res.status_code == 200:
                return res.json()
        except requests.RequestException:
            pass
        return None


# =============================================================================
# 数据模型
# =============================================================================

class TimelineEvent:
    """时间轴事件"""

    def __init__(
        self,
        event_type: str,
        timestamp: Optional[datetime],
        description: str,
        status: str = "info",
        details: Optional[Dict] = None
    ):
        self.event_type = event_type  # 'step_start', 'step_end', 'think', 'tool_call', 'error', 'recovery'
        self.timestamp = timestamp
        self.description = description
        self.status = status  # 'info', 'success', 'warning', 'error'
        self.details = details or {}

    def __repr__(self):
        return f"[{self.event_type}] {self.description}"


# =============================================================================
# 时间轴可视化器
# =============================================================================

class AdvancedTimelineVisualizer:
    """高级时间轴可视化器"""

    def __init__(self):
        self.events: List[TimelineEvent] = []
        self.status_icons = {
            "pending": "⏳",
            "running": "🔄",
            "finished": "✅",
            "failed": "❌",
            "error": "🔥",
            "recovery": "🔧",
            "warning": "⚠️"
        }

    def parse_execution_data(self, execution_data: Dict[str, Any]) -> List[TimelineEvent]:
        """解析执行数据，提取时间轴事件"""
        events = []
        agent_sequence = execution_data.get("agentExecutionSequence", [])

        for step_idx, step in enumerate(agent_sequence):
            step_name = self._extract_step_name(step.get("agentRequest", ""), step_idx + 1)
            start_time = self._parse_time(step.get("startTime"))
            end_time = self._parse_time(step.get("endTime"))
            status = step.get("status", "unknown")

            # 步骤开始事件
            if start_time:
                events.append(TimelineEvent(
                    event_type="step_start",
                    timestamp=start_time,
                    description=f"步骤 {step_idx + 1}: {step_name}",
                    status="running"
                ))

            # 解析 Think-Act 步骤
            think_act_steps = step.get("thinkActSteps", [])
            for turn_idx, ta in enumerate(think_act_steps):
                # Think 事件
                think_input = ta.get("thinkInput", "")
                think_output = ta.get("thinkOutput", "")

                if think_input or think_output:
                    events.append(TimelineEvent(
                        event_type="think",
                        timestamp=start_time,  # 使用步骤开始时间
                        description=f"思考过程 (Turn {turn_idx + 1})",
                        status="info",
                        details={
                            "input": think_input,
                            "output": think_output
                        }
                    ))

                # Tool Call 事件
                tool_calls = ta.get("actToolInfoList", [])
                for tool in tool_calls:
                    tool_name = tool.get("toolName", "unknown")
                    tool_status = tool.get("toolExecuteStatus", "unknown")
                    tool_result = tool.get("result", "")

                    # 判断是否是修复工具
                    is_recovery = "repair" in tool_name.lower() or "fix" in tool_name.lower()
                    is_error_tool = "error" in tool_name.lower()

                    event_status = "success" if tool_status == "success" else "error"
                    if is_recovery:
                        event_status = "recovery"
                    elif is_error_tool:
                        event_status = "error"

                    events.append(TimelineEvent(
                        event_type="tool_call",
                        timestamp=start_time,
                        description=f"工具调用: {tool_name}",
                        status=event_status,
                        details={
                            "tool_name": tool_name,
                            "status": tool_status,
                            "result": tool_result[:200] if tool_result else ""
                        }
                    ))

            # 步骤结束事件
            if end_time:
                step_status = "success" if status == "FINISHED" else "error"
                events.append(TimelineEvent(
                    event_type="step_end",
                    timestamp=end_time,
                    description=f"步骤 {step_idx + 1} 完成",
                    status=step_status
                ))

        # 按时间排序
        events.sort(key=lambda e: e.timestamp or datetime.min)
        return events

    def _extract_step_name(self, agent_request: str, step_idx: int) -> str:
        """提取步骤名称"""
        lines = agent_request.split('\n')
        if lines:
            first_line = lines[0]
            # 移除 "Step X:" 前缀
            if ":" in first_line:
                return first_line.split(":", 1)[1].strip()
        return f"步骤 {step_idx}"

    def _parse_time(self, time_value: Any) -> Optional[datetime]:
        """解析时间"""
        if not time_value:
            return None

        try:
            # 如果是列表 [Y, M, D, H, M, S, N]
            if isinstance(time_value, list):
                return datetime(*time_value[:6])
            # 如果是字符串
            if isinstance(time_value, str):
                return datetime.fromisoformat(time_value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass
        return None

    def render_ascii_timeline(self, events: List[TimelineEvent]) -> str:
        """渲染 ASCII 时间轴"""
        if not events:
            return "📭 暂无执行记录"

        lines = []
        width = 80

        # 标题
        lines.append("╔" + "═" * (width - 2) + "╗")
        lines.append("║" + " " * 20 + "📊 Agent 执行时间轴" + " " * (width - 42) + "║")
        lines.append("╠" + "═" * (width - 2) + "╣")
        lines.append("║" + " " * (width - 2) + "║")

        # 渲染每个事件
        for event in events:
            icon = self.status_icons.get(event.status, "📌")
            time_str = event.timestamp.strftime("%H:%M:%S") if event.timestamp else "--:--:--"

            # 事件描述
            desc = event.description[:50] + "..." if len(event.description) > 50 else event.description

            line = f"║ {icon} {time_str} │ {desc:<55} ║"
            lines.append(line)

            # 显示详细信息
            if event.details:
                if "input" in event.details and event.details["input"]:
                    input_text = event.details["input"][:60] + "..." if len(event.details["input"]) > 60 else event.details["input"]
                    lines.append(f"║     💭 思考: {input_text:<55} ║")
                if "output" in event.details and event.details["output"]:
                    output_text = event.details["output"][:60] + "..." if len(event.details["output"]) > 60 else event.details["output"]
                    lines.append(f"║     💡 结果: {output_text:<55} ║")
                if "result" in event.details and event.details["result"]:
                    result_text = event.details["result"][:60] + "..." if len(event.details["result"]) > 60 else event.details["result"]
                    lines.append(f"║     📄 返回: {result_text:<55} ║")

        lines.append("╚" + "═" * (width - 2) + "╝")

        return "\n".join(lines)

    def render_markdown_timeline(self, events: List[TimelineEvent], execution_data: Dict[str, Any]) -> str:
        """渲染 Markdown 时间轴"""
        lines = ["# Agent 执行报告\n"]
        lines.append("## 📊 执行时间轴\n")

        # 统计信息
        total_steps = len([e for e in events if e.event_type == "step_start"])
        total_thinks = len([e for e in events if e.event_type == "think"])
        total_tools = len([e for e in events if e.event_type == "tool_call"])
        errors = len([e for e in events if e.status == "error"])
        recoveries = len([e for e in events if e.status == "recovery"])

        lines.append("### 统计信息")
        lines.append(f"- 总步骤数: {total_steps}")
        lines.append(f"- 思考过程: {total_thinks}")
        lines.append(f"- 工具调用: {total_tools}")
        lines.append(f"- 错误数量: {errors}")
        lines.append(f"- 修复操作: {recoveries}\n")

        # 时间轴
        lines.append("### 详细时间线")
        lines.append("| 时间 | 事件 | 状态 | 详情 |")
        lines.append("|------|------|------|------|")

        for event in events:
            time_str = event.timestamp.strftime("%H:%M:%S") if event.timestamp else "--:--:--"
            icon = self.status_icons.get(event.status, "📌")
            desc = event.description.replace("|", "\\|")

            details = ""
            if event.details:
                if "input" in event.details:
                    details = event.details["input"][:30] + "..." if len(event.details.get("input", "")) > 30 else event.details.get("input", "")

            lines.append(f"| {time_str} | {desc} | {icon} {event.status} | {details} |")

        return "\n".join(lines)

    def render_html_timeline(self, events: List[TimelineEvent], execution_data: Dict[str, Any]) -> str:
        """渲染 HTML 时间轴"""
        html = ['<!DOCTYPE html>']
        html.append('<html lang="zh-CN">')
        html.append('<head>')
        html.append('    <meta charset="UTF-8">')
        html.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html.append('    <title>Agent 执行时间轴</title>')
        html.append('    <style>')
        html.append('        * { margin: 0; padding: 0; box-sizing: border-box; }')
        html.append('        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; min-height: 100vh; }')
        html.append('        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); overflow: hidden; }')
        html.append('        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }')
        html.append('        .header h1 { font-size: 28px; margin-bottom: 10px; }')
        html.append('        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; padding: 20px 30px; background: #f8f9fa; }')
        html.append('        .stat-card { background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }')
        html.append('        .stat-card .number { font-size: 32px; font-weight: bold; color: #667eea; }')
        html.append('        .stat-card .label { font-size: 14px; color: #666; margin-top: 5px; }')
        html.append('        .timeline { padding: 30px; }')
        html.append('        .timeline-item { position: relative; padding-left: 40px; margin-bottom: 25px; }')
        html.append('        .timeline-item::before { content: ""; position: absolute; left: 10px; top: 0; bottom: -25px; width: 2px; background: #e9ecef; }')
        html.append('        .timeline-item:last-child::before { display: none; }')
        html.append('        .timeline-dot { position: absolute; left: 3px; top: 5px; width: 16px; height: 16px; border-radius: 50%; background: #667eea; border: 3px solid white; box-shadow: 0 0 0 2px #667eea; }')
        html.append('        .timeline-item.error .timeline-dot { background: #dc3545; box-shadow: 0 0 0 2px #dc3545; }')
        html.append('        .timeline-item.recovery .timeline-dot { background: #ffc107; box-shadow: 0 0 0 2px #ffc107; }')
        html.append('        .timeline-item.success .timeline-dot { background: #28a745; box-shadow: 0 0 0 2px #28a745; }')
        html.append('        .timeline-time { font-size: 12px; color: #6c757d; margin-bottom: 5px; }')
        html.append('        .timeline-content { background: #f8f9fa; padding: 15px; border-radius: 8px; }')
        html.append('        .event-type { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; margin-bottom: 8px; }')
        html.append('        .event-type.step { background: #e7f3ff; color: #0066cc; }')
        html.append('        .event-type.think { background: #fff3cd; color: #856404; }')
        html.append('        .event-type.tool { background: #d4edda; color: #155724; }')
        html.append('        .event-type.error { background: #f8d7da; color: #721c24; }')
        html.append('        .event-type.recovery { background: #ffeaa7; color: #d63031; }')
        html.append('        .event-description { font-weight: 500; color: #333; margin-bottom: 8px; }')
        html.append('        .event-details { font-size: 13px; color: #666; background: white; padding: 10px; border-radius: 6px; margin-top: 8px; }')
        html.append('        .event-details strong { color: #495057; }')
        html.append('        .thinking-process { background: #fffbeb; border-left: 3px solid #f59e0b; padding: 10px; margin-top: 8px; border-radius: 4px; }')
        html.append('        .thinking-process .label { font-size: 11px; color: #92400e; font-weight: bold; margin-bottom: 5px; }')
        html.append('        .thinking-process .content { font-size: 13px; color: #78350f; font-style: italic; }')
        html.append('    </style>')
        html.append('</head>')
        html.append('<body>')
        html.append('    <div class="container">')
        html.append('        <div class="header">')
        html.append('            <h1>🚀 Agent 执行时间轴</h1>')
        html.append('            <p>实时监控执行过程、思考过程和异常处理</p>')
        html.append('        </div>')

        # 统计
        total_steps = len([e for e in events if e.event_type == "step_start"])
        total_thinks = len([e for e in events if e.event_type == "think"])
        total_tools = len([e for e in events if e.event_type == "tool_call"])
        errors = len([e for e in events if e.status == "error"])
        recoveries = len([e for e in events if e.status == "recovery"])

        html.append('        <div class="stats">')
        html.append(f'            <div class="stat-card"><div class="number">{total_steps}</div><div class="label">总步骤</div></div>')
        html.append(f'            <div class="stat-card"><div class="number">{total_thinks}</div><div class="label">思考过程</div></div>')
        html.append(f'            <div class="stat-card"><div class="number">{total_tools}</div><div class="label">工具调用</div></div>')
        html.append(f'            <div class="stat-card"><div class="number">{errors}</div><div class="label">错误</div></div>')
        html.append(f'            <div class="stat-card"><div class="number">{recoveries}</div><div class="label">修复操作</div></div>')
        html.append('        </div>')

        # 时间轴
        html.append('        <div class="timeline">')

        for event in events:
            item_class = "timeline-item"
            if event.status == "error":
                item_class += " error"
            elif event.status == "recovery":
                item_class += " recovery"
            elif event.status == "success":
                item_class += " success"

            html.append(f'            <div class="{item_class}">')
            html.append('                <div class="timeline-dot"></div>')

            if event.timestamp:
                html.append(f'                <div class="timeline-time">{event.timestamp.strftime("%H:%M:%S")}</div>')

            html.append('                <div class="timeline-content">')

            # 事件类型标签
            type_labels = {
                "step_start": "步骤开始",
                "step_end": "步骤完成",
                "think": "💭 思考",
                "tool_call": "🔧 工具",
                "error": "❌ 错误",
                "recovery": "🔧 修复"
            }
            type_class = "step" if "step" in event.event_type else event.event_type
            html.append(f'                    <span class="event-type {type_class}">{type_labels.get(event.event_type, event.event_type)}</span>')

            html.append(f'                    <div class="event-description">{self._escape_html(event.description)}</div>')

            # 详细信息
            if event.details:
                if "input" in event.details and event.details["input"]:
                    html.append('                    <div class="thinking-process">')
                    html.append('                        <div class="label">思考输入</div>')
                    html.append(f'                        <div class="content">{self._escape_html(event.details["input"][:200])}</div>')
                    html.append('                    </div>')

                if "output" in event.details and event.details["output"]:
                    html.append('                    <div class="thinking-process">')
                    html.append('                        <div class="label">思考输出</div>')
                    html.append(f'                        <div class="content">{self._escape_html(event.details["output"][:200])}</div>')
                    html.append('                    </div>')

                if "result" in event.details and event.details["result"]:
                    html.append('                    <div class="event-details">')
                    html.append(f'                        <strong>结果:</strong> {self._escape_html(event.details["result"][:200])}')
                    html.append('                    </div>')

            html.append('                </div>')
            html.append('            </div>')

        html.append('        </div>')
        html.append('    </div>')
        html.append('</body>')
        html.append('</html>')

        return "\n".join(html)

    @staticmethod
    def _escape_html(text: str) -> str:
        """转义 HTML"""
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&#x27;"))


# =============================================================================
# 实时监控器
# =============================================================================

class RealtimeMonitor:
    """实时监控器"""

    def __init__(self, client: LynxeClient, visualizer: AdvancedTimelineVisualizer):
        self.client = client
        self.visualizer = visualizer
        self.processed_steps = set()
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_idx = 0

    def monitor(self, plan_id: str, timeout: int = 300) -> Optional[Dict[str, Any]]:
        """实时监控任务执行"""
        print(f"\n🚀 开始监控任务: {plan_id}")
        print("=" * 80)

        start_time = time.time()
        last_event_count = 0

        while time.time() - start_time < timeout:
            details = self.client.get_execution_details(plan_id)
            if not details:
                print(f"❌ 无法获取任务详情")
                return None

            # 解析事件
            events = self.visualizer.parse_execution_data(details)

            # 显示新事件
            if len(events) > last_event_count:
                for event in events[last_event_count:]:
                    self._print_event(event)
                last_event_count = len(events)

            # 检查是否完成
            if details.get("completed", False):
                print("\n" + "=" * 80)
                print("✅ 任务完成!")
                return details

            # 显示进度
            self._print_progress(events, len(details.get("agentExecutionSequence", [])))
            time.sleep(1)

        print("\n⚠️ 监控超时")
        return None

    def _print_event(self, event: TimelineEvent):
        """打印单个事件"""
        icons = {
            "step_start": "📍",
            "step_end": "🏁",
            "think": "💭",
            "tool_call": "🔧",
            "error": "❌",
            "recovery": "🔧"
        }

        icon = icons.get(event.event_type, "📌")
        time_str = event.timestamp.strftime("%H:%M:%S") if event.timestamp else "--:--:--"

        print(f"\n{icon} [{time_str}] {event.description}")

        # 显示详细信息
        if event.details:
            if "input" in event.details and event.details["input"]:
                input_text = event.details["input"][:100] + "..." if len(event.details["input"]) > 100 else event.details["input"]
                print(f"   🤔 思考: {input_text}")

            if "output" in event.details and event.details["output"]:
                output_text = event.details["output"][:100] + "..." if len(event.details["output"]) > 100 else event.details["output"]
                print(f"   💡 输出: {output_text}")

            if "result" in event.details and event.details["result"]:
                result_text = event.details["result"][:100] + "..." if len(event.details["result"]) > 100 else event.details["result"]
                print(f"   📄 结果: {result_text}")

    def _print_progress(self, events: List[TimelineEvent], step_count: int):
        """打印进度"""
        spinner = self.spinner_frames[self.spinner_idx % len(self.spinner_frames)]
        self.spinner_idx += 1

        # 统计
        steps_done = len([e for e in events if e.event_type == "step_end"])
        thinks = len([e for e in events if e.event_type == "think"])
        tools = len([e for e in events if e.event_type == "tool_call"])
        errors = len([e for e in events if e.status == "error"])
        recoveries = len([e for e in events if e.status == "recovery"])

        progress = f"\r{spinner} 步骤: {steps_done}/{step_count} | 思考: {thinks} | 工具: {tools} | 错误: {errors} | 修复: {recoveries}"
        sys.stdout.write(progress)
        sys.stdout.flush()


# =============================================================================
# 主程序
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Lynxe Agent 高级时间轴可视化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # 执行模式
    parser.add_argument("--execute", "-e", help="工具名称")
    parser.add_argument("--plan-id", "-p", help="任务 ID")
    parser.add_argument("--params", help="替换参数 (JSON)")
    parser.add_argument("--service-group", "-g", help="服务组")
    parser.add_argument("--upload-key", "-u", help="文件上传 Key")
    parser.add_argument("--template", "-t", help="模板文件路径")

    # 输出格式
    parser.add_argument("--output", "-o", choices=["console", "markdown", "html"], default="console", help="输出格式")
    parser.add_argument("--output-file", "-f", help="输出文件")

    # 其他选项
    parser.add_argument("--server", "-s", default="http://localhost:18080", help="服务器地址")
    parser.add_argument("--timeout", type=int, default=300, help="超时时间（秒）")
    parser.add_argument("--no-monitor", action="store_true", help="不实时监控")

    args = parser.parse_args()

    # 初始化
    client = LynxeClient(args.server)
    visualizer = AdvancedTimelineVisualizer()
    monitor = RealtimeMonitor(client, visualizer)

    plan_id = args.plan_id

    # 导入模板（如果指定）
    if args.template:
        print(f"📦 导入模板: {args.template}")
        if client.import_template(args.template):
            print("✅ 模板导入成功")
        else:
            print("❌ 模板导入失败")

    # 执行任务
    if args.execute:
        params = None
        if args.params:
            try:
                params = json.loads(args.params)
            except json.JSONDecodeError as e:
                print(f"❌ JSON 解析失败: {e}")
                sys.exit(1)

        plan_id = client.execute_async(
            tool_name=args.execute,
            replacement_params=params,
            upload_key=args.upload_key,
            service_group=args.service_group
        )

        if not plan_id:
            print("❌ 任务启动失败")
            sys.exit(1)

        print(f"✅ 任务已启动: {plan_id}")

    if not plan_id:
        parser.error("必须指定 --execute 或 --plan-id")

    # 监控或获取结果
    if args.no_monitor:
        execution_data = client.get_execution_details(plan_id)
    else:
        execution_data = monitor.monitor(plan_id, args.timeout)

    if not execution_data:
        print("❌ 无法获取执行数据")
        sys.exit(1)

    # 生成输出
    events = visualizer.parse_execution_data(execution_data)

    if args.output == "console":
        print("\n" + visualizer.render_ascii_timeline(events))
    elif args.output == "markdown":
        md = visualizer.render_markdown_timeline(events, execution_data)
        if args.output_file:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"✅ Markdown 报告已保存: {args.output_file}")
        else:
            print(md)
    elif args.output == "html":
        html = visualizer.render_html_timeline(events, execution_data)
        if args.output_file:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"✅ HTML 报告已保存: {args.output_file}")
        else:
            print(html)


if __name__ == "__main__":
    main()
