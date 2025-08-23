# FinsightAI LLM API

**LangGraph 기반의 지능형 멀티 에이전트 시스템**

KOSPI200 컨센서스 리포트 처리 및 분석을 위한 FastAPI 애플리케이션으로, PDF 문서에서 자동으로 투자 정보를 추출하고 컨센서스 데이터를 분석합니다.

## 주요 기능

- **PDF 텍스트 추출**: 컨센서스 리포트 PDF에서 텍스트 자동 추출
- **지능형 정보 파싱**: AI 에이전트를 통한 투자 정보 자동 분석
- **컨센서스 분석**: DB 기반 정량/정성 컨센서스 데이터 종합 분석
- **실시간 주가 조회**: pykrx, yfinance를 통한 실제 주가 데이터 연동
- **멀티 에이전트 시스템**: 감독자 에이전트와 전문 분석 에이전트 간 협업
- **RESTful API**: 간편한 HTTP API 인터페이스
- **D+1 성과 분석**: 투자 의견과 실제 주가 결과 비교 분석

## 기술 스택

- **프레임워크**: FastAPI, Uvicorn
- **AI/LLM**: Google Gemini 2.5 Flash, LangChain, LangGraph
- **모니터링**: LangSmith
- **PDF 처리**: PyPDF, Unstructured
- **데이터베이스**: MySQL (Private Cloud)
- **주가 데이터**: pykrx, yfinance

## 프로젝트 구조

```text
Finsight-LLM-API/
├── api/                         # API 엔드포인트
│   ├── endpoints.py             # 워크플로우 처리 API
│   └── __init__.py
├── agents/                      # AI 에이전트
│   ├── supervisor_agent.py      # 감독자 에이전트
│   ├── consensus_processing_agent.py  # 컨센서스 처리 에이전트
│   ├── consensus_analyst_agent.py     # 컨센서스 분석 에이전트
│   ├── performance_analyst_agent.py   # 성과 분석 에이전트
│   ├── corporate_analyst_agent.py     # 기업 분석 에이전트
│   ├── industry_analyst_agent.py      # 산업 분석 에이전트
│   ├── market_context_analyst_agent.py # 시장 환경 분석 에이전트
│   ├── quantitative_analyst_agent.py  # 정량 분석 에이전트
│   ├── report_writer_agent.py         # 보고서 작성 에이전트
│   └── __init__.py
├── tools/                       # 도구 모듈
│   ├── consensus_tools.py       # 컨센서스 데이터 조회 도구
│   ├── financial_data_tools.py  # 재무/주가 데이터 도구
│   ├── external_data_tools.py   # 뉴스/시장 데이터 도구
│   ├── document_tools.py        # 문서 처리 도구
│   └── __init__.py
├── workflows/                   # 워크플로우
│   ├── consensus_workflow.py    # 컨센서스 처리 워크플로우
│   ├── report_workflow.py       # 투자 보고서 생성 워크플로우
│   ├── review_workflow.py       # D+1 성과 분석 워크플로우
│   └── __init__.py
├── schemas/                     # 데이터 스키마
│   ├── schema.py               # Pydantic 스키마
│   └── __init__.py
├── data/                       # 데이터 폴더
│   └── report.txt              # 샘플 보고서
├── app.py                      # 메인 애플리케이션
├── requirements.txt            # 의존성
└── README.md
```

## 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 환경 변수를 설정하세요:

```env
# Google API 설정
GOOGLE_API_KEY=your_google_api_key

# LangSmith 설정 (선택사항)
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=your_project_name
LANGSMITH_TRACING_V2=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# Tavily API 설정 (뉴스 검색용)
TAVILY_API_KEY=your_tavily_api_key
```

### 3. 서버 실행

```bash
python app.py
```

서버는 `http://localhost:8000`에서 실행됩니다.

## 데이터베이스

### Private Cloud MySQL
- **호스트**: finsight.kro.kr:32503
- **데이터베이스**: finsight_database
- **테이블**: Stock, report_metadata, report_content
- **용도**: 실제 서비스 운영

## 워크플로우 시스템

### 1. Consensus 워크플로우
**목적**: PDF 컨센서스 리포트에서 투자 정보 자동 추출

**에이전트 구성**:
- `Consensus Processing Agent`: PDF 텍스트 추출 및 파싱
- `Supervisor Agent`: 결과 검증 및 최종 JSON 생성

