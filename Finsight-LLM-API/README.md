# AI 기반 증시 투자 분석 시스템 - LLM Agent 모듈

이 프로젝트는 증권사 리포트를 분석하여 투자 인사이트를 제공하는 AI 기반 증시 분석 시스템입니다.
Ollama LLM API를 활용하여 세 가지 핵심 Agent(요약, 분석, 감성)를 구현하였습니다.

## 핵심 기능

- **Summary Agent**: 증권사 애널리스트 리포트를 요약하고 핵심 포인트를 추출합니다.
- **Analysis Agent**: 여러 요약된 리포트를 통합하여 기업별, 산업별 분석을 수행합니다.
- **Sentiment Agent**: 리포트의 감성 점수를 분석하고 긍정적/부정적 요인을 식별합니다.

## 설치 방법

### 1. 요구사항
- Python 3.10 이상
- [Ollama](<https://ollama.com>) 설치 및 실행

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. Ollama 모델 다운로드

```bash
ollama pull llama3
```

### 4. 환경 설정

`.env` 파일을 생성하고 설정을 커스터마이즈할 수 있습니다:

```
API_HOST=localhost
API_PORT=8000
OLLAMA_API_URL=http://localhost:11434
DEFAULT_MODEL=llama3
SUMMARY_MODEL=llama3
ANALYSIS_MODEL=llama3
SENTIMENT_MODEL=llama3

```

## 실행 방법

### API 서버 실행

```bash
python app.py
```

또는

```bash
uvicorn app:app --reload
```

### 테스트 실행

테스트 스크립트를 실행하여 각 Agent의 기능을 검증할 수 있습니다:

```bash
python test_agents.py
```

## API 엔드포인트

### 리포트 요약 API

- `POST /v1/report/summary` - 증권사 애널리스트 리포트 요약

### 리포트 통합 분석 API

- `POST /v1/report/analysis` - 여러 리포트 요약을 통합 분석

### 리포트 감성 분석 API

- `POST /v1/report/sentiment` - 리포트의 감성 분석

## 향후 개발 계획

- **Supervisor Agent**: 사용자 요청에 맞는 Agent와 모델을 선택하고 결과를 조율
- **RAG + ReRanker**: 벡터 DB를 활용한 관련 정보 검색 및 품질 향상
- **Function Calling**: 포맷 처리 개선 및 구조화된 출력 자동화

## 프로젝트 구조

```
investment-analysis-llm-api/
├── app.py                   # 메인 애플리케이션
├── config.py                # 설정 및 모델 관리
├── error_handlers.py        # 오류 처리
├── agents/                  # Agent 구현
│   ├── __init__.py
│   ├── summary_agent.py     # 리포트 요약 에이전트
│   ├── analysis_agent.py    # 통합 분석 에이전트
│   └── sentiment_agent.py   # 감성 분석 에이전트
├── routers/                 # API 라우터
│   ├── __init__.py
│   └── report_router.py     # 리포트 분석 API
├── models/                  # 데이터 모델
│   ├── __init__.py
│   └── schemas.py           # 요청/응답 스키마
├── utils/                   # 유틸리티
│   ├── __init__.py
│   └── llm_client.py        # LLM API 클라이언트
└── tests/                   # 테스트
    └── test_agents.py       # Agent 테스트
```