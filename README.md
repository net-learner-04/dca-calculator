# dca-calculator

## 파일별 기능

- **requirement.txt** : 프로그램을 실행 하기 위해 필요한 파이썬 모듈 명 정리 (명령어 이용하여 설치도 가능)
- **main.py** : config.json이 없으면 기본값으로 생성하고 텔레그램 봇을 실행함
- **config.py** : config.json 생성/불러오기/저장, .env 값 로드, 토스 증권 Open API 액세스 토큰 발급
- **calculate.py** : 월 예산과 종목 비율로 1회 투자 금액을 계산하고, 토스 증권 API의 현재 매도 호가 기준으로 종목별 매수 가능 수량을 계산함
- **telegram_bot.py** : 텔레그램 명령어로 예산, 투자 주기, 종목, 비율을 설정하고 이번 달 투자 금액을 계산해줌 (본인 텔레그램 ID만 응답)

## 모듈 설치

```bash
python3 -m pip install -r modules.txt
```

## 환경 변수

프로젝트 폴더에 `.env` 파일을 만들어서 아래 값을 채워야 함

```
TOSS_CLIENT_ID=토스_클라이언트_ID
TOSS_CLIENT_SECRET=토스_클라이언트_시크릿
TELEGRAM_BOT_TOKEN=BotFather에서_받은_토큰
TELEGRAM_OWNER_ID=내_텔레그램_숫자_ID
```

## 실행

```bash
python3 main.py               # 처음 실행하면 config.json 이 자동 생성되고 봇이 켜짐 (터미널을 켜 두거나 tmux, nohup 등으로 상시 실행)
```

```bash
/start                        # 텔레그램에서 봇에게 보내면 명령어 목록이 나옴
/budget 500000                # 월 투자 예산 변경
/period weekly                # 투자 주기 변경 (daily / weekly / monthly)
/add 삼성전자 005930 60        # 종목 추가 (이름 코드 비율)
/remove 005930                # 종목 삭제 (코드)
/ratio 005930 70              # 종목 비율 변경 (코드 비율)
/show                         # 현재 설정 확인
/invest                       # 이번 달 1회 투자 금액 및 매수 가능 수량 계산 (종목 비율 합계가 100이어야 가능)
```