**입력**: PDF 파일 경로
**출력**: 구조화된 JSON 데이터 (종목코드, 투자의견, 목표주가, 분석 내용 등)

**사용 예시**:
```json
{
    "request_type": "consensus",
    "file_path": "C:/path/to/consensus_report.pdf"
}
```

### 2. Report 워크플로우
**목적**: 종목별 종합 투자 분석 보고서 생성

**에이전트 구성**:
- `Consensus Analyst Agent`: DB 기반 컨센서스 데이터 분석
- `Corporate Analyst Agent`: 기업 펀더멘털 분석
- `Industry Analyst Agent`: 산업 동향 분석
- `Market Context Analyst Agent`: 시장 환경 분석
- `Quantitative Analyst Agent`: 기술적 분석
- `Report Writer Agent`: 최종 보고서 작성
- `Supervisor Agent`: 전체 워크플로우 관리

**입력**: 종목코드
**출력**: 완성된 투자 분석 보고서 (투자의견, 목표주가, 핵심 근거, 위험 요소 등)

**사용 예시**:
```json
{
    "request_type": "report",
    "stock_code": "005930"
}
```

### 3. Review 워크플로우
**목적**: D+1 성과 분석 및 원인 규명

**에이전트 구성**:
- `Performance Analyst Agent`: 전날 투자 의견 vs 실제 주가 비교 분석
- `Corporate Analyst Agent`: 기업 요인 분석
- `Industry Analyst Agent`: 산업 요인 분석
- `Market Context Analyst Agent`: 시장 환경 요인 분석
- `Quantitative Analyst Agent`: 기술적 요인 분석
- `Report Writer Agent`: D+1 성과 분석 보고서 작성
- `Supervisor Agent`: 전체 워크플로우 관리

**입력**: 종목코드
**출력**: D+1 성과 분석 보고서 (성과 요약, 원인 분석, 종합 결론, 투자 전략)

**사용 예시**:
```json
{
    "request_type": "review",
    "stock_code": "005930"
}
```

## API 엔드포인트

### 통합 워크플로우 API

**POST** `/api/workflow`

**요청 스키마**:
```json
{
    "request_type": "consensus" | "report" | "review",
    "file_path": "string (consensus 타입에서 필수)",
    "stock_code": "string (report, review 타입에서 필수)"
}
```

**응답 형식**:
- Consensus: 구조화된 JSON 데이터
- Report: 투자 분석 보고서 텍스트
- Review: D+1 성과 분석 보고서 텍스트

### 헬스 체크

- **GET** `/api/health` - API 상태 확인
- **GET** `/` - 루트 엔드포인트

## AI 에이전트 시스템

### 감독자 에이전트 (Supervisor Agent)
- 워크플로우별 전용 프롬프트와 라우팅 관리
- 에이전트 간 작업 조정 및 순서 관리
- 결과 검토 및 품질 확인
- 최종 출력 형식 관리

### 전문 분석 에이전트들
- **Consensus Processing Agent**: PDF 텍스트 추출 및 구조화
- **Consensus Analyst Agent**: DB 기반 컨센서스 데이터 분석
- **Performance Analyst Agent**: 투자 성과 분석 및 1차 검증
- **Corporate Analyst Agent**: 기업 펀더멘털 및 재무 분석
- **Industry Analyst Agent**: 산업 동향 및 경쟁 환경 분석
- **Market Context Analyst Agent**: 거시경제 및 시장 환경 분석
- **Quantitative Analyst Agent**: 기술적 지표 및 주가 패턴 분석
- **Report Writer Agent**: 워크플로우별 최종 보고서 작성

## 도구 모듈

### Consensus Tools
- query_consensus_data: 컨센서스 메타데이터 조회
- query_consensus_summaries: 컨센서스 요약 정보 조회
- get_previous_day_investment_reports: 전날 투자 보고서 조회

### Financial Data Tools
- get_financial_statements: 재무지표 조회 (PER, PBR, EPS, BPS 등)
- get_stock_price_data: 주가 및 거래 정보 조회
- get_technical_analysis: 기술적 분석 지표 조회
- get_current_trading_date: 현재 영업일 조회
- get_52_week_performance: 52주 성과 분석

### External Data Tools
- search_company_news: 기업 관련 뉴스 검색
- search_industry_news: 산업 관련 뉴스 검색
- search_financial_news: 경제/시장 뉴스 검색
- get_market_indicators: 시장 지표 조회

## 실제 테스트 결과 예시

