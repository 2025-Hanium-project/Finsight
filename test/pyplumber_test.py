import requests
import pandas as pd

API_KEY = "YOUR_ECOS_API_KEY"

def fetch_ecos(stat_code, item_code=None, start="20250101", end="20250731"):
    url = f"https://ecos.bok.or.kr/api/{API_KEY}/json/StatisticSearch/1/100/{stat_code}/D/{start}/{end}"
    if item_code:
        url += f"/{item_code}"
    res = requests.get(url)
    data = res.json().get('StatisticSearch', {}).get('row', [])
    df = pd.DataFrame(data)
    return df[['TIME', 'DATA_VALUE']]

# 환율
df_fx = fetch_ecos("036Y001")
df_fx.columns = ['date', 'usd_krw']
df_fx['date'] = pd.to_datetime(df_fx['date'], format="%Y%m%d")
df_fx['usd_krw'] = df_fx['usd_krw'].astype(float)

# 국채 3년
df_bond3 = fetch_ecos("817Y002", item_code="010200000")
df_bond3.columns, df_bond3.columns = ['date', 'bond3y'], df_bond3.columns
df_bond3['date'] = pd.to_datetime(df_bond3['date'], format="%Y%m%d")
df_bond3['bond3y'] = df_bond3['bond3y'].astype(float)

print(df_fx.tail(), df_bond3.tail())
