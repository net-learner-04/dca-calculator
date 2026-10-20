
import config
import calendar, requests, math


def get_weekly_count(year: int, month: int) -> int:
    weeks = calendar.monthcalendar(year, month)
    target_weekday = calendar.FRIDAY

    # 해당 달에 금요일이 몇 번 있는지 반환
    return sum(
        1 for week in weeks
        if week[target_weekday] != 0
    )


def get_daily_count(year: int, month: int) -> int:
    _, total = calendar.monthrange(year, month)

    # 해당 달에 몇 일이 있는지 반환
    return sum(
        1 for day in range(1, total + 1)
        if calendar.weekday(year, month, day) < 5
    )


def monthly_allocation_amount(data: dict) -> list:
    budget = data["budget"]
    portfolio = data["portfolio"]

    if not isinstance(budget, (int, float)) or isinstance(budget, bool) or budget <= 0:
        raise ValueError("투자 예산은 0보다 큰 숫자여야 합니다.")

    if not isinstance(portfolio, list) or len(portfolio) == 0:
        raise ValueError("포트폴리오에 종목을 하나 이상 등록해야 합니다.")

    ratio_total = 0
    results = []

    for i in range(len(portfolio)):
        ratio = portfolio[i]["ratio"]

        if not isinstance(ratio, (int, float)) or isinstance(ratio, bool) or ratio < 0:
            raise ValueError("종목 비율은 0 이상의 숫자여야 합니다.")

        ratio_total += ratio

        # 월간 배정 금액 계산 공식
        result = budget * (ratio / 100)
        results.append(result)

    if not math.isclose(ratio_total, 100, abs_tol=0.000001):
        raise ValueError("종목별 비율의 합계는 100이어야 합니다.")

    return results


def investment_amount(data: dict, year: int, month: int) -> list:
    if not isinstance(year, int) or isinstance(year, bool) or year < 1:
        raise ValueError("연도는 1 이상의 정수여야 합니다.")

    if not isinstance(month, int) or isinstance(month, bool) or not 1 <= month <= 12:
        raise ValueError("월은 1부터 12 사이의 정수여야 합니다.")

    count = data["period"]
    amount = monthly_allocation_amount(data)

    number_of_investments = 0

    if count == "daily":
        number_of_investments = get_daily_count(year, month)
    elif count == "weekly":
        number_of_investments = get_weekly_count(year, month)
    elif count == "monthly":
        number_of_investments = 1
    else:
        raise ValueError("투자 주기는 daily, weekly, monthly 중 하나여야 합니다.")

    if number_of_investments <= 0:
        raise ValueError("투자 횟수가 0 이하입니다.")

    results = []

    for i in range(len(amount)):
        result = amount[i] / number_of_investments
        results.append(result)

    return results


def get_current_price(token, code):
    if not token:
        raise ValueError("API 액세스 토큰이 없습니다.")

    if not isinstance(code, str) or not code.strip():
        raise ValueError("종목 코드가 올바르지 않습니다.")

    url = f"{config.BASE_URL}/v1/stocks/{code}/price"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

    except requests.RequestException as e:
        raise RuntimeError(f"시세 조회 요청 실패: {e}") from e
    except ValueError as e:
        raise RuntimeError("시세 API 응답이 올바른 JSON 형식이 아닙니다.") from e

    return data


def available_purchase(data: dict, year: int, month: int) -> list:
    portfolio = data["portfolio"]
    token = config.get_access_token()
    investment = investment_amount(data, year, month)

    results = []

    for i in range(len(portfolio)):
        code = portfolio[i]["code"]
        price_data = get_current_price(token, code)

        # 가장 낮은 매도 호가를 현재 매수 예상 가격으로 사용
        price = int(price_data["result"]["asks"][0]["price"])

        if not isinstance(price, (int, float)) or isinstance(price, bool) or price <= 0:
            raise ValueError(f"{code}의 주가 데이터가 올바르지 않습니다.")

        result = investment[i] // price
        results.append(result)

    return results
