import sys
import json
import time
import requests
import datetime

# Configuration
BASE_URL = "http://localhost:18080"
TEMPLATE_FILE = "example/robust-data-repair.json"
TEST_DATA_FILE = "example/test-data/corrupted_sales.csv"
TOOL_NAME_IN_JSON = "robust-data-repair-workflow" # Title in JSON
# Note: internal tool name might be `data-repair-robust-data-repair-workflow` but API uses Title.

def print_header():
    print("=" * 60)
    print("🚀 Robust Data Repair Workflow Execution & Visualization")
    print("=" * 60)
    print(f"Time: {datetime.datetime.now().strftime('%H:%M:%S')}")
    print("-" * 60)

def import_template():
    print("📦 Importing Workflow Template...")
    # Delete first to ensure clean state
    requests.delete(f"{BASE_URL}/api/plan-template/details/planTemplate-robust-data-repair-workflow")
    
    with open(TEMPLATE_FILE, 'r') as f:
        template_data = json.load(f)
        
    # Wrap in list as import-all expects list
    res = requests.post(f"{BASE_URL}/api/plan-template/import-all", json=[template_data])
    if res.status_code == 200:
        print("✅ Template Imported.")
    else:
        print(f"❌ Import Failed: {res.text}")
        sys.exit(1)

def upload_file():
    print("📂 Uploading Corrupted Data File...")
    with open(TEST_DATA_FILE, 'rb') as f:
        files = {'files': (TEST_DATA_FILE.split('/')[-1], f)}
        res = requests.post(f"{BASE_URL}/api/file-upload/upload", files=files)
        
    if res.status_code == 200:
        data = res.json()
        key = data.get('uploadKey')
        print(f"✅ File Uploaded. Key: {key}")
        return key
    else:
        print(f"❌ Upload Failed: {res.text}")
        sys.exit(1)

def start_workflow(upload_key):
    print("▶️ Starting Workflow...")
    payload = {
        "toolName": TOOL_NAME_IN_JSON,
        "serviceGroup": "data-repair",
        "uploadKey": upload_key,
        "replacementParams": {
            "file_path": "corrupted_sales.csv"
        }
    }
    res = requests.post(f"{BASE_URL}/api/executor/executeByToolNameAsync", json=payload)
    if res.status_code == 200:
        data = res.json()
        plan_id = data.get('planId')
        print(f"✅ Workflow Started. Plan ID: {plan_id}")
        return plan_id
    else:
        print(f"❌ Execution Start Failed: {res.text}")
        sys.exit(1)

def format_time_str(ts_list):
    if not ts_list: return ""
    # [Y, M, D, H, M, S, N]
    dt = datetime.datetime(*ts_list[:6])
    return dt.strftime("%H:%M:%S")

def visualize_timeline(plan_id):
    print("\n📊 Waiting for Execution Updates...\n")
    
    processed_steps = set()
    last_status = ""
    
    start_time = time.time()
    while time.time() - start_time < 120: # 2 min timeout
        try:
            res = requests.get(f"{BASE_URL}/api/executor/details/{plan_id}")
            if res.status_code != 200: continue
            
            details = res.json()
            completed = details.get('completed', False)
            steps = details.get('agentExecutionSequence', [])
            steps.sort(key=lambda x: x.get('currentStep', 0))
            
            # Check for new steps or updates
            for step in steps:
                step_idx = step.get('currentStep')
                step_id = step.get('id') # specific execution id
                step_status = step.get('status')
                
                # Unique identifier for this step state output
                unique_key = f"{step_id}_{step_status}"
                
                if unique_key not in processed_steps:
                    processed_steps.add(unique_key)
                    
                    # Print Step Header
                    agent_req = step.get('agentRequest')
                    if agent_req:
                        req_lines = agent_req.split('\n')
                        header = req_lines[0]
                    else:
                        header = f"Step {step_idx} (Initializing...)"
                    
                    print(f"\n🔹 [Step {step_idx}] {header}")
                    print(f"   Status: {step_status}")
                    
                    if step.get('startTime'):
                         print(f"   Started: {format_time_str(step.get('startTime'))}")
                    
                    # Check for Think/Act
                    think_acts = step.get('thinkActSteps', [])
                    for ta in think_acts:
                         print(f"   🤔 Thinking: {ta.get('thinkOutput', '')[:100]}...")
                         for tool in ta.get('actToolInfoList', []):
                             t_name = tool.get('toolName')
                             print(f"   🛠️  Tool Call: {t_name}")
                             if t_name == "fs-write-file-operator":
                                 print(f"   ⚠️  REPAIR ACTION DETECTED: Modifying file...")

                    # Check for Final Result (latestMethodArgs)
                    if step_status == 'FINISHED':
                        args = step.get('latestMethodArgs')
                        print(f"   ✅ Finished. Result summary provided.")
                        # Could parse JSON here if needed
            
            if completed:
                print("\n🎉 Workflow Completed Successfully!")
                break
                
            time.sleep(2)
        except Exception as e:
            print(f"Error polling: {e}")
            break

def main():
    print_header()
    import_template()
    upload_key = upload_file()
    plan_id = start_workflow(upload_key)
    visualize_timeline(plan_id)

if __name__ == "__main__":
    main()
