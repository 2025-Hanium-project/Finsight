import requests
from bs4 import BeautifulSoup

def get_usdkrw_realtime():
    url = "https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    today_rate = float("".join(soup.select_one(".no_today").stripped_strings).replace("원", "").replace(",", ""))
    change_value = float("".join(soup.select_one(".no_exday em").stripped_strings).replace(",", ""))
    change_rate_value = float(
        "".join(soup.select(".no_exday em")[1].stripped_strings)
        .replace("(", "").replace(")", "").replace("%", "").replace("+", "").replace(",", "")
    )
    return {
        "today": today_rate,
        "change": change_value,
        "change_rate": change_rate_value
    }

def get_kor_treasury_3y():
    url = "https://finance.naver.com/marketindex/interestDetail.naver?marketindexCd=IRR_GOVT03Y"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    today_rate = float("".join(soup.select_one(".no_today").stripped_strings).replace("%", "").replace(",", ""))
    change_value = float("".join(soup.select_one(".no_exday em").stripped_strings).replace(",", ""))
    change_rate_value = float(
        "".join(soup.select(".no_exday em")[1].stripped_strings)
        .replace("(", "").replace(")", "").replace("%", "").replace("+", "").replace(",", "")
    )
    return {
        "today": today_rate,
        "change": change_value,
        "change_rate": change_rate_value
    }
