# Finsight Data

한국 금융 시장 데이터를 종합적으로 수집하는 Python 프로젝트입니다.

## 📊 수집 데이터

### 1. 시장 지수 (Market Index)
- **수집 데이터**: KOSPI, KOSDAQ, KONEX 등 주요 지수
- **데이터 내용**: 일별 OHLCV(시가, 고가, 저가, 종가, 거래량) 데이터 및 변화율
- **수집 방법**: pykrx 라이브러리를 통한 KRX API 호출
- **수집 주기**: 일 1회 (장 마감 후)
- **저장 형식**: `market_index_{index_name}_{date}.csv`

### 2. 환율 정보 (Exchange Rate)
- **수집 데이터**: 주요 통화별 환율 정보
- **데이터 내용**: USD/KRW, EUR/KRW, JPY/KRW, CNY/KRW, GBP/KRW 등
- **수집 방법**: 한국은행 경제통계시스템(ECOS) API
- **수집 주기**: 일 1회 (장 마감 후)
- **저장 형식**: `exchange_rate_{currency}_{date}.csv`

### 3. 금리 정보 (Interest Rate)
- **수집 데이터**: 한국은행 기준금리, 국채 금리, 회사채 금리
- **데이터 내용**: 
  - 기준금리 (한국은행)
  - 국채 금리 (3년, 5년, 10년)
  - 회사채 금리 (AA, BBB 등급)
- **수집 방법**: 한국은행 ECOS API
- **수집 주기**: 일 1회
- **저장 형식**: `interest_rate_{type}_{date}.csv`

### 4. 주식 데이터 (Stock Data)
- **수집 데이터**: KOSPI 상장 종목 정보
- **데이터 내용**: 
  - 종목명, 종목코드, 시가총액
  - 일별 OHLCV 데이터
  - 거래량, 거래대금
- **수집 방법**: pykrx 라이브러리
- **수집 주기**: 일 1회
- **저장 형식**: `stock_data_kospi_{date}.csv`

### 5. 섹터 동향 (Sector Trends)
- **수집 데이터**: KRX 업종별 지수
- **데이터 내용**: 
  - 17개 업종 지수: 자동차, 반도체, 헬스케어, 은행, 에너지화학, 철강, 방송통신, 건설, 증권, 기계장비, 보험, 운송, 경기소비재, 필수소비재, 미디어&엔터테인먼트, 정보기술, 유틸리티
  - 일별 지수값, 변화율, 거래량
- **수집 방법**: pykrx 라이브러리 (업종별 지수 조회)
- **수집 주기**: 일 1회
- **저장 형식**: `sector_trend_{sector_name}_{date}.csv`

### 6. 경제 지표 (Economic Indicators)
- **수집 데이터**: GDP, 인플레이션, 실업률 등 주요 경제 지표
- **데이터 내용**:
  - GDP 성장률 (분기별)
  - 소비자물가지수 (CPI)
  - 생산자물가지수 (PPI)
  - 실업률
  - 수출입 지수
- **수집 방법**: 한국은행 ECOS API
- **수집 주기**: 월 1회 (발표 시점)
- **저장 형식**: `economic_indicator_{indicator_name}_{date}.csv`

### 7. 경제 캘린더 (Economic Calendar)
- **수집 데이터**: 주요 경제 이벤트 및 발표 일정
- **데이터 내용**:
  - 한국은행 금통위 일정
  - 통계청 주요 지표 발표
  - 정부 정책 발표
  - 국제 경제 이벤트
- **수집 방법**: 한국은행 및 통계청 공식 일정
- **수집 주기**: 주 1회
- **저장 형식**: `economic_calendar_{period}_{date}.csv`

### 8. 원자재 가격 (Commodity Prices)
- **수집 데이터**: 금, 은, 구리, 원유 등 주요 원자재
- **데이터 내용**:
  - 국제 원자재 가격 (USD 기준)
  - 일별 가격 변동
  - 거래량 정보
- **수집 방법**: 국제 원자재 거래소 API
- **수집 주기**: 일 1회
- **저장 형식**: `commodity_price_{commodity_name}_{date}.csv`

### 9. 재무 정보 (Financial Data)
- **수집 데이터**: DART API를 통한 기업 재무제표
- **데이터 내용**:
  - 매출액, 영업이익, 당기순이익
  - 자산총계, 부채총계, 자본총계
  - 영업활동현금흐름, 투자활동현금흐름
  - 재무비율 (ROE, ROA, 부채비율 등)
- **수집 방법**: DART Open API (공시정보)
- **수집 주기**: 분기 1회 (재무제표 발표 후)
- **저장 형식**: `financial_data_{company_code}_{period}.csv`

### 10. 투자자 동향 (Investor Trends)
- **수집 데이터**: 기관, 외국인, 개인 투자자별 매매동향
- **데이터 내용**:
  - KOSPI 시장 전체 투자자 분석
  - 기관투자자 매매동향
  - 외국인 투자자 매매동향
  - 개인투자자 매매동향
  - 순매수/순매도 금액