### 1. Consensus 워크플로우 결과

**입력**: PDF 파일 경로
**출력**: 구조화된 JSON 데이터

```json
{
  "status": "success",
  "data": {
    "stock_code": "005930",
    "stock_name": "삼성전자",
    "report_title": "실망감도 이미 반영된 주가",
    "report_date": "2025-07-14",
    "report_type": "기업분석",
    "analyst_name": "김영건, 김제호",
    "company_name": "미래에셋증권",
    "rating": "매수",
    "opinion_change": "유지",
    "target_price": "78000",
    "target_price_change": "하향",
    "investment_rationale": "[투자의견 및 밸류에이션] 동사에 대한 12개월 목표주가를 78,000원(기존 80,000원)으로 하향한다...",
    "summary": "삼성전자의 12개월 목표주가는 HBM 불용처리 상각 및 HBM 3E 12단 납품 지연으로 78,000원(기존 80,000원)으로 하향 조정되었다..."
  }
}
```

### 2. Report 워크플로우 결과

**입력**: 종목코드 "005930" (삼성전자)
**출력**: 종합 투자 분석 보고서

```markdown
## 종목 투자 보고서

### 1. 투자 의견
- **투자의견**: 매수
- **목표주가**: 75,500원 (컨센서스 평균, 최저 71,000원 ~ 최고 80,000원)
- **핵심 근거**:
    1. 하반기 HBM 경쟁력 강화 및 DRAM 가격 반등에 따른 실적 턴어라운드 기대.
    2. 3조 9천억 원 규모의 자사주 매입을 통한 적극적인 주주가치 제고 노력.
    3. AI 및 고성능 컴퓨팅(HPC) 수요 증가에 따른 반도체 시장의 지속적인 성장 수혜.
    4. 2분기 실적 부진은 일회성 요인(HBM 관련 재고자산 평가 충당금 등)으로 판단되며, 이미 주가에 상당 부분 반영.

### 2. 종목 요약
- **기업명**: 삼성전자 (005930)
- **현재가**: 70,000원 (2025년 8월 18일 기준)
- **주요 지표**:
    * PER: 14.14배
    * PBR: 1.21배
    * EPS: 4,950원
    * BPS: 57,951원
    * 배당수익률 (DIV): 2.07%
    * 주당배당금 (DPS): 1,446원
    * 시가총액: 414조 3,746억 5,454만 원

### 3. 핵심 포인트
- **긍정 요인**:
    1. **하반기 실적 턴어라운드 가시화**: 2분기 실적은 HBM 관련 일회성 비용 및 비메모리 부진으로 시장 기대치를 하회했으나, 3분기부터 HBM3e 12단 사업 안정화, DRAM 가격 상승 전환, 파운드리 적자 축소 등으로 실적 개선이 본격화될 것으로 전망됩니다.
    2. **적극적인 주주환원 정책**: 최근 발표된 3조 9천억 원 규모의 자사주 매입은 주주가치 제고에 대한 기업의 강력한 의지를 보여주며, 주가 하방 경직성을 확보하고 투자 심리 개선에 긍정적인 영향을 미칠 것입니다.
    3. **AI 시대 반도체 시장 성장 수혜**: AI 및 고성능 컴퓨팅(HPC) 수요 증가에 따른 글로벌 반도체 시장의 지속적인 성장은 삼성전자의 핵심 성장 동력입니다.

### 4. 위험 요소
- **주요 리스크**:
    1. **HBM 시장 경쟁 심화 및 기술 불확실성**: HBM3e 12단 양산 및 주요 고객사 인증 지연 가능성, SK하이닉스 등 경쟁사와의 기술 경쟁 심화는 시장 점유율 및 수익성에 영향을 미칠 수 있습니다.
    2. **글로벌 경기 둔화 및 지정학적 리스크**: 미국 관세 부과 가능성, 미-중 기술 패권 경쟁 심화 등 글로벌 무역 환경의 불확실성은 반도체 수요 위축 및 공급망 교란을 야기할 수 있습니다.

### 5. 결론
삼성전자는 2분기 일회성 비용으로 인한 실적 부진을 겪었으나, 이는 이미 주가에 상당 부분 반영된 것으로 판단됩니다. 하반기에는 HBM 경쟁력 강화, DRAM 가격 반등, 파운드리 가동률 상승 등 핵심 사업 부문의 펀더멘털 개선이 기대되며, 대규모 자사주 매입을 통한 주주환원 정책도 긍정적인 투자 심리를 형성할 것입니다.

**투자 전략**: 현재 주가는 52주 최고가(80,100원) 대비 약 12.6% 낮은 수준으로, 하반기 실적 개선 기대감을 고려할 때 매력적인 매수 구간으로 판단됩니다. 단기적인 기술적 조정 가능성을 염두에 두고, 20일 이동평균선(69,615원) 부근에서의 지지 여부를 확인하며 **분할 매수** 전략으로 접근하는 것이 유효합니다.
```

