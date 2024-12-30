import requests
import json
from datetime import time


# Base URL (replace with your actual API URL)
base_url = "http://127.0.0.1:8000"  # Example: localhost

# 0. sign user
# sign_url = f"{base_url}/auth/sign_user"
# user_data = {"user": "dambt2"}
# headers = {"Content-Type": "application/json"}
# response = requests.post(sign_url, json=user_data,headers=headers)
# if response.status_code == 200:
#     print("'/chat' response:", response.json())
# token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiZGFtYnQyIiwiZXhwaXJlcyI6MTcyNTUyNTc1MC41NzExMzg5fQ.d-Pmj7V4L1ig3XqS3KQHRPpx1RuhAbuVUOcZejxRFi4"
# 1. Test /chat endpoint
complete_url = f"{base_url}/v1/complete"
message_data = {"message": "Giá gói dịch vụ epoints"}
headers = {"Content-Type": "application/json"}
response = requests.post(complete_url, json=message_data,headers=headers)
print("response", response)
if response.status_code == 200:
    full_response = ""
    for chunk in response.iter_content(
        chunk_size=None, decode_unicode=True
    ):
        streaming_resp = chunk
        full_response += streaming_resp
    print("'/chat' response:", full_response)
else:
    print(f"Error calling '/chat': {response.status_code} - {response.text}")