- **수집 방법**: pykrx 라이브러리 (투자자별 매매동향)
- **수집 주기**: 일 1회
- **저장 형식**: `investor_trend_kospi_{date}.csv`

### 11. 뉴스 수집 (News Collection)
- **수집 데이터**: 금융 관련 뉴스 및 공시 정보
- **데이터 내용**:
  - 실시간 뉴스 피드
  - 기업 공시 정보
  - 경제 정책 뉴스
  - 시장 동향 뉴스
- **수집 방법**: 뉴스 API 및 RSS 피드
- **수집 주기**: 실시간 (1시간 간격)
- **저장 형식**: `news_financial_{date}.csv`

## 🚀 설치 및 실행

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/your-username/Finsight-Data.git
cd Finsight-Data

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 정보를 입력하세요:

```env
# DART API 키 (재무 정보 수집용)
DART_API_KEY=your_dart_api_key_here

# 로그 레벨
LOG_LEVEL=INFO

# 데이터 저장 경로
DATA_DIR=./data
LOGS_DIR=./logs
```

### 3. 실행

#### 전체 데이터 수집
```bash
python main.py
```

#### 특정 데이터만 수집
```bash
# 시장 지수만 수집
python main.py market_index

# 환율 정보만 수집
python main.py exchange_rate

# 금리 정보만 수집
python main.py interest_rate

# 주식 데이터만 수집
python main.py stock

# 섹터 동향만 수집
python main.py sector_trend

# 경제 지표만 수집
python main.py economic_indicator

# 경제 캘린더만 수집
python main.py economic_calendar

# 원자재 가격만 수집
python main.py commodity

# 재무 정보만 수집
python main.py financial

# 투자자 동향만 수집
python main.py investor_trend

# 뉴스만 수집
python main.py news
```

## 📁 프로젝트 구조

```
Finsight-Data/
├── config/
│   ├── __init__.py
│   └── settings.py          # 설정 파일
├── data_collectors/
│   ├── __init__.py
│   ├── market_index_collector.py
│   ├── exchange_rate_collector.py
│   ├── interest_rate_collector.py
│   ├── stock_collector.py
│   ├── sector_trend_collector.py
│   ├── economic_indicator_collector.py
│   ├── economic_calendar_collector.py
│   ├── commodity_collector.py
│   ├── financial_collector.py
│   ├── investor_trend_collector.py
│   └── news_collector.py
├── utils/
│   ├── __init__.py
│   └── helpers.py           # 공통 유틸리티 함수
├── data/                    # 수집된 데이터 저장
├── logs/                    # 로그 파일
├── main.py                  # 메인 실행 파일
├── requirements.txt         # Python 의존성
├── .env                     # 환경 변수 (예시)
├── .gitignore
└── README.md
```

## 🔧 주요 기능

### 데이터 수집 방법

#### 1. pykrx 라이브러리 활용
- **용도**: 시장 지수, 주식 데이터, 섹터 동향, 투자자 동향 수집
- **API 소스**: KRX (한국거래소) 공식 데이터
- **주요 함수**:
  - `stock.get_market_ohlcv_by_date()`: 일별 OHLCV 데이터
  - `stock.get_market_cap_by_date()`: 시가총액 데이터
  - `stock.get_market_trading_value_by_date()`: 거래대금 데이터
  - `stock.get_market_trading_volume_by_date()`: 거래량 데이터
  - `stock.get_market_fundamental_by_date()`: 투자자별 매매동향

#### 2. 한국은행 ECOS API
- **용도**: 환율, 금리, 경제 지표 수집
- **API 엔드포인트**: https://ecos.bok.or.kr/api/
- **인증 방식**: API 키 기반 인증
- **주요 데이터**:
  - 환율: 036Y001 (원/달러 환율)
  - 금리: 721Y001 (기준금리), 817Y002 (국채금리)
  - 경제지표: 901Y009 (GDP), 901Y013 (CPI)

#### 3. DART Open API
- **용도**: 기업 재무제표 및 공시 정보 수집
- **API 엔드포인트**: https://opendart.fss.or.kr/api/
- **인증 방식**: API 키 기반 인증
- **주요 기능**:
  - 기업 고유번호 조회
  - 재무제표 정보 조회
  - 공시 정보 조회
- **데이터 형식**: ZIP 파일 압축 해제 후 JSON 파싱

#### 4. 뉴스 API 및 RSS 피드
- **용도**: 금융 뉴스 및 공시 정보 수집
- **수집 방식**: HTTP 요청 및 RSS 피드 파싱
- **주요 소스**: 금융 관련 뉴스 사이트 및 공시 시스템

### 데이터 수집기 (Collectors)
각 데이터 수집기는 독립적으로 실행 가능하며, 다음과 같은 공통 인터페이스를 제공합니다:

- `collect_all()`: 해당 데이터 유형의 모든 정보 수집
- 자동 CSV 파일 저장
- 로깅 및 오류 처리
- 재시도 로직

### 설정 관리
- `config/settings.py`에서 모든 설정 중앙 관리
- 환경 변수를 통한 민감 정보 관리
- 로깅 레벨 및 파일 경로 설정

