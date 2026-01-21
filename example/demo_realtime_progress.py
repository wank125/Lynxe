#!/usr/bin/env python3
"""
演示实时进度监控功能

使用模拟数据展示实时监控界面的效果
"""

import time
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def demo_realtime_progress():
    """演示实时进度条的效果"""

    print("\n" + "=" * 70)
    print("实时进度监控演示")
    print("=" * 70)

    print("\n🚀 开始监控任务: demo-plan-123")
    print("=" * 70)
    print(f"{'状态':<8} {'进度':<30} {'步骤':<20} {'耗时'}")
    print("-" * 70)

    spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    spinner_idx = 0

    steps = [
        {"name": "读取和验证数据文件", "duration": 2.5, "has_think": True},
        {"name": "处理和转换数据", "duration": 1.8, "has_think": True},
        {"name": "错误检测和恢复", "duration": 3.2, "has_error": True, "has_think": True},
        {"name": "生成最终报告", "duration": 1.5, "has_think": True}
    ]

    total_steps = len(steps)
    elapsed = 0

    for i, step in enumerate(steps):
        # 模拟步骤执行过程
        step_elapsed = 0
        step_duration = step["duration"]

        # 在步骤执行过程中显示动态进度
        while step_elapsed < step_duration:
            step_elapsed += 0.1
            elapsed += 0.1

            # 更新进度条
            progress_percent = int(((i + step_elapsed / step_duration) / total_steps) * 100)
            bar_width = 20
            filled = int(bar_width * progress_percent / 100)
            bar = "█" * filled + "░" * (bar_width - filled)

            spinner = spinner_frames[spinner_idx % len(spinner_frames)]
            spinner_idx += 1

            step_name = step["name"]
            if len(step_name) > 18:
                step_name = step_name[:15] + "..."

            # 同行更新进度条
            sys.stdout.write(f"\r{spinner:<7} [{bar}] {progress_percent:3d}% | {step_name:<18} | {elapsed:5.1f}s")
            sys.stdout.flush()

            time.sleep(0.1)

        # 步骤完成，打印详细信息
        print()  # 换行

        # 打印步骤详情
        indent = "  "
        status_icon = "⚠️" if step.get("has_error") else "✅"
        status_text = "有错误" if step.get("has_error") else "完成"

        print(f"{indent}[{i+1}/{total_steps}] {status_icon} {status_text}: {step['name']} ({step['duration']:.2f}s)")

        if step.get("has_think"):
            print(f"{indent}    💭 Turn 1: 分析任务需求并制定执行计划...")

        if step.get("has_error"):
            print(f"{indent}    ❌ fs-read-file-operator")
            print(f"{indent}    💭 Turn 2: 检测到文件不存在，需要执行恢复操作...")
            print(f"{indent}    ✅ error-report-tool")
            print(f"{indent}    ✅ fs-replace-file-operator")
        else:
            print(f"{indent}    ✅ 工具调用成功")

        print()  # 步骤后空行

    # 最终完成显示
    print("\r" + " " * 120 + "\r", end="")
    print(f"{'✅ 完成':<8} [{'█' * 20}] 100% | {total_steps} 步骤 | {elapsed:5.1f}s")
    print("=" * 70)
    print(f"✅ 任务完成！总耗时: {elapsed:.2f}秒 | 步骤数: {total_steps}")
    print()


def demo_error_recovery():
    """演示错误恢复场景的实时监控"""

    print("\n" + "=" * 70)
    print("错误恢复场景演示")
    print("=" * 70)

    print("\n🚀 开始监控任务: demo-error-recovery")
    print("=" * 70)
    print(f"{'状态':<8} {'进度':<30} {'步骤':<20} {'耗时'}")
    print("-" * 70)

    spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    spinner_idx = 0

    # 模拟一个有错误的执行流程
    scenario = [
        {"name": "读取输入文件", "duration": 1.5, "status": "success"},
        {"name": "验证数据格式", "duration": 2.0, "status": "error"},  # 这一步会出错
        {"name": "自动修复数据", "duration": 1.8, "status": "recovery"},  # 恢复步骤
        {"name": "重新验证", "duration": 1.2, "status": "success"},
        {"name": "生成报告", "duration": 1.0, "status": "success"}
    ]

    total_steps = len(scenario)
    elapsed = 0

    for i, step in enumerate(scenario):
        step_elapsed = 0
        step_duration = step["duration"]

        # 动态进度更新
        while step_elapsed < step_duration:
            step_elapsed += 0.1
            elapsed += 0.1

            progress_percent = int(((i + step_elapsed / step_duration) / total_steps) * 100)
            bar_width = 20
            filled = int(bar_width * progress_percent / 100)
            bar = "█" * filled + "░" * (bar_width - filled)

            spinner = spinner_frames[spinner_idx % len(spinner_frames)]
            spinner_idx += 1

            step_name = step["name"]
            if len(step_name) > 18:
                step_name = step_name[:15] + "..."

            sys.stdout.write(f"\r{spinner:<7} [{bar}] {progress_percent:3d}% | {step_name:<18} | {elapsed:5.1f}s")
            sys.stdout.flush()

            time.sleep(0.1)

        print()

        # 根据状态显示不同的图标和信息
        indent = "  "
        if step["status"] == "success":
            status_icon = "✅"
            status_text = "完成"
        elif step["status"] == "error":
            status_icon = "❌"
            status_text = "失败"
        elif step["status"] == "recovery":
            status_icon = "🔧"
            status_text = "修复中"
        else:
            status_icon = "✅"
            status_text = "完成"

        print(f"{indent}[{i+1}/{total_steps}] {status_icon} {status_text}: {step['name']} ({step['duration']:.2f}s)")

        # 显示详情
        if step["status"] == "error":
            print(f"{indent}    💭 Turn 1: 尝试读取文件 /tmp/data.csv")
            print(f"{indent}    ❌ fs-read-file-operator")
            print(f"{indent}    💭 检测到错误: 文件格式不符合预期")
            print(f"{indent}    💭 Turn 2: 启动错误恢复流程...")
            print(f"{indent}    ✅ error-report-tool")
        elif step["status"] == "recovery":
            print(f"{indent}    💭 Turn 3: 使用修复工具处理文件...")
            print(f"{indent}    ✅ fs-replace-file-operator")
            print(f"{indent}    💭 修复完成，继续执行...")
        else:
            print(f"{indent}    💭 执行任务并处理结果")
            print(f"{indent}    ✅ 工具调用完成")

        print()

    print("\r" + " " * 120 + "\r", end="")
    print(f"{'✅ 完成':<8} [{'█' * 20}] 100% | {total_steps} 步骤 | {elapsed:5.1f}s")
    print("=" * 70)
    print(f"✅ 任务完成！总耗时: {elapsed:.2f}秒 | 步骤数: {total_steps}")
    print()
    print("⚠️  发现错误:")
    print("  步骤 2 - fs-read-file-operator: file_not_found")
    print("    建议: 检查文件路径是否正确，或确保文件存在")
    print()


if __name__ == "__main__":
    print("\n" + "🎯" * 35)
    print("实时进度监控功能演示")
    print("🎯" * 35)

    # 演示1: 正常执行流程
    demo_realtime_progress()

    time.sleep(1)

    # 演示2: 错误恢复流程
    demo_error_recovery()

    print("=" * 70)
    print("演示完成！")
    print("=" * 70)
    print("\n💡 提示: 在实际使用中，进度条会实时更新，")
    print("   每个步骤完成后会显示详细信息和思考过程。")
