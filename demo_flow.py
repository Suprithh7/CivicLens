import requests
import os
import sys
import time
import json

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
PDF_FILENAME = "Sample_Student_Loan_Policy.pdf"
SAMPLE_PDF_SCRIPT = "create_sample_pdf.py"

def check_server():
    """Check if the backend server is running."""
    try:
        response = requests.get(f"{BASE_URL}/simplification/health")
        if response.status_code == 200:
            print("✅ Backend server is online.")
            return True
        else:
            print(f"⚠️ Backend server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server.")
        print("Please ensure the backend is running at http://localhost:8000")
        print("Run: uvicorn app.main:app --reload")
        return False

def generate_pdf():
    """Generate the sample PDF if it doesn't exist."""
    if not os.path.exists(PDF_FILENAME):
        print(f"Generating {PDF_FILENAME}...")
        try:
            # Import dynamically to avoid issues if dependency missing
            import importlib.util
            spec = importlib.util.spec_from_file_location("create_sample_pdf", SAMPLE_PDF_SCRIPT)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                print("✅ PDF generated successfully.")
            else:
                print(f"❌ Could not load {SAMPLE_PDF_SCRIPT}")
                return False
        except Exception as e:
            print(f"❌ Failed to generate PDF: {e}")
            # Fallback: try running as subprocess
            try:
                os.system(f"python {SAMPLE_PDF_SCRIPT}")
            except:
                return False
            return os.path.exists(PDF_FILENAME)
    else:
        print(f"✅ {PDF_FILENAME} already exists.")
    return True

def upload_policy():
    """Upload the policy PDF."""
    url = f"{BASE_URL}/policies/upload"
    file_path = os.path.abspath(PDF_FILENAME)
    
    print(f"\n📤 Uploading {PDF_FILENAME}...")
    
    with open(file_path, "rb") as f:
        files = {"file": (PDF_FILENAME, f, "application/pdf")}
        try:
            response = requests.post(url, files=files)
            if response.status_code == 201:
                data = response.json()
                print(f"✅ Upload successful! Policy ID: {data['policy_id']}")
                return data['policy_id']
            elif response.status_code == 409:
                # File already exists, try to get it from list or just fail gracefully
                print("⚠️ Policy already exists.")
                
                # Try to parse ID from error message
                if "detail" in response.json():
                    detail = response.json().get("detail", "")
                    if isinstance(detail, str) and ":" in detail:
                        policy_id = detail.split(":")[-1].strip()
                        print(f"ℹ️ Using existing Policy ID from error: {policy_id}")
                        return policy_id
                
                # Fallback: List policies and find by filename
                print("ℹ️ Searching for existing policy by filename...")
                list_url = f"{BASE_URL}/policies/list?limit=100"
                list_response = requests.get(list_url)
                if list_response.status_code == 200:
                    policies = list_response.json().get("policies", [])
                    for p in policies:
                        if p.get("filename") == PDF_FILENAME:
                            print(f"✅ Found existing policy: {p['policy_id']}")
                            return p['policy_id']
                
                print("❌ Could not find valid Policy ID for existing file.")
                return None
            else:
                print(f"❌ Upload failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return None

def extract_text(policy_id):
    """Trigger text extraction."""
    url = f"{BASE_URL}/policies/{policy_id}/extract-text"
    print(f"\n🔍 Extracting text for Policy ID: {policy_id}...")
    
    try:
        response = requests.post(url, params={"force": "true"}) # Force consistent demo behavior
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Extraction started/completed. Status: {data.get('status')}")
            print(f"📊 Character count: {data.get('character_count')}")
            return True
        else:
            print(f"❌ Extraction failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Extraction error: {e}")
        return False

def simplify_policy(policy_id):
    """Get simplified explanation."""
    url = f"{BASE_URL}/simplification/explain"
    print(f"\n🧠 Generating simplified explanation...")
    
    payload = {
        "policy_id": policy_id,
        "explanation_type": "explanation",
        "focus_area": "eligibility and benefits"
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Simplification complete ({duration:.2f}s)!")
            print("\n" + "="*50)
            print(f"📜 {data.get('policy_title', 'Policy Explanation')}")
            print("="*50)
            print(data.get('simplified_text'))
            print("="*50)
            return True
        else:
            error_msg = f"❌ Simplification failed: {response.status_code} - {response.text}"
            print(error_msg[:200] + "...") # Print snippet
            with open("error.log", "w", encoding="utf-8") as f:
                f.write(error_msg)
            return False
    except Exception as e:
        print(f"❌ Simplification error: {e}")
        return False

def main():
    print("🚀 Starting CivicLens Demo Flow")
    print("="*30)
    
    if not check_server():
        return
        
    if not generate_pdf():
        return
        
    policy_id = upload_policy()
    if not policy_id:
        return
        
    if not extract_text(policy_id):
        return
        
    # Small pause to ensure DB consistency if async (though endpoints seemed awaited)
    time.sleep(1)
    
    if not simplify_policy(policy_id):
        return
        
    print("\n✨ Demo completed successfully!")

if __name__ == "__main__":
    main()