### 유틸리티 함수
- `utils/helpers.py`에서 공통 함수 제공
- API 요청 재시도 로직
- 데이터 저장/로드 함수
- 날짜 처리 및 포맷팅

## 📈 데이터 형식

### CSV 파일 명명 규칙
- `{data_type}_{market}_{date}.csv`
- 예: `market_index_kospi_20250624.csv`
- 예: `financial_data_top20_20250624.csv`

### 공통 컬럼
- `date`: 데이터 날짜 (YYYY-MM-DD)
- `collected_at`: 수집 시간 (YYYY-MM-DD HH:MM:SS)

### 데이터 유형별 상세 컬럼

#### 1. 시장 지수 (Market Index)
```csv
date,index_name,open,high,low,close,volume,change_rate,collected_at
2025-06-24,KOSPI,2800.50,2815.20,2795.30,2810.45,1234567,0.35,2025-06-24 15:30:00
```

#### 2. 환율 정보 (Exchange Rate)
```csv
date,currency_pair,exchange_rate,change_rate,collected_at
2025-06-24,USD/KRW,1350.25,0.12,2025-06-24 15:30:00
```

#### 3. 금리 정보 (Interest Rate)
```csv
date,rate_type,rate_value,change_basis_points,collected_at
2025-06-24,기준금리,3.50,0,2025-06-24 15:30:00
```

#### 4. 주식 데이터 (Stock Data)
```csv
date,stock_code,stock_name,open,high,low,close,volume,market_cap,collected_at
2025-06-24,005930,삼성전자,75000,75500,74800,75200,1234567,4500000000000,2025-06-24 15:30:00
```

#### 5. 섹터 동향 (Sector Trends)
```csv
date,sector_name,sector_code,index_value,change_rate,volume,collected_at
2025-06-24,반도체,5044,1250.50,1.25,987654,2025-06-24 15:30:00
```

#### 6. 경제 지표 (Economic Indicators)
```csv
date,indicator_name,indicator_code,value,unit,period,collected_at
2025-06-24,GDP성장률,901Y009,2.5,%,2024Q1,2025-06-24 15:30:00
```

#### 7. 경제 캘린더 (Economic Calendar)
```csv
date,event_name,event_type,announcement_time,importance,description,collected_at
2025-06-24,한국은행 금통위,정책,14:00,High,기준금리 결정,2025-06-24 15:30:00
```

#### 8. 원자재 가격 (Commodity Prices)
```csv
date,commodity_name,price_usd,change_rate,volume,collected_at
2025-06-24,Gold,2350.50,0.25,12345,2025-06-24 15:30:00
```

#### 9. 재무 정보 (Financial Data)
```csv
date,company_code,company_name,revenue,operating_income,net_income,total_assets,period,collected_at
2025-06-24,005930,삼성전자,2500000000000,350000000000,280000000000,4500000000000,2024Q1,2025-06-24 15:30:00
```

#### 10. 투자자 동향 (Investor Trends)
```csv
date,investor_type,net_buy_amount,net_buy_volume,market_share,collected_at
2025-06-24,외국인,150000000000,1234567,32.5,2025-06-24 15:30:00
```

#### 11. 뉴스 수집 (News Collection)
```csv
date,news_title,news_source,news_url,news_category,published_time,collected_at
2025-06-24,삼성전자 실적 발표,연합뉴스,https://...,기업실적,2025-06-24 14:30:00,2025-06-24 15:30:00
```

## 🔍 사용 예시

### Python에서 직접 사용
```python
from data_collectors.market_index_collector import MarketIndexCollector

# 시장 지수 수집
collector = MarketIndexCollector()
data = collector.collect_all()
print(f"수집된 데이터: {len(data)}개")
```

### 데이터 분석
```python
import pandas as pd

# CSV 파일 로드
df = pd.read_csv('data/market_index_kospi_20250624.csv')
print(df.head())

# 최근 30일 데이터 분석
recent_data = df.tail(30)
print(f"평균 종가: {recent_data['close'].mean():.2f}")
```

## ⚠️ 주의사항

### API 제한
- DART API: 일일 호출 제한 확인 필요
- pykrx: 과도한 요청 시 일시적 차단 가능
- 한국은행 ECOS: 공식 API 사용 권장

### 데이터 품질
- 주말 및 공휴일 데이터 부재
- 일부 데이터는 지연 제공
- API 서버 점검 시 데이터 수집 불가

### 에러 처리
- 네트워크 오류 시 자동 재시도
- 데이터 없음 시 로그 기록
- 치명적 오류 시 프로그램 중단

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

프로젝트에 대한 문의사항이나 버그 리포트는 GitHub Issues를 이용해 주세요.

## 🔄 업데이트 로그

### v1.0.0 (2025-06-24)
- 초기 버전 릴리즈
- 11개 데이터 수집기 구현
- 기본적인 데이터 수집 및 저장 기능
- 로깅 및 오류 처리 시스템

---

**Finsight Data** - 한국 금융 시장 데이터의 종합적 수집 및 분석 