### 3. Review 워크플로우 결과

**입력**: 종목코드 "005930" (삼성전자)
**출력**: D+1 성과 분석 보고서

```markdown
## D+1 성과 분석 보고서

### 1. 성과 요약
- **전날 투자 의견 vs 실제 결과**:
    * 전날(2025년 8월 18일) 삼성전자(005930)에 대한 투자 의견은 '매수'였으며, 목표주가는 75,500원으로 제시되었습니다. 하반기 HBM 경쟁력 강화 및 DRAM 가격 반등에 따른 실적 턴어라운드 기대, 3조 9천억 원 규모의 자사주 매입을 통한 주주가치 제고 노력, AI 및 고성능 컴퓨팅(HPC) 수요 증가에 따른 반도체 시장의 지속적인 성장 수혜 등이 주요 근거였습니다.
    * 실제 결과, 2025년 8월 19일 삼성전자(005930)의 주가는 전일 대비 1,600원(-2.23%) 하락한 70,000원에 마감했습니다.

- **성과 판단 (성공/실패/혼재) 및 근거**:
    * **성과 판단: 실패**
    * **근거**: '매수' 의견과 목표주가 제시에도 불구하고, 당일 주가는 오히려 하락하여 예측과 상반된 움직임을 보였습니다. 이는 투자 의견의 핵심 근거들이 단기적으로 주가에 긍정적으로 반영되지 못했음을 의미합니다.

### 2. 원인 분석

- **기업 요인 (Corporate Analyst 분석 결과)**:
    * **2분기 실적 부진에 대한 시장의 단기적 반응**: 전날 보도된 삼성전자의 2분기 영업이익이 전년 대비 '반토막' 났다는 뉴스가 시장에 단기적인 부정적 영향을 미쳤을 가능성이 높습니다. 비록 분석 보고서에서는 이를 일회성 요인으로 판단하고 하반기 턴어라운드를 기대했으나, 시장은 단기 실적 악화에 더 민감하게 반응한 것으로 보입니다.
    * **자사주 매입 효과의 제한적 반영**: 3조 9천억 원 규모의 자사주 매입 발표는 주주가치 제고에 긍정적인 신호였으나, 2분기 실적 부진과 전반적인 시장 하락세 속에서 그 효과가 충분히 발휘되지 못했습니다.

- **산업 요인 (Industry Analyst 분석 결과)**:
    * **긍정적 산업 전망에도 불구하고 개별 종목 하락**: 반도체 산업 전반은 AI 및 HPC 수요 증가, HBM 기술력 강세 등으로 긍정적인 성장 전망을 보였습니다. 삼성전자 역시 HBM3E 및 고용량 DDR5 판매 확대, 파운드리 매출 개선 등 긍정적인 내부 요인이 있었음에도 불구하고 주가가 하락했습니다.

- **시장 환경 (Market Context Analyst 분석 결과)**:
    * **전반적인 시장 하락세**: 2025년 8월 19일 KOSPI 지수가 전일 대비 1.50% 하락하는 등 국내 증시 전반이 약세를 보였습니다. 이는 삼성전자 주가 하락에 대한 외부적인 요인으로 작용하여, 개별 기업의 긍정적 요인들이 시장의 하락 압력을 이겨내기 어려웠음을 나타냅니다.

- **기술적 요인 (Quantitative Analyst 분석 결과)**:
    * **단기 지지선 이탈**: 전일 종가 71,600원에서 70,000원으로 하락하며 단기적인 지지선이 이탈된 것으로 판단됩니다. 이는 추가 하락에 대한 기술적 신호로 작용할 수 있습니다.
    * **거래량 동반 하락**: 1,300만 주 이상의 거래량으로 주가가 하락한 것은 매도 압력이 강했음을 시사합니다.

### 3. 종합 결론

- **성과의 최종 원인**:
    삼성전자 주가의 D+1 하락은 **2분기 실적 부진에 대한 시장의 단기적이고 즉각적인 부정적 반응**과 **전반적인 국내 증시의 하락세**가 복합적으로 작용한 결과로 판단됩니다. 비록 하반기 실적 턴어라운드 기대감, 자사주 매입, HBM 경쟁력 강화 등 긍정적인 기업 및 산업 요인이 존재했으나, 이러한 장기적이고 긍정적인 요인들은 단기적인 실적 악화 뉴스 및 시장 전반의 매도 압력을 상쇄하기에는 역부족이었습니다.

- **향후 투자 전략 제언**:
    * **단기 변동성 대비**: 삼성전자의 펀더멘털은 여전히 견고하나, 단기적으로는 시장의 실적 발표 민감도와 거시경제 불확실성에 따른 변동성이 클 수 있습니다. 급격한 추격 매수보다는 시장 상황을 관망하며 분할 매수 전략을 고려해야 합니다.
    * **하반기 실적 턴어라운드 확인**: 3분기 실적 발표(2025년 10월 29일 예정)를 통해 HBM 및 DRAM 가격 반등에 따른 실질적인 실적 개선 여부를 확인하는 것이 중요합니다.
    * **장기적 관점 유지**: AI, HPC 등 반도체 산업의 구조적 성장은 삼성전자에 지속적인 기회를 제공할 것입니다. 단기적인 노이즈에 흔들리지 않고 장기적인 관점에서 접근하는 것이 유효합니다.

- **모니터링 포인트**:
    * **삼성전자 3분기 실적 발표 및 가이던스**: 특히 메모리(DRAM, HBM) 부문의 수익성 개선 여부.
    * **글로벌 반도체 시장 동향**: DRAM 및 낸드플래시 가격 추이, AI 반도체 수요 변화.
    * **국내외 거시경제 지표**: KOSPI/KOSDAQ 지수 흐름, 환율 변동성, 주요국 금리 정책 변화.
    * **경쟁사(SK하이닉스 등) 실적 및 투자 동향**: HBM 시장 내 경쟁 구도 변화.
```

