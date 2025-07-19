# FinsightAI - AI 기반 금융 분석 시스템

## 개요

FinsightAI는 증권사 리포트와 금융 데이터를 AI로 분석하여 투자 인사이트를 제공하는 종합 금융 분석 시스템입니다.

## 주요 기능

### 📊 데이터 분석
- **재무제표 분석**: 기업 재무상태 종합 분석
- **뉴스 분석**: 실시간 뉴스 감성 및 영향도 분석
- **증권사 리포트 분석**: 전문가 리포트 요약 및 인사이트 추출
- **시장 데이터 분석**: 주가, 거래량, 지표 분석

### 🤖 AI 에이전트 시스템
- **리스크 평가**: 투자 리스크 요인 분석
- **성장성 분석**: 기업 성장 동력 및 전망 분석
- **가치 평가**: 기업 가치 평가 및 투자 적정성 분석
- **동료 비교**: 업종 내 경쟁사 비교 분석

### 📈 리포트 생성
- **D-day 리포트**: 실시간 시장 상황 분석
- **D+1 리포트**: 다음날 전망 및 투자 전략
- **종합 분석**: 다각도 분석 결과 통합 리포트

### 🔧 시스템 관리
- **품질 관리**: AI 분석 결과 품질 검토
- **문서 처리**: PDF, 이미지 등 다양한 문서 처리
- **협업 시스템**: 다중 에이전트 협업 분석

## 시스템 아키텍처

```
Finsight-LLM-API/
├── agents/                         # AI 분석 에이전트
│   ├── data_agents/               # 데이터 수집/분석 에이전트
│   ├── analysis_agents/           # 전문 분석 에이전트
│   ├── report_agents/             # 리포트 생성 에이전트
│   └── support_agents/            # 지원 에이전트
├── routers/                        # API 라우터
│   └── report_router.py           # 리포트 분석 API
├── models/                         # 데이터 모델
│   └── schemas.py                 # Pydantic 스키마
├── utils/                          # 유틸리티
│   ├── core/                      # 핵심 유틸리티
│   ├── llm/                       # LLM 통신
│   ├── collaboration/             # 협업 시스템
│   └── performance/               # 성능 모니터링
├── rag_system/                     # RAG 시스템
├── tests/                          # 테스트 코드
├── error_handlers.py               # 에러 처리
├── config.py                       # 설정 관리
├── app.py                          # FastAPI 애플리케이션
└── requirements.txt                # 의존성 목록
```

## API 엔드포인트

### 기본 상태 확인
- `GET /` : API 상태 확인
- `GET /api` : API 정보
- `GET /api/v1/health` : 헬스체크
- `GET /api/system/status` : 시스템 상태

### 에이전트 API
- `POST /api/v1/agents/financial-statement` : 재무제표 분석
- `POST /api/v1/agents/news-analysis` : 뉴스 분석
- `POST /api/v1/agents/securities-report` : 증권사 리포트 분석
- `POST /api/v1/agents/market-data` : 시장 데이터 분석
- `POST /api/v1/agents/risk-assessment` : 리스크 평가
- `POST /api/v1/agents/growth-analysis` : 성장성 분석
- `POST /api/v1/agents/valuation` : 가치 평가
- `POST /api/v1/agents/peer-comparison` : 동료 비교

### 리포트 API
- `POST /api/v1/agents/dday-report` : D-day 리포트
- `POST /api/v1/agents/dplus1-report` : D+1 리포트

### 협업 API
- `POST /api/v1/collaboration/basic` : 기본 협업
- `POST /api/v1/collaboration/advanced` : 고급 협업
- `POST /api/v1/collaboration/optimized` : 최적화 협업
- `GET /api/collaboration/status` : 협업 상태

### 대시보드 API
- `GET /api/v1/dashboard/summary` : 대시보드 요약
- `GET /api/v1/dashboard/agent/{agent_name}` : 에이전트 상세
- `GET /api/v1/dashboard/alerts` : 시스템 알림
- `GET /api/v1/dashboard/visualization` : 시각화 데이터

### 워크플로우 API
- `POST /api/v1/workflow/comprehensive` : 종합 워크플로우

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 설정
`.env` 파일을 생성하고 다음 설정을 추가:

#### Gemini API 사용 (권장)
```env
# LLM 제공자 설정
LLM_PROVIDER=gemini

# Gemini API 설정
GEMINI_API_KEY=your_gemini_api_key_here
DEFAULT_GEMINI_MODEL=gemini-1.5-pro

# API 서버 설정
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# 보안 설정
SECRET_KEY=your_secret_key_here
```

#### Ollama 사용 (로컬)
```env
# LLM 제공자 설정
LLM_PROVIDER=ollama

# Ollama API 설정
OLLAMA_API_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama3.2:latest

# API 서버 설정
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# 보안 설정
SECRET_KEY=your_secret_key_here
```

### 3. 서버 실행
```bash
python app.py
```

또는

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 4. API 문서 확인
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 테스트

### 전체 테스트 실행
```bash
python -m tests.test_api
```

### 개별 테스트 실행
```bash
# API 테스트
python -m tests.test_api

# 단위 테스트
python -m tests.test_unit

# 협업 테스트
python -m tests.test_collaboration
```

## 사용 예시

### 재무제표 분석
```bash
curl -X POST "http://localhost:8000/api/v1/agents/financial-statement" \
  -H "Content-Type: application/json" \
  -d '{
    "target_type": "company",
    "target_name": "삼성전자",
    "symbol": "005930",
    "reports": ["재무제표 데이터"],
    "context": "분석 컨텍스트"
  }'
```

### 뉴스 분석
```bash
curl -X POST "http://localhost:8000/api/v1/agents/news-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "target_type": "company",
    "target_name": "삼성전자",
    "symbol": "005930",
    "reports": ["뉴스 데이터"],
    "context": "분석 컨텍스트"
  }'
```

### 협업 분석
```bash
curl -X POST "http://localhost:8000/api/v1/collaboration/basic" \
  -H "Content-Type: application/json" \
  -d '{
    "target_type": "company",
    "target_name": "삼성전자",
    "symbol": "005930",
    "reports": ["분석 데이터"],
    "context": "분석 컨텍스트"
  }'
```

## 개발 가이드

### 에러 처리
- 모든 에러는 `error_handlers.py`에서 중앙 관리
- 보안을 위한 에러 메시지 sanitization 적용
- Rate limiting 및 IP 차단 기능 포함

### 로깅
- 구조화된 로깅 시스템
- 에이전트별 로그 분리
- 성능 모니터링 및 알림

### 확장성
- 모듈화된 에이전트 시스템
- 플러그인 방식의 기능 확장
- 마이크로서비스 아키텍처 지원

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 기여

버그 리포트, 기능 요청, 풀 리퀘스트를 환영합니다.
