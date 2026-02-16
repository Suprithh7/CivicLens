import requests
import json

def test_rag():
    url = "http://localhost:8000/api/v1/rag/ask"
    payload = {
        "query": "What are the income requirements?",
        "policy_id": "pol_r273wvl3zcx5"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response:", json.dumps(response.json(), indent=2))
        else:
            print("Error:", response.text)
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_rag()
    
    # Also test simplification with evaluation
    print("\nTesting Simplification Evaluation...")
    simplification_url = "http://localhost:8000/api/v1/simplify/explain"
    simplification_payload = {
        "policy_id": "pol_r273wvl3zcx5",
        "explanation_type": "explanation",
        "focus_area": "income requirements"
    }
    
    try:
        response = requests.post(simplification_url, json=simplification_payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Evaluation Metics:")
            if result.get("evaluation"):
                print(json.dumps(result["evaluation"], indent=2))
            else:
                print("No evaluation metrics returned")
        else:
            print("Error:", response.text)
    except Exception as e:
        print(f"Simplification request failed: {e}")