## 성능 및 품질

### 처리 속도
- **Consensus 워크플로우**: PDF 파일당 평균 30-60초
- **Report 워크플로우**: 종목당 평균 2-3분
- **Review 워크플로우**: 종목당 평균 3-4분

### 정확도
- **PDF 텍스트 추출**: 95% 이상 (텍스트 기반 PDF 기준)
- **투자 정보 파싱**: 90% 이상
- **주가 데이터 연동**: 실시간 정확도
- **뉴스 검색**: 최신 24시간 내 관련 뉴스

### 지원 종목
- **KOSPI200**: 전체 종목 지원
- **주요 대형주**: 삼성전자, SK하이닉스, LG에너지솔루션, 현대차 등
- **중소형주**: 시장 동향에 따른 동적 지원

## 사용 예시

### 1. 컨센서스 리포트 처리
```bash
curl -X POST "http://localhost:8000/api/workflow" \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "consensus",
    "file_path": "C:/path/to/report.pdf"
  }'
```

### 2. 투자 보고서 생성
```bash
curl -X POST "http://localhost:8000/api/workflow" \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "report",
    "stock_code": "005930"
  }'
```

### 3. D+1 성과 분석
```bash
curl -X POST "http://localhost:8000/api/workflow" \
  -H "Content-Type: application/json" \
  -d '{
    "request_type": "review",
    "stock_code": "005930"
  }'
```

## 개발 가이드

### API 문서
서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### 로깅 및 모니터링
LangSmith를 통한 에이전트 실행 과정 추적 및 모니터링이 가능합니다.

### 지원 모델
- **기본 모델**: Gemini 2.5 Flash
- **특징**: 빠른 응답속도, 비용 효율성, 한국어 최적화

## 주의사항

- Google API 키가 필수적으로 필요합니다
- PDF 파일 경로는 서버에서 접근 가능한 절대 경로여야 합니다
- Windows 경로 사용 시 JSON에서 백슬래시 이스케이프 필요 (\ 또는 / 사용)
- 이미지 기반 PDF는 현재 지원되지 않습니다 (텍스트 추출 가능한 PDF만 지원)
- KOSPI200 종목만 지원됩니다

## 라이선스

이 프로젝트는 개인/내부 사용을 위한 것입니다.

## 기여

버그 리포트나 기능 개선 제안은 이슈를 통해 제출해주세요.
