#!/usr/bin/env python3
"""
Test script for system prompt API endpoints
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_system_prompts_api():
    """Test all system prompt API endpoints"""
    print("Testing System Prompt API Endpoints...")
    print("=" * 50)
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    try:
        # Test 1: Get all system prompts
        print("\n1. Testing GET /system-prompts")
        response = requests.get(f"{BASE_URL}/system-prompts")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {len(data['prompts'])} prompts")
            print(f"   Active prompt: {data['active_prompt_id']}")
            for prompt in data['prompts']:
                print(f"   - {prompt['id']}: {prompt['config']['name']}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return
        
        # Test 2: Get active system prompt
        print("\n2. Testing GET /system-prompts/active")
        response = requests.get(f"{BASE_URL}/system-prompts/active")
        if response.status_code == 200:
            active_prompt = response.json()
            print(f"✅ Success! Active prompt: {active_prompt['config']['name']}")
            print(f"   Description: {active_prompt['config']['description']}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
        
        # Test 3: Create a new system prompt
        print("\n3. Testing POST /system-prompts (Create new prompt)")
        new_prompt = {
            "prompt_id": "test_prompt",
            "config": {
                "name": "Test Assistant",
                "description": "A test assistant for API testing",
                "instructions": [
                    "You are a test assistant.",
                    "Always mention that you are in test mode.",
                    "Be helpful and concise."
                ],
                "additional_context": "This is a test prompt created via API",
                "expected_output": "Clear and concise responses",
                "markdown": True,
                "add_datetime_to_instructions": False
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/system-prompts", 
            json=new_prompt,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("✅ Success! Created new test prompt")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
        
        # Test 4: Get specific prompt by ID
        print("\n4. Testing GET /system-prompts/{prompt_id}")
        response = requests.get(f"{BASE_URL}/system-prompts/test_prompt")
        if response.status_code == 200:
            prompt = response.json()
            print(f"✅ Success! Retrieved prompt: {prompt['config']['name']}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
        
        # Test 5: Set active system prompt
        print("\n5. Testing POST /system-prompts/active (Set active)")
        response = requests.post(
            f"{BASE_URL}/system-prompts/active",
            json={"prompt_id": "test_prompt"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("✅ Success! Set test prompt as active")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
        
        # Test 6: Verify the change
        print("\n6. Testing active prompt change verification")
        response = requests.get(f"{BASE_URL}/system-prompts/active")
        if response.status_code == 200:
            active_prompt = response.json()
            if active_prompt['id'] == 'test_prompt':
                print("✅ Success! Active prompt correctly changed to test_prompt")
            else:
                print(f"❌ Unexpected active prompt: {active_prompt['id']}")
        
        # Test 7: Switch back to default
        print("\n7. Testing switch back to default")
        response = requests.post(
            f"{BASE_URL}/system-prompts/active",
            json={"prompt_id": "default"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("✅ Success! Switched back to default prompt")
        
        # Test 8: Delete test prompt
        print("\n8. Testing DELETE /system-prompts/{prompt_id}")
        response = requests.delete(f"{BASE_URL}/system-prompts/test_prompt")
        if response.status_code == 200:
            print("✅ Success! Deleted test prompt")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
        
        # Test 9: Try to delete default prompt (should fail)
        print("\n9. Testing deletion protection for default prompt")
        response = requests.delete(f"{BASE_URL}/system-prompts/default")
        if response.status_code == 400:
            print("✅ Success! Default prompt deletion correctly blocked")
        else:
            print(f"❌ Unexpected: {response.status_code} - {response.text}")
        
        print("\n" + "=" * 50)
        print("✅ All system prompt API tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server.")
        print("   Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_system_prompts_api() 