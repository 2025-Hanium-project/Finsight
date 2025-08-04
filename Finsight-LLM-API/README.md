# FinsightAI LLM API

**LangGraph 기반의 지능형 멀티 에이전트 시스템**

컨센서스 리포트 처리를 위한 FastAPI 애플리케이션으로, PDF 문서에서 자동으로 투자 정보를 추출하고 구조화된 데이터로 변환합니다.

## 📋 주요 기능

- **PDF 텍스트 추출**: 컨센서스 리포트 PDF에서 텍스트 자동 추출
- **지능형 정보 파싱**: AI 에이전트를 통한 투자 정보 자동 분석
- **구조화된 데이터 변환**: JSON 형식의 표준화된 컨센서스 데이터 출력
- **멀티 에이전트 시스템**: 감독자 에이전트와 처리 에이전트 간 협업
- **RESTful API**: 간편한 HTTP API 인터페이스

## 🛠 기술 스택

- **프레임워크**: FastAPI
- **AI/LLM**: Google Gemini API, LangChain, LangGraph
- **모니터링**: LangSmith
- **PDF 처리**: PyPDF
- **서버**: Uvicorn

## 📁 프로젝트 구조

```
Finsight-LLM-API/
├── api/                    # API 엔드포인트
│   ├── endpoints.py        # 컨센서스 처리 API
│   └── __init__.py
├── agents/                 # AI 에이전트
│   ├── supervisor_agent.py          # 감독자 에이전트
│   ├── consensus_processing_agent.py # 컨센서스 처리 에이전트
│   ├── prompts.py          # 에이전트 프롬프트
│   └── __init__.py
├── tools/                  # 도구 모듈
│   ├── document_tools.py   # PDF 처리 도구
│   └── __init__.py
├── workflows/              # 워크플로우
│   ├── consensus_workflow.py # 컨센서스 처리 워크플로우
│   └── __init__.py
├── schemas/                # 데이터 스키마
│   ├── schema.py          # Pydantic 스키마
│   └── __init__.py
├── data/                   # 데이터 폴더
├── app.py                  # 메인 애플리케이션
└── requirements.txt        # 의존성
```

## ⚙️ 설치 및 설정

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
```

### 3. 서버 실행

```bash
python app.py
```

서버는 `http://localhost:8000`에서 실행됩니다.

## 🚀 사용법

### API 엔드포인트

#### 1. 루트 엔드포인트
```
GET /
```
API 정보 및 사용 가능한 엔드포인트 목록을 반환합니다.

#### 2. 헬스 체크
```
GET /health
```
서비스 상태 및 환경 설정을 확인합니다.

#### 3. 컨센서스 처리
```
POST /consensus
```

**요청 형식:**
```json
{
    "file_path": "/path/to/consensus_report.pdf"
}
```

**응답 형식:**
```json
{
    "status": "success",
    "data": {
        "stock_code": "005930",
        "stock_name": "삼성전자",
        "report_title": "리포트 제목",
        "report_date": "2024-01-15",
        "report_type": "기업분석",
        "analyst_name": "애널리스트명",
        "company_name": "증권사명",
        "rating": "매수",
        "opinion_change": "유지",
        "target_price": 84000,
        "target_price_change": "상향",
        "investment_rationale": "전체 리포트 본문 내용...",
        "summary": "3-5문장 요약"
    }
}
```

### 예시 사용법

```python
import requests

# 컨센서스 리포트 처리
response = requests.post(
    "http://localhost:8000/consensus",
    json={"file_path": "/path/to/report.pdf"}
)

result = response.json()
print(result['data']['stock_name'])  # 종목명
print(result['data']['target_price'])  # 목표가
```

## 🤖 AI 에이전트 시스템

### 감독자 에이전트 (Supervisor Agent)
- 워크플로우 전체를 관리하고 라우팅
- 결과 품질 검토 및 검증
- 구조화된 최종 출력 생성

### 컨센서스 처리 에이전트 (Consensus Processing Agent)
- PDF 텍스트 추출 및 분석
- 투자 정보 파싱 및 구조화
- 표준 JSON 형식으로 데이터 변환

## 📊 추출되는 정보

- **기본 정보**: 종목코드, 종목명, 리포트 제목/날짜/유형
- **애널리스트 정보**: 애널리스트명, 증권사명
- **투자 의견**: 투자등급, 의견 변경 여부
- **목표가**: 목표가, 목표가 변경 여부
- **분석 내용**: 전체 리포트 본문, 요약

## 🔧 개발 가이드

### API 문서
서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 로깅 및 모니터링
LangSmith를 통한 에이전트 실행 과정 추적 및 모니터링이 가능합니다.

## ⚠️ 주의사항

- Google API 키가 필수적으로 필요합니다
- PDF 파일 경로는 서버에서 접근 가능한 절대 경로여야 합니다
- 이미지 기반 PDF는 현재 지원되지 않습니다 (텍스트 추출 가능한 PDF만 지원)

## 📝 라이선스

이 프로젝트는 개인/내부 사용을 위한 것입니다.

## 🤝 기여

버그 리포트나 기능 개선 제안은 이슈를 통해 제출해주세요.