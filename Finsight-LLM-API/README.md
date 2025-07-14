# AI 기반 증시 투자 분석 시스템 API

## 개요

증권사 리포트를 AI로 자동 분석하여 투자 인사이트를 제공하는 REST API 시스템입니다.

## 주요 기능

- **리포트 요약**: 긴 증권사 리포트를 핵심 내용으로 요약
- **감성 분석**: 리포트의 감성 상태와 긍정/부정 요인 분석
- **리스크 분석**: 투자 리스크 요인과 심각도 평가
- **성장성 분석**: 성장 동력과 투자 기회 분석
- **종합 분석**: D-day, D+1 상황별 종합 분석
- **품질 검토**: AI 분석 결과의 품질 관리

## 시스템 아키텍처

```
Finsight-LLM-API/
├── agents/                         # AI 분석 에이전트
│   ├── sentiment_agent.py          # 감성 분석
│   ├── risk_agent.py               # 리스크 분석
│   ├── growth_agent.py             # 성장성 분석
│   ├── summary_agent.py            # 리포트 요약
│   ├── analysis_agent.py           # 종합 분석
│   └── supervisor_agent.py         # 품질 검토
├── routers/                        # API 라우터
│   └── report_router.py            # 리포트 분석 API
├── models/                         # 데이터 모델
│   └── schemas.py                  # Pydantic 스키마
├── utils/                          # 유틸리티
│   ├── llm_client.py              # LLM 통신 및 구조화된 응답 생성
│   ├── data_models.py             # 공통 데이터 모델
│   ├── logging_config.py          # 로깅 설정
│   └── agent_base.py              # 에이전트 기본 클래스
├── error_handlers.py               # 에러 처리
├── config.py                       # 설정 관리
├── app.py                          # FastAPI 애플리케이션
├── test.py                         # API 테스트 스크립트
└── requirements.txt                # 의존성 목록
```

## API 엔드포인트

### 기본 상태 확인
- `GET /` : API 상태 확인
- `GET /security/status` : 보안 상태 확인

### 리포트 분석 API
- `POST /v1/report/summary` : 리포트 요약
- `POST /v1/report/sentiment` : 감성 분석
- `POST /v1/report/risk` : 리스크 분석
- `POST /v1/report/growth` : 성장성 분석
- `POST /v1/report/analysis/d-day` : D-day 종합 분석
- `POST /v1/report/analysis/d-plus1` : D+1 종합 분석
- `POST /v1/report/supervisor/review` : 품질 검토

---

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 설정
`.env` 파일을 생성하고 다음 설정을 추가:

#### Ollama 사용 시:
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

#### Gemini API 사용 시:
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

### 5. LLM 제공자 설정

#### Ollama 사용
- 로컬에서 Ollama 서버가 실행 중이어야 합니다
- `LLM_PROVIDER=ollama`로 설정
- 다양한 오픈소스 모델 사용 가능 (llama3, llama3.2, codellama 등)

#### Gemini API 사용
- Google AI Studio에서 API 키를 발급받아야 합니다
- `LLM_PROVIDER=gemini`로 설정
- `GEMINI_API_KEY` 환경변수에 API 키 설정
- 지원 모델: gemini-1.5-pro, gemini-1.5-flash 등

---

## 테스트

### 자동 테스트 실행
```bash
python test.py
```

테스트 결과는 `test_results.json` 파일에 저장됩니다.

#### Gemini API 연결 테스트
```bash
python test_gemini.py
```

이 테스트는 Gemini API 키가 올바르게 설정되어 있는지 확인합니다.

### 수동 테스트 예시

#### 리포트 요약
```bash
curl -X POST "http://localhost:8000/v1/report/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "report_content": "삼성전자는 2024년 4분기 실적 발표에서...",
    "report_info": {
      "company": "삼성전자",
      "date": "2024-01-15"
    }
  }'
```

#### 감성 분석
```bash
curl -X POST "http://localhost:8000/v1/report/sentiment" \
  -H "Content-Type: application/json" \
  -d '{
    "report_contents": ["리포트 내용1", "리포트 내용2"],
    "target_type": "company",
    "target_name": "삼성전자"
  }'
```

#### 리스크 분석
```bash
curl -X POST "http://localhost:8000/v1/report/risk" \
  -H "Content-Type: application/json" \
  -d '{
    "report_contents": ["리포트 내용1", "리포트 내용2"],
    "target_type": "company",
    "target_name": "삼성전자"
  }'
```

---

## 개발 가이드

### 에러 처리

- 모든 에러는 `error_handlers.py`에서 중앙 관리
- 보안을 위한 에러 메시지 sanitization 적용
- Rate limiting 및 IP 차단 기능 포함

### 로깅

- 구조화된 로깅 시스템 사용
- 요청별 고유 ID 추적
- 성능 메트릭 자동 수집

---

## TODO 항목

- [ ] 데이터베이스 연동
- [ ] 외부 데이터 소스 연동

---

## 라이센스

MIT License

---

## 기술 스택

- **웹 프레임워크**: FastAPI
- **AI/LLM**: Ollama (로컬), Google Gemini API
- **데이터 검증**: Pydantic
- **HTTP 클라이언트**: httpx
- **로깅**: Python logging
- **테스트**: pytest (TODO)
- **보안**: 자체 구현된 보안 미들웨어

---

## 성능 최적화

- 비동기 처리로 높은 동시성 지원
- 연결 풀링 및 재사용
- 구조화된 JSON 응답 파싱 최적화
- Rate limiting으로 시스템 보호

---

## 모니터링

- 요청/응답 시간 추적
- 에러율 모니터링
- 보안 이벤트 로깅
- LLM API 사용량 추적

---

## 기여하기

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## 지원 및 문의

프로젝트 관련 문의사항이나 버그 리포트는 GitHub Issues를 통해 제출해 주세요.
