from dotenv import load_dotenv
from pathlib import Path
import json, requests, os

load_dotenv(Path(__file__).parent / ".env")

# 생성되는 .json 파일명
CONFIG = Path(__file__).parent / "config.json"

# 토스 증권 API Keys
TOSS_CLIENT_ID = os.environ.get("TOSS_CLIENT_ID", None)
TOSS_CLIENT_SECRET = os.environ.get("TOSS_CLIENT_SECRET", None)

# 토스 증권 Open API 기본 도메인
BASE_URL = "https://openapi.tossinvest.com"


def create_default_json() -> None:
    # 기본적으로 생성되는 .json 파일 형식
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


def save_config(data: dict) -> None:
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_access_token() -> str:
    if not TOSS_CLIENT_ID or not TOSS_CLIENT_SECRET:
        raise ValueError("TOSS_CLIENT_ID 또는 TOSS_CLIENT_SECRET이 설정되지 않았습니다.")

    url = f"{BASE_URL}/oauth2/token"
    payload = {"grant_type": "client_credentials"}
    auth = (TOSS_CLIENT_ID, TOSS_CLIENT_SECRET)

    response = requests.post(url, data=payload, auth=auth, timeout=10)

    if response.status_code == 200:
        token = response.json().get("access_token")

        if not token:
            raise RuntimeError("access_token이 없습니다.")

        return token
    else:
        raise Exception(f"토큰 발급 실패: {response.text}")