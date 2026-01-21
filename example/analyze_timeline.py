import json
import sys
import datetime

def format_time(timestamp_list):
    if not timestamp_list:
        return "N/A"
    # timestamp_list is typically [year, month, day, hour, minute, second, nanos]
    try:
        dt = datetime.datetime(*timestamp_list[:6])
        # Add micros/nanos if present
        if len(timestamp_list) > 6:
            dt = dt.replace(microsecond=int(timestamp_list[6] / 1000))
        return dt.strftime("%H:%M:%S.%f")[:-3]
    except Exception:
        return str(timestamp_list)

def safe_get(d, key, default=None):
    return d.get(key, default)

def analyze_timeline(json_path, output_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        sys.exit(1)

    with open(output_path, 'w', encoding='utf-8') as out:
        plan_id = data.get('currentPlanId', 'Unknown')
        title = data.get('title', 'Unknown Plan')
        start_time = format_time(data.get('startTime'))
        end_time = format_time(data.get('endTime'))

        out.write(f"# Execution Timeline Report\n\n")
        out.write(f"**Plan Title:** {title}\n")
        out.write(f"**Plan ID:** {plan_id}\n")
        out.write(f"**Start Time:** {start_time}\n")
        out.write(f"**End Time:** {end_time}\n")
        out.write(f"**Status:** {'Completed' if data.get('completed') else 'Running/Failed'}\n\n")

        steps = data.get('agentExecutionSequence', [])
        steps.sort(key=lambda x: safe_get(x, 'currentStep', 0))

        for step in steps:
            step_idx = step.get('currentStep', '?')
            agent_req = step.get('agentRequest', 'No Goal')
            # Extract first line of request as header if multi-line
            req_header = agent_req.split('\n')[0] if agent_req else "Step " + str(step_idx)
            
            s_start = format_time(step.get('startTime'))
            s_end = format_time(step.get('endTime'))
            
            out.write(f"## Step {step_idx}: {req_header}\n")
            out.write(f"**Time:** {s_start} - {s_end}\n")
            out.write(f"**Agent:** {step.get('agentName', 'Unknown')}\n\n")

            # Agent Request Full
            out.write(f"### 📋 Request (Prompt)\n")
            out.write(f"```text\n{agent_req}\n```\n\n")

            # Think-Act Steps (Detailed Reasoning)
            think_acts = step.get('thinkActSteps', [])
            if think_acts:
                out.write(f"### 🤔 Reasoning & Actions\n")
                for i, ta in enumerate(think_acts):
                    t_time = format_time(ta.get('recordTime'))
                    out.write(f"#### Turn {i+1} ({t_time})\n")
                    
                    think_input = ta.get('thinkInput', '')
                    think_output = ta.get('thinkOutput', '')
                    
                    if think_output:
                        out.write(f"**Thinking Process:**\n> {think_output.replace(chr(10), chr(10)+'> ')}\n\n")
                    
                    # Tool Calls
                    tools = ta.get('actToolInfoList', [])
                    for tool in tools:
                        t_name = tool.get('toolName', 'Unknown')
                        t_args = tool.get('args', '{}')
                        t_res = tool.get('result', '')
                        
                        out.write(f"**🛠️ Tool Call:** `{t_name}`\n")
                        out.write(f"**Args:** `{t_args}`\n")
                        if t_res:
                            # Truncate long results
                            display_res = t_res if len(t_res) < 500 else t_res[:500] + "... (truncated)"
                            out.write(f"**Result:**\n```\n{display_res}\n```\n\n")
            else:
                out.write(f"> *No intermediate think-act steps recorded (Direct termination or simple execution)*\n\n")

            # Final Step Result (Latest Method)
            latest_method = step.get('latestMethodName')
            latest_args = step.get('latestMethodArgs')
            
            if latest_method == 'default-terminate':
                out.write(f"### 🏁 Step Completion (Result)\n")
                # Try to parse arguments if they are JSON string
                try:
                    if isinstance(latest_args, str):
                        args_json = json.loads(latest_args)
                        # Extract the key message
                        if isinstance(args_json, dict) and 'message' in args_json:
                            msg_list = args_json['message']
                            for msg in msg_list:
                                for k, v in msg.items():
                                    out.write(f"**{k}:**\n{v}\n\n")
                        else:
                             out.write(f"```json\n{latest_args}\n```\n\n")
                    else:
                        out.write(f"```json\n{json.dumps(latest_args, indent=2)}\n```\n\n")
                except:
                    out.write(f"```\n{latest_args}\n```\n\n")
            
            out.write("---\n")

    print(f"Timeline report generated at: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 analyze_timeline.py <json_path> <output_path>")
        sys.exit(1)
    
    analyze_timeline(sys.argv[1], sys.argv[2])
