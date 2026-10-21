from config import CONFIG, create_default_json
from telegram_bot import run_bot
import os


def main() -> None:
    print("스크립트가 실행되었습니다.")
    if not os.path.exists(CONFIG):
        create_default_json()

    run_bot()


if __name__ == "__main__":
    main()