#!/usr/bin/env python3
"""
Lynxe Agent 时间轴监控与可视化工具

功能：
1. 调用 API 启动任务
2. 实时监控执行过程
3. 生成时间轴可视化（ASCII/Markdown/HTML）

使用示例：
    # 启动新任务并监控
    python timeline_monitor.py --execute simple-tool-test --params '{"file_path": "/tmp/test.txt"}'

    # 监控已有任务
    python timeline_monitor.py --plan-id plan-xxx

    # 生成 Markdown 报告
    python timeline_monitor.py --plan-id plan-xxx --output markdown --output-file report.md
"""

import argparse
import json
import sys
import time
from datetime import datetime
from typing import Optional, Dict, List, Any

try:
    import requests
except ImportError:
    print("错误: 需要安装 requests 库")
    print("请运行: pip install requests")
    sys.exit(1)


# =============================================================================
# API 客户端
# =============================================================================

class LynxeClient:
    """Lynxe API 客户端，用于与后端交互"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def execute_async(
        self,
        tool_name: str,
        replacement_params: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
        service_group: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        启动异步任务

        请求格式：
        POST /api/executor/executeByToolNameAsync
        {
            "toolName": "simple-tool-test",
            "replacementParams": {"file_path": "/path/to/file.txt"},
            "conversationId": "optional-conversation-id",
            "serviceGroup": "test"
        }

        响应格式：
        {
            "planId": "plan-xxx",
            "status": "processing",
            "message": "Task submitted, processing"
        }
        """
        url = f"{self.base_url}/api/executor/executeByToolNameAsync"
        payload = {"toolName": tool_name}

        if replacement_params:
            payload["replacementParams"] = replacement_params
        if conversation_id:
            payload["conversationId"] = conversation_id
        if service_group:
            payload["serviceGroup"] = service_group

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"启动任务失败: {e}")

    def get_execution_details(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        获取完整执行详情

        响应格式：PlanExecutionRecord JSON
        - rootPlanId
        - currentPlanId
        - completed
        - agentExecutionSequence: List[AgentExecutionRecord]
            - stepId
            - stepName
            - startTime / endTime
            - thinkActSteps: List[ThinkActRecord]
                - turnNumber
                - thinkInput / thinkOutput
                - actToolInfoList: List[ActToolInfo]
                    - toolName
                    - parameters
                    - result
                    - toolExecuteStatus
        """
        url = f"{self.base_url}/api/executor/details/{plan_id}"
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"获取执行详情失败: {e}")

    def get_task_status(self, plan_id: str) -> Dict[str, Any]:
        """获取任务状态（轻量级）"""
        url = f"{self.base_url}/api/executor/taskStatus/{plan_id}"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"获取任务状态失败: {e}")

    def stop_task(self, plan_id: str) -> Dict[str, Any]:
        """停止运行中的任务"""
        url = f"{self.base_url}/api/executor/stopTask/{plan_id}"
        try:
            response = requests.post(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RuntimeError(f"停止任务失败: {e}")


# =============================================================================
# 实时监控器
# =============================================================================

class TimelineMonitor:
    """实时监控任务执行并生成时间轴"""

    def __init__(self, client: LynxeClient, poll_interval: float = 1.0):
        self.client = client
        self.poll_interval = poll_interval
        self.start_time = None
        self.last_printed_step = 0
        self.total_steps_estimate = 0  # 预估总步骤数
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_idx = 0

    def monitor(self, plan_id: str, verbose: bool = True) -> Optional[Dict[str, Any]]:
        """
        监控任务执行，显示实时进度条和详细步骤信息

        轮询逻辑：
        1. 每 poll_interval 秒调用一次 get_execution_details()
        2. 检查 completed 状态
        3. 实时打印当前进度（带进度条）
        4. 完成后返回完整数据
        """
        self.start_time = time.time()
        last_step_count = 0
        last_output_line = ""

        if verbose:
            print(f"\n🚀 开始监控任务: {plan_id}")
            print("=" * 70)
            # 打印表头
            print(f"{'状态':<8} {'进度':<30} {'步骤':<20} {'耗时'}")
            print("-" * 70)

        try:
            while True:
                details = self.client.get_execution_details(plan_id)

                if details is None:
                    if verbose:
                        print(f"\r❌ 任务 {plan_id} 不存在" + " " * 40)
                    return None

                # 检查是否有新步骤
                agent_sequence = details.get("agentExecutionSequence", [])
                current_step_count = len(agent_sequence)

                # 更新总步骤数预估
                if current_step_count > self.total_steps_estimate:
                    self.total_steps_estimate = current_step_count

                # 实时更新进度条（即使在同一步骤内也更新）
                if verbose:
                    progress_info = self._get_progress_info(details, agent_sequence)
                    # 使用 \r 实现同行更新，显示动态进度
                    sys.stdout.write(f"\r{progress_info}")
                    sys.stdout.flush()

                # 检查是否有新步骤完成
                if current_step_count > last_step_count:
                    if verbose:
                        # 新步骤完成，打印详细信息
                        print()  # 换行，保留进度条显示
                        for i in range(last_step_count, current_step_count):
                            self._print_step(agent_sequence[i], i + 1, current_step_count)
                            print()  # 步骤后空行
                    last_step_count = current_step_count

                # 检查是否完成
                if details.get("completed", False):
                    total_time = time.time() - self.start_time
                    if verbose:
                        # 打印最终进度条
                        final_progress = self._get_final_progress(total_time, current_step_count)
                        print(f"\r{final_progress}")
                        print("=" * 70)
                        print(f"✅ 任务完成！总耗时: {total_time:.2f}秒 | 步骤数: {current_step_count}")
                    return details

                # 等待下一次轮询
                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            if verbose:
                print(f"\n\n⚠️  监控已中断 (Ctrl+C)")
                print(f"   已完成步骤: {last_step_count}")
            return None

    def _get_progress_info(self, details: Dict[str, Any], agent_sequence: List[Dict]) -> str:
        """获取当前进度信息字符串"""
        # 获取当前正在运行的步骤
        current_step_count = len(agent_sequence)
        completed = details.get("completed", False)

        # 估算总步骤数（根据已完成的步骤）
        if self.total_steps_estimate == 0 and current_step_count > 0:
            self.total_steps_estimate = max(current_step_count, 3)

        total_steps = max(self.total_steps_estimate, current_step_count)

        # 计算进度百分比
        progress_percent = min(100, int((current_step_count / total_steps) * 100)) if total_steps > 0 else 0

        # 计算已用时间
        elapsed = time.time() - self.start_time

        # 判断当前状态
        if completed:
            status = "✅ 完成"
            spinner = "✓"
        else:
            spinner = self.spinner_frames[self.spinner_idx % len(self.spinner_frames)]
            self.spinner_idx += 1
            status = f"{spinner} 运行"

        # 构建进度条
        bar_width = 20
        filled = int(bar_width * progress_percent / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        # 当前步骤名称
        if agent_sequence:
            current_step = agent_sequence[-1]
            step_name = current_step.get("stepName", "Processing...")
            # 截断过长的步骤名
            if len(step_name) > 18:
                step_name = step_name[:15] + "..."
        else:
            step_name = "初始化..."

        # 格式: [状态] [进度条] 百分% | 步骤名 | 已用时间
        return f"{status:<8} [{bar}] {progress_percent:3d}% | {step_name:<18} | {elapsed:5.1f}s"

    def _get_final_progress(self, total_time: float, step_count: int) -> str:
        """获取完成时的最终进度字符串"""
        bar_width = 20
        bar = "█" * bar_width
        return f"{'✅ 完成':<8} [{bar}] 100% | {step_count} 步骤 | {total_time:5.1f}s"

    def _print_step(self, step: Dict[str, Any], index: int, total_steps: int):
        """打印单个步骤的详细信息"""
        step_name = step.get("stepName", f"Step {index}")
        start_time = self._parse_time(step.get("startTime"))
        end_time = self._parse_time(step.get("endTime"))

        if start_time and end_time:
            duration = (end_time - start_time).total_seconds()
        else:
            duration = 0

        # 判断步骤状态
        if not end_time:
            status_icon = "🔄"
            status_text = "运行中"
        elif self._step_has_error(step):
            status_icon = "⚠️"
            status_text = "有错误"
        else:
            status_icon = "✅"
            status_text = "完成"

        # 缩进显示层级
        indent = "  "

        print(f"{indent}[{index}/{total_steps}] {status_icon} {status_text}: {step_name} ({duration:.2f}s)")

        # 打印 Think-Act 记录（如果有）
        think_act_steps = step.get("thinkActSteps", [])
        if think_act_steps:
            for ta in think_act_steps:
                turn = ta.get("turnNumber", 0)
                think_input = ta.get("thinkInput", "")
                if think_input:
                    # 显示思考内容（截断）
                    truncated = think_input[:60] + "..." if len(think_input) > 60 else think_input
                    print(f"{indent}    💭 Turn {turn}: {truncated}")

                # 显示工具调用
                tool_calls = ta.get("actToolInfoList", [])
                for tc in tool_calls:
                    tool_name = tc.get("toolName", "unknown")
                    exec_status = tc.get("toolExecuteStatus", "unknown")
                    icon = "✅" if exec_status == "success" else "❌"
                    print(f"{indent}    {icon} {tool_name}")

    def _step_has_error(self, step: Dict[str, Any]) -> bool:
        """检查步骤是否有错误"""
        think_act_steps = step.get("thinkActSteps", [])
        for ta in think_act_steps:
            tool_calls = ta.get("actToolInfoList", [])
            for tc in tool_calls:
                if tc.get("toolExecuteStatus") != "success":
                    return True
                if "error-report-tool" in tc.get("toolName", ""):
                    return True
        return False

    @staticmethod
    def _parse_time(time_str: Optional[str]) -> Optional[datetime]:
        """解析时间字符串"""
        if not time_str:
            return None
        try:
            # Java LocalDateTime 格式: 2025-01-21T12:34:56.123456
            return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None


# =============================================================================
# 时间轴可视化器
# =============================================================================

class TimelineVisualizer:
    """生成多种格式的时间轴可视化"""

    def __init__(self):
        self.status_icons = {
            "completed": "✅",
            "failed": "❌",
            "running": "🔄",
            "error": "🔥"
        }

    def render_ascii_timeline(self, execution_data: Dict[str, Any]) -> str:
        """
        渲染 ASCII 时间轴

        输出示例：
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        00:00                                                01:30
        │
        ├─ Step 1: Read File ✅ (2s)
        │   ├─ 💭: "Need to read the file first"
        │   └─ 🔧: fs-read-file-operator → Success
        │
        └─ Step 2: Process Data ⚠️ (5s)
            ├─ 💭: "Checking data format"
            └─ 🔧: error-report-tool → Error: Invalid format
        """
        lines = []
        agent_sequence = execution_data.get("agentExecutionSequence", [])

        if not agent_sequence:
            return "📭 无执行记录"

        total_duration = self._calculate_total_duration(execution_data)
        timeline_length = 60

        # 绘制时间轴头
        lines.append("━" * timeline_length)
        lines.append(f"00:00{' ' * (timeline_length - 20)}{self._format_duration(total_duration)}")
        lines.append("│")

        # 绘制每个步骤
        for i, step in enumerate(agent_sequence):
            step_line = self._render_step(step, i + 1, is_last=(i == len(agent_sequence) - 1))
            lines.append(step_line)

        lines.append("━" * timeline_length)

        return "\n".join(lines)

    def _render_step(self, step: Dict[str, Any], index: int, is_last: bool = False) -> str:
        """渲染单个步骤"""
        step_name = step.get("stepName", f"Step {index}")
        duration = self._calculate_step_duration(step)

        # 判断步骤状态
        status = "✅"
        has_error = self._step_has_error(step)
        if has_error:
            status = "⚠️"

        prefix = "└" if is_last else "├"
        step_header = f"{prefix}─ Step {index}: {step_name} {status} ({duration:.1f}s)"

        lines = [step_header]

        # 渲染 Think-Act 记录
        think_act_steps = step.get("thinkActSteps", [])
        connector = "    " + ("└" if is_last else "│")

        for ta in think_act_steps:
            # Think
            think_input = ta.get("thinkInput", "")
            if think_input:
                truncated_think = think_input[:80] + "..." if len(think_input) > 80 else think_input
                lines.append(f"{connector}    ├─ 💭: {truncated_think}")

            # Tool Calls
            tool_calls = ta.get("actToolInfoList", [])
            for tc in tool_calls:
                tool_name = tc.get("toolName", "unknown")
                exec_status = tc.get("toolExecuteStatus", "unknown")
                result = tc.get("result", "")

                icon = "✅" if exec_status == "success" else "❌"
                result_preview = result[:50] + "..." if result and len(result) > 50 else (result or "")

                lines.append(f"{connector}    └─ 🔧: {tool_name} {icon}")
                if result_preview:
                    lines.append(f"{connector}       → {result_preview}")

        return "\n".join(lines)

    def render_markdown(self, execution_data: Dict[str, Any]) -> str:
        """
        渲染 Markdown 报告

        格式：
        # 执行报告

        ## 概览
        - 总耗时: 10.5s
        - 步骤数: 3
        - 状态: ✅ 完成
        """
        lines = ["# Agent 执行报告\n"]

        # 概览
        total_duration = self._calculate_total_duration(execution_data)
        agent_sequence = execution_data.get("agentExecutionSequence", [])
        completed = execution_data.get("completed", False)

        lines.append("## 📊 概览")
        lines.append(f"- **总耗时**: {self._format_duration(total_duration)}")
        lines.append(f"- **步骤数**: {len(agent_sequence)}")
        lines.append(f"- **状态**: {'✅ 完成' if completed else '🔄 运行中'}\n")

        # 时间轴
        lines.append("## ⏱️ 时间轴")
        lines.append("```")
        lines.append(self.render_ascii_timeline(execution_data))
        lines.append("```\n")

        # 详细步骤
        lines.append("## 📝 详细步骤")
        for i, step in enumerate(agent_sequence):
            step_name = step.get("stepName", f"Step {i + 1}")
            duration = self._calculate_step_duration(step)
            lines.append(f"\n### 步骤 {i + 1}: {step_name} ({duration:.1f}s)")

            # Think-Act 记录
            think_act_steps = step.get("thinkActSteps", [])
            for ta in think_act_steps:
                turn = ta.get("turnNumber", 0)
                think_input = ta.get("thinkInput", "")
                think_output = ta.get("thinkOutput", "")

                if think_input:
                    lines.append(f"\n**Turn {turn} - Think Input:**")
                    lines.append(f"```\n{think_input}\n```")

                if think_output:
                    lines.append(f"\n**Turn {turn} - Think Output:**")
                    lines.append(f"```\n{think_output}\n```")

                # Tool Calls
                tool_calls = ta.get("actToolInfoList", [])
                if tool_calls:
                    lines.append(f"\n**Tool Calls:**")
                    for tc in tool_calls:
                        tool_name = tc.get("toolName", "unknown")
                        exec_status = tc.get("toolExecuteStatus", "unknown")
                        result = tc.get("result", "")

                        lines.append(f"- `{tool_name}`: **{exec_status}**")
                        if result:
                            preview = result[:200] + "..." if len(result) > 200 else result
                            lines.append("  ```")
                            lines.append(preview)
                            lines.append("  ```")

        return "\n".join(lines)

    def render_html(self, execution_data: Dict[str, Any]) -> str:
        """渲染 HTML 报告"""
        agent_sequence = execution_data.get("agentExecutionSequence", [])
        total_duration = self._calculate_total_duration(execution_data)
        completed = execution_data.get("completed", False)

        html = ['<!DOCTYPE html>']
        html.append('<html lang="zh-CN">')
        html.append('<head>')
        html.append('    <meta charset="UTF-8">')
        html.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html.append('    <title>Agent 执行报告</title>')
        html.append('    <style>')
        html.append('        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 20px; background: #f5f5f5; }')
        html.append('        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }')
        html.append('        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }')
        html.append('        h2 { color: #555; margin-top: 30px; }')
        html.append('        .overview { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }')
        html.append('        .overview-item { background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; }')
        html.append('        .overview-item strong { display: block; color: #666; font-size: 12px; }')
        html.append('        .overview-item span { font-size: 24px; font-weight: bold; color: #333; }')
        html.append('        .timeline { margin: 20px 0; }')
        html.append('        .step { margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 6px; border-left: 4px solid #28a745; }')
        html.append('        .step.error { border-left-color: #dc3545; }')
        html.append('        .step-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }')
        html.append('        .step-title { font-weight: bold; font-size: 16px; }')
        html.append('        .step-duration { color: #666; font-size: 14px; }')
        html.append('        .think-act { margin: 10px 0; padding: 10px; background: white; border-radius: 4px; }')
        html.append('        .think-input { color: #6c757d; font-style: italic; margin-bottom: 8px; }')
        html.append('        .tool-call { display: flex; align-items: center; gap: 8px; padding: 8px; background: #e9ecef; border-radius: 4px; }')
        html.append('        .tool-name { font-family: monospace; font-weight: bold; }')
        html.append('        .tool-success { color: #28a745; }')
        html.append('        .tool-error { color: #dc3545; }')
        html.append('        .tool-result { margin-top: 8px; padding: 8px; background: #f8f9fa; border-radius: 4px; font-size: 12px; }')
        html.append('    </style>')
        html.append('</head>')
        html.append('<body>')
        html.append('    <div class="container">')
        html.append('        <h1>Agent 执行报告</h1>')

        # 概览
        html.append('        <div class="overview">')
        html.append(f'            <div class="overview-item"><strong>总耗时</strong><span>{self._format_duration(total_duration)}</span></div>')
        html.append(f'            <div class="overview-item"><strong>步骤数</strong><span>{len(agent_sequence)}</span></div>')
        html.append(f'            <div class="overview-item"><strong>状态</strong><span>{"✅ 完成" if completed else "🔄 运行中"}</span></div>')
        html.append('        </div>')

        html.append('        <h2>执行时间轴</h2>')
        html.append('        <div class="timeline">')

        # 每个步骤
        for i, step in enumerate(agent_sequence):
            step_name = step.get("stepName", f"Step {i + 1}")
            duration = self._calculate_step_duration(step)
            has_error = self._step_has_error(step)

            error_class = " error" if has_error else ""

            html.append(f'            <div class="step{error_class}">')
            html.append(f'                <div class="step-header">')
            html.append(f'                    <span class="step-title">步骤 {i + 1}: {step_name}</span>')
            html.append(f'                    <span class="step-duration">{duration:.1f}s</span>')
            html.append(f'                </div>')

            # Think-Act 记录
            think_act_steps = step.get("thinkActSteps", [])
            for ta in think_act_steps:
                think_input = ta.get("thinkInput", "")
                if think_input:
                    html.append(f'                <div class="think-act">')
                    html.append(f'                    <div class="think-input">💭 {self._escape_html(think_input[:200])}</div>')

                tool_calls = ta.get("actToolInfoList", [])
                for tc in tool_calls:
                    tool_name = tc.get("toolName", "unknown")
                    exec_status = tc.get("toolExecuteStatus", "unknown")
                    result = tc.get("result", "")

                    status_class = "tool-success" if exec_status == "success" else "tool-error"
                    status_icon = "✅" if exec_status == "success" else "❌"

                    html.append(f'                    <div class="tool-call">')
                    html.append(f'                        <span>{status_icon}</span>')
                    html.append(f'                        <span class="tool-name">{self._escape_html(tool_name)}</span>')
                    html.append(f'                        <span class="{status_class}">{exec_status}</span>')
                    html.append(f'                    </div>')

                    if result:
                        preview = result[:300] + "..." if len(result) > 300 else result
                        html.append(f'                    <div class="tool-result">{self._escape_html(preview)}</div>')

                html.append(f'                </div>')

            html.append(f'            </div>')

        html.append('        </div>')
        html.append('    </div>')
        html.append('</body>')
        html.append('</html>')

        return "\n".join(html)

    def _calculate_total_duration(self, execution_data: Dict[str, Any]) -> float:
        """计算总执行时长（秒）"""
        agent_sequence = execution_data.get("agentExecutionSequence", [])
        if not agent_sequence:
            return 0.0

        start_time = self._parse_time(agent_sequence[0].get("startTime"))
        end_time = None

        for step in agent_sequence:
            step_end = self._parse_time(step.get("endTime"))
            if step_end and (end_time is None or step_end > end_time):
                end_time = step_end

        if start_time and end_time:
            return (end_time - start_time).total_seconds()
        return 0.0

    def _calculate_step_duration(self, step: Dict[str, Any]) -> float:
        """计算单步时长"""
        start = self._parse_time(step.get("startTime"))
        end = self._parse_time(step.get("endTime"))
        if start and end:
            return (end - start).total_seconds()
        return 0.0

    def _step_has_error(self, step: Dict[str, Any]) -> bool:
        """检查步骤是否有错误"""
        think_act_steps = step.get("thinkActSteps", [])
        for ta in think_act_steps:
            tool_calls = ta.get("actToolInfoList", [])
            for tc in tool_calls:
                if tc.get("toolExecuteStatus") != "success":
                    return True
                if "error-report-tool" in tc.get("toolName", ""):
                    return True
        return False

    @staticmethod
    def _parse_time(time_str: Optional[str]) -> Optional[datetime]:
        """解析时间字符串"""
        if not time_str:
            return None
        try:
            return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"

    @staticmethod
    def _escape_html(text: str) -> str:
        """转义 HTML 特殊字符"""
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&#x27;"))


# =============================================================================
# 错误分析器
# =============================================================================

class ErrorAnalyzer:
    """分析执行过程中的错误"""

    def analyze(self, execution_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        分析所有错误

        返回格式：
        [
            {
                "step": 2,
                "tool": "fs-read-file-operator",
                "error_type": "file_not_found",
                "message": "File not found: /path/to/file.txt",
                "suggested_fix": "Check if file path is correct"
            }
        ]
        """
        errors = []
        agent_sequence = execution_data.get("agentExecutionSequence", [])

        for step_idx, step in enumerate(agent_sequence):
            think_act_steps = step.get("thinkActSteps", [])
            for ta in think_act_steps:
                tool_calls = ta.get("actToolInfoList", [])
                for tc in tool_calls:
                    tool_name = tc.get("toolName", "")
                    exec_status = tc.get("toolExecuteStatus", "")
                    result = tc.get("result", "")

                    if exec_status != "success" or "error" in tool_name.lower():
                        error_info = self._analyze_error(tc, step_idx + 1)
                        errors.append(error_info)

        return errors

    def _analyze_error(self, tool_call: Dict[str, Any], step: int) -> Dict[str, Any]:
        """分析单个错误"""
        tool_name = tool_call.get("toolName", "")
        result = tool_call.get("result", "")

        error_type = self._classify_error(result)
        suggested_fix = self._suggest_fix(error_type)

        return {
            "step": step,
            "tool": tool_name,
            "error_type": error_type,
            "message": result[:200] if result else "",
            "suggested_fix": suggested_fix
        }

    def _classify_error(self, error_message: str) -> str:
        """错误分类"""
        error_msg_lower = error_message.lower()

        if "file not found" in error_msg_lower or "no such file" in error_msg_lower:
            return "file_not_found"
        elif "validation" in error_msg_lower or "invalid" in error_msg_lower:
            return "validation_error"
        elif "timeout" in error_msg_lower:
            return "timeout"
        elif "permission" in error_msg_lower:
            return "permission_error"
        else:
            return "unknown_error"

    def _suggest_fix(self, error_type: str) -> str:
        """建议修复方案"""
        suggestions = {
            "file_not_found": "检查文件路径是否正确，或确保文件存在",
            "validation_error": "检查输入数据格式是否符合要求",
            "timeout": "增加超时时间或检查网络连接",
            "permission_error": "检查文件权限设置"
        }
        return suggestions.get(error_type, "请检查错误详情")


# =============================================================================
# 命令行入口
# =============================================================================

def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="Lynxe Agent 时间轴监控与可视化工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 启动新任务并监控
  %(prog)s --execute simple-tool-test --params '{"file_path": "/tmp/test.txt"}'

  # 监控已有任务
  %(prog)s --plan-id plan-xxx

  # 生成 Markdown 报告
  %(prog)s --plan-id plan-xxx --output markdown --output-file report.md
        """
    )

    # 执行模式
    parser.add_argument(
        "--execute", "-e",
        help="工具名称，启动新任务并监控"
    )
    parser.add_argument(
        "--plan-id", "-p",
        help="监控已有任务 ID"
    )
    parser.add_argument(
        "--params",
        help="替换参数 (JSON 格式)"
    )
    parser.add_argument(
        "--service-group", "-g",
        help="服务组名称"
    )

    # 输出格式
    parser.add_argument(
        "--output", "-o",
        choices=["console", "markdown", "html"],
        default="console",
        help="输出格式 (默认: console)"
    )
    parser.add_argument(
        "--output-file", "-f",
        help="输出到文件"
    )

    # 监控选项
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=2.0,
        help="轮询间隔（秒，默认: 2.0）"
    )
    parser.add_argument(
        "--no-monitor",
        action="store_true",
        help="不实时监控，直接获取结果"
    )

    # 服务器配置
    parser.add_argument(
        "--server", "-s",
        default="http://localhost:8080",
        help="服务器地址 (默认: http://localhost:8080)"
    )

    args = parser.parse_args()

    # 初始化
    client = LynxeClient(args.server)
    monitor = TimelineMonitor(client, args.poll_interval)
    visualizer = TimelineVisualizer()

    plan_id = args.plan_id

    # 启动新任务
    if args.execute:
        params = None
        if args.params:
            try:
                params = json.loads(args.params)
            except json.JSONDecodeError as e:
                print(f"错误: JSON 参数解析失败: {e}")
                sys.exit(1)

        result = client.execute_async(
            tool_name=args.execute,
            replacement_params=params,
            service_group=args.service_group
        )
        plan_id = result.get("planId")
        print(f"✅ 任务已启动: {plan_id}")

    # 监控任务
    if not plan_id:
        parser.error("必须指定 --execute 或 --plan-id")

    if args.no_monitor:
        # 直接获取结果
        execution_data = client.get_execution_details(plan_id)
    else:
        # 实时监控
        execution_data = monitor.monitor(plan_id)

    if execution_data is None:
        print("❌ 获取执行详情失败")
        sys.exit(1)

    # 生成输出
    if args.output == "console":
        print("\n" + visualizer.render_ascii_timeline(execution_data))
    elif args.output == "markdown":
        md = visualizer.render_markdown(execution_data)
        if args.output_file:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"✅ Markdown 报告已保存到: {args.output_file}")
        else:
            print(md)
    elif args.output == "html":
        html = visualizer.render_html(execution_data)
        if args.output_file:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"✅ HTML 报告已保存到: {args.output_file}")
        else:
            print(html)

    # 错误分析
    analyzer = ErrorAnalyzer()
    errors = analyzer.analyze(execution_data)
    if errors:
        print("\n⚠️ 发现错误:")
        for err in errors:
            print(f"  步骤 {err['step']} - {err['tool']}: {err['error_type']}")
            if err['message']:
                print(f"    消息: {err['message'][:100]}")
            print(f"    建议: {err['suggested_fix']}")


if __name__ == "__main__":
    main()
