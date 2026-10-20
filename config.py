from dotenv import load_dotenv
from pathlib import Path
import json, requests

load_dotenv(Path(__file__).parent / ".env")

# 생성되는 .json 파일명
CONFIG = "config.json"

# 토스 증권 API Keys
TOSS_CLIENT_ID = ""
TOSS_CLIENT_SECRET = ""

# 토스 증권 Open API 기본 도메인
BASE_URL = "https://openapi.tossinvest.com"

def create_default_json() -> None:
    data = {
        "budget": 0,
        # daily / weekly / monthly 중 하나
        "period": "",
        "portfolio": [
            {"name": "", "code": "", "ratio": 0},
            {"name": "", "code": "", "ratio": 0},
        ]
    }
   
    with open(CONFIG, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        

def load_config() -> dict:
    with open(CONFIG, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data

def get_access_token():
    url = f"{BASE_URL}/oauth2/token"
    payload = {"grant_type": "client_credentials"}
    auth = (TOSS_CLIENT_ID, TOSS_CLIENT_SECRET)

    response = requests.post(url, data=payload, auth=auth)

    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"토큰 발급 실패: {response.text}")