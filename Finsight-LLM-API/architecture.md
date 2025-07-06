# Finsight LLM API 아키텍처

## 1. 시스템 개요

AI 기반 증시 투자 분석 시스템으로, 증권사 리포트를 자동 분석하여 투자 인사이트를 제공하는 REST API입니다.

### 1.1 핵심 원칙
- **단순성**: 복잡한 워크플로우 없이 직접적인 agent 호출
- **안정성**: 각 agent 독립 동작으로 장애 격리
- **확장성**: 새로운 agent 쉽게 추가 가능
- **성능**: 비동기 처리로 높은 동시성

## 2. 시스템 구조

### 2.1 레이어 구조
```
┌─────────────────────────────────────┐
│           API Layer                 │  ← FastAPI 라우터
├─────────────────────────────────────┤
│          Agent Layer                │  ← AI 분석 에이전트들
├─────────────────────────────────────┤
│         Service Layer               │  ← LLM 통신, 유틸리티
├─────────────────────────────────────┤
│        Security Layer               │  ← 보안, 인증, 로깅
└─────────────────────────────────────┘
```

### 2.2 컴포넌트 구조
```
app.py
├── routers/report_router.py
│   ├── /summary        → summary_agent
│   ├── /sentiment      → sentiment_agent
│   ├── /risk          → risk_agent
│   ├── /growth        → growth_agent
│   ├── /analysis/*    → analysis_agent
│   └── /supervisor/*  → supervisor_agent
├── agents/
│   ├── BaseAgent (공통 기능)
│   ├── ReportAnalysisAgent (리포트 분석 공통)
│   └── 각 전문 에이전트들
├── utils/
│   ├── llm_client (LLM 통신)
│   ├── data_models (데이터 구조)
│   └── logging_config (로깅)
└── error_handlers (에러 처리)
```

### 2.3 데이터 흐름
```
Client Request
    ↓
FastAPI Router
    ↓
Security Middleware
    ↓
Input Validation
    ↓
Agent Processing
    ↓
LLM Communication
    ↓
Response Processing
    ↓
Error Handling
    ↓
JSON Response
```

### 2.4 API 라우터
# TODO: 워크플로우 엔드포인트 구현 필요시 추가
- `/report/summary`, `/report/sentiment`, `/report/risk`, `/report/growth`, `/report/analysis/d-day`, `/report/analysis/d-plus1`: 개별 agent 및 analysis 테스트용 엔드포인트

## 3. 에이전트 시스템

### 3.1 에이전트 계층 구조
```
BaseAgent
├── ReportAnalysisAgent
│   ├── SentimentAgent
│   ├── RiskAgent
│   ├── GrowthAgent
│   └── AnalysisAgent
├── SummaryAgent
└── SupervisorAgent
```

### 3.2 에이전트 역할
- **SentimentAgent**: 감성 분석 (긍정/부정 요인, 점수)
- **RiskAgent**: 리스크 요인 분석 (심각도, 확률)
- **GrowthAgent**: 성장성 분석 (동력, 기회)
- **SummaryAgent**: 리포트 요약 (핵심 포인트)
- **AnalysisAgent**: 종합 분석 (D-day, D+1)
- **SupervisorAgent**: 품질 검토 (결과 평가)

### 3.3 에이전트 표준 인터페이스
```python
class BaseAgent:
    async def process(self, input_data: StandardInput) -> StandardOutput
    def _validate_input(self, input_data: Any) -> bool
    def _create_prompt(self, input_data: Any) -> str
```

## 4. LLM 통신

### 4.1 LLM 클라이언트 구조
```
LLMClient
├── generate_response()           # 일반 텍스트 응답
├── generate_structured_response() # 구조화된 JSON 응답
├── _parse_and_validate()        # JSON 파싱 및 검증
└── _retry_mechanism()           # 재시도 로직
```

### 4.2 응답 처리 파이프라인
```
LLM Raw Response
    ↓
Response Cleaning
    ↓
JSON Extraction
    ↓
Schema Validation
    ↓
Fallback Processing
    ↓
Structured Output
```

## 5. 보안 시스템

### 5.1 보안 레이어
- **Input Sanitization**: XSS, SQL Injection 방지
- **Rate Limiting**: 요청 빈도 제한
- **IP Blocking**: 악성 IP 차단
- **Error Sanitization**: 민감 정보 마스킹

### 5.2 보안 미들웨어 흐름
```
Request
    ↓
IP Check
    ↓
Rate Limit Check
    ↓
Content-Type Validation
    ↓
Input Sanitization
    ↓
Processing
    ↓
Response Headers
    ↓
Response
```

## 6. 에러 처리

### 6.1 에러 계층
```
BaseAnalysisError
├── AgentError
├── LLMError
├── ValidationError
├── TimeoutError
└── ParsingError
```

### 6.2 에러 처리 흐름
```
Exception Occurs
    ↓
Error Classification
    ↓
Security Sanitization
    ↓
Logging
    ↓
User Response
```

## 7. 로깅 시스템

### 7.1 로깅 구조
- **요청 로깅**: 모든 API 요청/응답
- **성능 로깅**: 처리 시간, 메트릭
- **에러 로깅**: 상세 에러 정보
- **보안 로깅**: 보안 이벤트

### 7.2 로그 레벨
- **DEBUG**: 개발 디버깅 정보
- **INFO**: 일반 동작 정보
- **WARNING**: 주의 필요 상황
- **ERROR**: 에러 상황
- **CRITICAL**: 심각한 시스템 오류

## 8. 성능 최적화

### 8.1 비동기 처리
- FastAPI 비동기 처리
- HTTP 클라이언트 연결 풀링
- 동시 요청 처리

### 8.2 캐싱 전략 (TODO)
- [ ] LLM 응답 캐싱
- [ ] 자주 사용되는 분석 결과 캐싱
- [ ] Redis 기반 분산 캐싱

## 9. 모니터링

### 9.1 메트릭 수집
- API 응답 시간
- 에러율
- LLM API 사용량
- 시스템 리소스

### 9.2 알림 시스템 (TODO)
- [ ] 에러율 임계치 알림
- [ ] 응답 시간 지연 알림
- [ ] 시스템 리소스 알림

## 10. 배포 및 운영

### 10.1 환경 구성
```
Development
├── Local Ollama
├── Debug Logging
└── Development DB

Production
├── Remote LLM API
├── Production Logging
└── Production DB
```

### 10.2 확장성 계획
- **수평 확장**: 멀티 인스턴스 배포
- **부하 분산**: 로드 밸런서 적용
- **데이터베이스**: 읽기 전용 복제본

## 11. 보안 고려사항

### 11.1 데이터 보호
- 입력 데이터 암호화
- 로그 데이터 마스킹
- API 키 보안 관리

### 11.2 접근 제어 (TODO)
- [ ] JWT 기반 인증
- [ ] Role-based 접근 제어
- [ ] API 키 관리

## 12. TODO 항목

### 12.1 단기 계획
- [ ] 단위 테스트 추가
- [ ] CI/CD 파이프라인
- [ ] 성능 테스트

### 12.2 중기 계획
- [ ] 데이터베이스 연동
- [ ] 캐싱 시스템
- [ ] 모니터링 대시보드

### 12.3 장기 계획
- [ ] 마이크로서비스 분할
- [ ] 쿠버네티스 배포
- [ ] 멀티 리전 지원