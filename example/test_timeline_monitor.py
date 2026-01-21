#!/usr/bin/env python3
"""
测试时间轴监控工具的功能

使用模拟数据测试各种可视化功能
"""

import json
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from timeline_monitor import TimelineVisualizer, ErrorAnalyzer


def create_mock_execution_data():
    """创建模拟的执行数据用于测试"""
    return {
        "rootPlanId": "plan-test-123",
        "currentPlanId": "plan-test-123",
        "completed": True,
        "agentExecutionSequence": [
            {
                "stepId": "step-1",
                "stepName": "Read and Validate Data",
                "startTime": "2026-01-21T12:00:00.000000",
                "endTime": "2026-01-21T12:00:02.500000",
                "thinkActSteps": [
                    {
                        "turnNumber": 1,
                        "thinkInput": "I need to read the file first to validate its content. The file path is /tmp/test-data.csv",
                        "thinkOutput": "I'll use the fs-read-file-operator to read the file content.",
                        "actToolInfoList": [
                            {
                                "toolName": "fs-read-file-operator",
                                "parameters": {"file_path": "/tmp/test-data.csv"},
                                "result": "name,id,value\nAlice,1,100\nBob,2,200\nCharlie,3,300",
                                "toolExecuteStatus": "success"
                            }
                        ]
                    },
                    {
                        "turnNumber": 2,
                        "thinkInput": "File read successfully. Now I need to count the lines to verify the data.",
                        "thinkOutput": "I'll use fs-count-file to get the line count.",
                        "actToolInfoList": [
                            {
                                "toolName": "fs-count-file",
                                "parameters": {"file_path": "/tmp/test-data.csv"},
                                "result": "Total lines: 4 (including header)",
                                "toolExecuteStatus": "success"
                            }
                        ]
                    }
                ]
            },
            {
                "stepId": "step-2",
                "stepName": "Process and Transform Data",
                "startTime": "2026-01-21T12:00:02.500000",
                "endTime": "2026-01-21T12:00:05.000000",
                "thinkActSteps": [
                    {
                        "turnNumber": 1,
                        "thinkInput": "Now I need to process the CSV data. I should validate the format and clean the data.",
                        "thinkOutput": "The data looks good. I have 3 data rows with valid format. All values are numeric.",
                        "actToolInfoList": []
                    }
                ]
            },
            {
                "stepId": "step-3",
                "stepName": "Error Recovery (File Not Found)",
                "startTime": "2026-01-21T12:00:05.000000",
                "endTime": "2026-01-21T12:00:08.500000",
                "thinkActSteps": [
                    {
                        "turnNumber": 1,
                        "thinkInput": "I need to read the output template file.",
                        "thinkOutput": "I'll try to read /tmp/template.txt",
                        "actToolInfoList": [
                            {
                                "toolName": "fs-read-file-operator",
                                "parameters": {"file_path": "/tmp/template.txt"},
                                "result": "Error: File not found: /tmp/template.txt",
                                "toolExecuteStatus": "error"
                            }
                        ]
                    },
                    {
                        "turnNumber": 2,
                        "thinkInput": "The template file doesn't exist. I should report this error and create a default template.",
                        "thinkOutput": "I'll use error-report-tool to log this issue, then create a new template.",
                        "actToolInfoList": [
                            {
                                "toolName": "error-report-tool",
                                "parameters": {"error_type": "file_not_found"},
                                "result": "Error logged: Template file not found. Recovery action: Creating default template.",
                                "toolExecuteStatus": "success"
                            },
                            {
                                "toolName": "fs-replace-file-operator",
                                "parameters": {
                                    "file_path": "/tmp/template.txt",
                                    "content": "# Default Template\nGenerated automatically due to missing original."
                                },
                                "result": "Successfully created default template file at /tmp/template.txt",
                                "toolExecuteStatus": "success"
                            }
                        ]
                    }
                ]
            },
            {
                "stepId": "step-4",
                "stepName": "Generate Final Report",
                "startTime": "2026-01-21T12:00:08.500000",
                "endTime": "2026-01-21T12:00:10.000000",
                "thinkActSteps": [
                    {
                        "turnNumber": 1,
                        "thinkInput": "Now I need to compile all results and generate the final report.",
                        "thinkOutput": "I'll create a comprehensive report with all the findings.",
                        "actToolInfoList": [
                            {
                                "toolName": "fs-write-file-operator",
                                "parameters": {
                                    "file_path": "/tmp/final-report.md",
                                    "content": "# Data Processing Report\n\n## Summary\n- Processed 3 records\n- Total execution time: 10 seconds\n- Errors recovered: 1 (missing template)"
                                },
                                "result": "Report successfully saved to /tmp/final-report.md",
                                "toolExecuteStatus": "success"
                            }
                        ]
                    }
                ]
            }
        ]
    }


def main():
    """运行测试"""
    print("=" * 60)
    print("时间轴监控工具 - 功能测试")
    print("=" * 60)

    # 创建模拟数据
    execution_data = create_mock_execution_data()

    # 初始化可视化器和错误分析器
    visualizer = TimelineVisualizer()
    analyzer = ErrorAnalyzer()

    print("\n1. 测试 ASCII 时间轴渲染\n")
    print("-" * 60)
    ascii_timeline = visualizer.render_ascii_timeline(execution_data)
    print(ascii_timeline)

    print("\n2. 测试 Markdown 报告生成\n")
    print("-" * 60)
    markdown_report = visualizer.render_markdown(execution_data)
    print(markdown_report[:500] + "...\n[报告已截断]")

    # 保存完整的 Markdown 报告
    output_path = "/tmp/test_execution_report.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_report)
    print(f"\n✅ 完整 Markdown 报告已保存到: {output_path}")

    print("\n3. 测试 HTML 报告生成\n")
    print("-" * 60)
    html_report = visualizer.render_html(execution_data)

    # 保存 HTML 报告
    html_output_path = "/tmp/test_execution_report.html"
    with open(html_output_path, "w", encoding="utf-8") as f:
        f.write(html_report)
    print(f"✅ HTML 报告已保存到: {html_output_path}")
    print(f"   在浏览器中打开查看: file://{html_output_path}")

    print("\n4. 测试错误分析\n")
    print("-" * 60)
    errors = analyzer.analyze(execution_data)
    if errors:
        print(f"发现 {len(errors)} 个错误:")
        for err in errors:
            print(f"\n  步骤 {err['step']}:")
            print(f"    工具: {err['tool']}")
            print(f"    类型: {err['error_type']}")
            print(f"    消息: {err['message'][:80]}")
            print(f"    建议: {err['suggested_fix']}")
    else:
        print("未发现错误")

    print("\n5. 保存完整的 JSON 数据\n")
    print("-" * 60)
    json_output_path = "/tmp/test_execution_data.json"
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(execution_data, f, indent=2, ensure_ascii=False)
    print(f"✅ 完整执行数据已保存到: {json_output_path}")
    print("   可以使用以下命令查看时间轴:")
    print(f"   python3 timeline_monitor.py --plan-id plan-test-123 --no-monitor")
    print(f"   (需要后端服务运行并提供该 planId 的数据)")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
