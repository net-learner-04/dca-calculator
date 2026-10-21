import asyncio, logging, math, os
from datetime import datetime
from functools import wraps
from zoneinfo import ZoneInfo
import config
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from calculate import investment_amount, available_purchase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
OWNER_ID = int(os.environ["TELEGRAM_OWNER_ID"])
KST = ZoneInfo("Asia/Seoul")

PERIOD_LABEL = {"daily": "매일", "weekly": "매주", "monthly": "매월"}


def owner_only(func):
    # 본인 말고는 응답하지 않는 데코레이터
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user is None or user.id != OWNER_ID:
            return
        return await func(update, context)
    return wrapper


def parse_number(text: str):
    try:
        value = float(text.replace(",", ""))
    except ValueError:
        raise ValueError("숫자 형식이 올바르지 않습니다.")

    if not math.isfinite(value):
        raise ValueError("숫자 형식이 올바르지 않습니다.")

    if value.is_integer():
        return int(value)

    return value


def find_stock_index(portfolio: list, code: str) -> int:
    for i in range(len(portfolio)):
        if portfolio[i]["code"] == code:
            return i

    raise ValueError(f"포트폴리오에 {code} 종목이 없습니다.")


def format_config(data: dict) -> str:
    period = data["period"]
    period_text = PERIOD_LABEL.get(period, "미설정")
    portfolio = data["portfolio"]

    ratio_total = 0
    lines = [
        "현재 설정\n",
        f"예산: {data['budget']:,}원",
        f"투자 주기: {period_text}\n",
        "포트폴리오",
    ]

    for i in range(len(portfolio)):
        stock = portfolio[i]
        ratio_total += stock["ratio"]
        lines.append(f"• {stock['name']} ({stock['code']}) - {stock['ratio']}%")

    lines.append(f"\n비율 합계: {ratio_total}%")

    if not math.isclose(ratio_total, 100, abs_tol=0.000001):
        lines.append("비율 합계가 100이 아닌 경우 /invest 계산이 되지 않습니다.")

    return "\n".join(lines)


@owner_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "사용 가능한 명령어\n\n"
        "/invest - 이번 달 1회 투자 금액 및 매수 가능 수량 계산\n"
        "/show - 현재 설정 확인\n"
        "/budget 500000 - 월 투자 예산 변경\n"
        "/period weekly - 투자 주기 변경 (daily / weekly / monthly)\n"
        "/add 삼성전자 005930 50 - 종목 추가 (이름 코드 비율)\n"
        "/remove 005930 - 종목 삭제 (코드)\n"
        "/ratio 005930 60 - 종목 비율 변경 (코드 비율)"
    )


@owner_only
async def show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = config.load_config()

    await update.message.reply_text(format_config(data))


@owner_only
async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 1:
            raise ValueError("사용법: /budget 500000")

        value = parse_number(context.args[0])

        if value <= 0:
            raise ValueError("투자 예산은 0보다 큰 숫자여야 합니다.")

        data = config.load_config()
        data["budget"] = value
        config.save_config(data)
    except ValueError as e:
        await update.message.reply_text(f"오류: {e}")
        return

    await update.message.reply_text(f"투자 예산을 {value:,}원으로 변경했습니다.")


@owner_only
async def period(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 1:
            raise ValueError("사용법: /period weekly")

        value = context.args[0].lower()

        if value not in PERIOD_LABEL:
            raise ValueError("투자 주기는 daily, weekly, monthly 중 하나여야 합니다.")

        data = config.load_config()
        data["period"] = value
        config.save_config(data)
    except ValueError as e:
        await update.message.reply_text(f"오류: {e}")
        return

    await update.message.reply_text(f"투자 주기를 {PERIOD_LABEL[value]}로 변경했습니다.")


@owner_only
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 3:
            raise ValueError("사용법: /add 삼성전자 005930 50")

        # 마지막 두 개가 코드, 비율이고 나머지는 종목 이름
        name = " ".join(context.args[:-2])
        code = context.args[-2]
        ratio = parse_number(context.args[-1])

        if ratio < 0:
            raise ValueError("종목 비율은 0 이상의 숫자여야 합니다.")

        data = config.load_config()

        # 기본 JSON에 들어있는 빈 종목은 제거
        portfolio = []

        for i in range(len(data["portfolio"])):
            if data["portfolio"][i]["code"] != "":
                portfolio.append(data["portfolio"][i])

        for i in range(len(portfolio)):
            if portfolio[i]["code"] == code:
                raise ValueError(f"{code}는 이미 포트폴리오에 있습니다.")

        portfolio.append({"name": name, "code": code, "ratio": ratio})
        data["portfolio"] = portfolio
        config.save_config(data)
    except ValueError as e:
        await update.message.reply_text(f"에러: {e}")
        return

    await update.message.reply_text(f"{name}({code}) {ratio}% 추가했습니다.\n\n{format_config(data)}")


@owner_only
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 1:
            raise ValueError("사용법: /remove 005930")

        code = context.args[0]

        data = config.load_config()
        index = find_stock_index(data["portfolio"], code)
        removed = data["portfolio"].pop(index)
        config.save_config(data)
    except ValueError as e:
        await update.message.reply_text(f"에러: {e}")
        return

    await update.message.reply_text(f"{removed['name']}({code}) 삭제했습니다.\n\n{format_config(data)}")


@owner_only
async def ratio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 2:
            raise ValueError("사용법: /ratio 005930 60")

        code = context.args[0]
        value = parse_number(context.args[1])

        if value < 0:
            raise ValueError("종목 비율은 0 이상의 숫자여야 합니다.")

        data = config.load_config()
        index = find_stock_index(data["portfolio"], code)
        data["portfolio"][index]["ratio"] = value
        config.save_config(data)
    except ValueError as e:
        await update.message.reply_text(f"에러: {e}")
        return

    await update.message.reply_text(f"{code} 비율을 {value}%로 변경했습니다.\n\n{format_config(data)}")


@owner_only
async def invest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(KST)

    try:
        data = config.load_config()

        # requests는 블로킹이라 스레드로 넘겨서 봇이 멈추지 않게 함
        amounts = await asyncio.to_thread(investment_amount, data, now.year, now.month)
        shares = await asyncio.to_thread(available_purchase, data, now.year, now.month)
    except Exception as e:
        logger.exception("계산 실패")
        await update.message.reply_text(f"에러: {e}")
        return

    period_label = PERIOD_LABEL.get(data["period"], data["period"])

    lines = [f"{now.year}년 {now.month}월 ({period_label} 투자)\n"]

    for i in range(len(data["portfolio"])):
        stock = data["portfolio"][i]
        lines.append(
            f"• {stock['name']} ({stock['code']})\n"
            f"   1회 투자금: {amounts[i]:,.0f}원 / 매수 가능: {int(shares[i])}주"
        )

    await update.message.reply_text("\n".join(lines))


def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("show", show))
    app.add_handler(CommandHandler("budget", budget))
    app.add_handler(CommandHandler("period", period))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("ratio", ratio))
    app.add_handler(CommandHandler("invest", invest))

    app.run_polling()