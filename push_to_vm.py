# push_to_vm.py
import os
import sys
import json
import paramiko

# VM Connection Settings — loaded from db_config.json (vm_host/vm_port/vm_user/vm_pass)
def _vm_cfg():
    paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db_config.json'),
        r'F:\co work dashboard\db_config.json',
    ]
    for p in paths:
        if os.path.exists(p):
            cfg = json.load(open(p, encoding='utf-8'))
            return cfg['vm_host'], int(cfg['vm_port']), cfg['vm_user'], cfg['vm_pass']
    raise FileNotFoundError('db_config.json not found — add vm_host/vm_port/vm_user/vm_pass keys')

VM_HOST, VM_PORT, VM_USER, VM_PASS = _vm_cfg()
REMOTE_DIR = "/home/agent-worker/dashboard"

FILES_TO_TEST = [
    "index.html",
    "sales_dashboard_v8.html",
    "fraud_dashboard.html",
    "product_dashboard.html",
    "index_for_lost_product.html",
    "lost_product_dashboard.html",
    "gp_analysis_dashboard.html",
    "dead_stock_dashboard.html",
    "visual_adj_dashboard.html",
    "analytics.js"
]

def main():
    folder = os.path.dirname(os.path.abspath(__file__))
    
    # Check which local files actually exist
    files_to_upload = []
    for fname in FILES_TO_TEST:
        local_path = os.path.join(folder, fname)
        if os.path.exists(local_path):
            files_to_upload.append((fname, local_path))
            
    if not files_to_upload:
        print("Error: No testable dashboard files found in this directory.")
        sys.exit(1)
        
    print(f"Connecting to VM at {VM_USER}@{VM_HOST}:{VM_PORT}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(VM_HOST, port=VM_PORT, username=VM_USER, password=VM_PASS, timeout=15)
        print("Connected successfully!")
        
        sftp = client.open_sftp()
        
        print(f"\nUploading files directly to VM ({REMOTE_DIR}):")
        for fname, local_path in files_to_upload:
            remote_path = f"{REMOTE_DIR}/{fname}"
            size_kb = os.path.getsize(local_path) // 1024
            print(f"  Uploading {fname} ({size_kb:,} KB) ...", end=" ", flush=True)
            try:
                sftp.put(local_path, remote_path)
                print("OK")
            except Exception as e:
                print(f"FAILED: {e}")
                
        sftp.close()
        print("\nAll uploads completed!")
        print(f"Verify instantly at: http://agent-ab-sandbox.tjinternal.com:48081/")
        
    except Exception as e:
        print(f"\nSSH connection or upload failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
