import sys
import json
import base64
import requests

def fetch_and_save_report(plan_id, file_path, output_path):
    url = f"http://localhost:18080/api/file-browser/content/{plan_id}"
    params = {"path": file_path}
    
    try:
        print(f"Fetching {file_path} from plan {plan_id}...")
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching file: {response.status_code} - {response.text}")
            sys.exit(1)
            
        data = response.json()
        if not data.get("success"):
             print(f"API Error: {data.get('message')}")
             sys.exit(1)
             
        file_data = data.get("data", {})
        content = file_data.get("content", "")
        is_binary = file_data.get("isBinary", False)
        
        if is_binary and content:
            print("Decoding Base64 content...")
            decoded_bytes = base64.b64decode(content)
            with open(output_path, 'wb') as f:
                f.write(decoded_bytes)
        else:
            print("Writing text content...")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        print(f"Successfully saved to {output_path}")
        
    except Exception as e:
        print(f"Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 fetch_report.py <plan_id> <remote_path> <local_path>")
        sys.exit(1)
        
    fetch_and_save_report(sys.argv[1], sys.argv[2], sys.argv[3])
