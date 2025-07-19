# FinsightAI Agent 구조

## 개요

FinsightAI는 협업 기반의 모듈화된 에이전트 시스템으로, 각 에이전트가 독립적으로 작업하면서도 필요 시 다른 에이전트와 협업하여 종합적인 금융 분석을 제공합니다.

## 새로운 Agent 구조

### 1. 데이터 소스별 Agent

#### `financial_statement_agent.py`
- **역할**: 재무제표 데이터 분석
- **기능**: 재무 건전성, 수익성, 유동성, 지급능력 평가
- **협업 대상**: market_data_agent, securities_report_agent, risk_assessment_agent, valuation_agent

#### `news_analysis_agent.py`
- **역할**: 뉴스 및 미디어 데이터 분석
- **기능**: 시장 영향도, 감성, 트렌드 분석
- **협업 대상**: market_data_agent, risk_assessment_agent, growth_analysis_agent

#### `securities_report_agent.py`
- **역할**: 증권사 리포트 분석
- **기능**: 애널리스트 의견, 목표주가, 핵심 인사이트 추출
- **협업 대상**: financial_statement_agent, market_data_agent, valuation_agent, peer_comparison_agent

#### `market_data_agent.py`
- **역할**: 시장 데이터 분석
- **기능**: 가격 움직임, 거래량, 기술적 지표 분석
- **협업 대상**: financial_statement_agent, news_analysis_agent, risk_assessment_agent, valuation_agent

### 2. 분석 유형별 Agent

#### `risk_assessment_agent.py`
- **역할**: 리스크 평가 및 관리
- **기능**: 재무적, 시장적, 운영적 리스크 종합 평가
- **협업 대상**: financial_statement_agent, news_analysis_agent, market_data_agent, securities_report_agent

#### `growth_analysis_agent.py`
- **역할**: 성장성 분석
- **기능**: 성장 잠재력, 성장 동력, 성장 리스크 분석
- **협업 대상**: financial_statement_agent, news_analysis_agent, securities_report_agent, market_data_agent

#### `valuation_agent.py`
- **역할**: 밸류에이션 분석
- **기능**: 다양한 밸류에이션 방법을 통한 공정가치 추정
- **협업 대상**: financial_statement_agent, market_data_agent, securities_report_agent, peer_comparison_agent

#### `peer_comparison_agent.py`
- **역할**: 동종업계 비교 분석
- **기능**: 경쟁사 비교, 상대적 위치 분석
- **협업 대상**: financial_statement_agent, market_data_agent, valuation_agent, growth_analysis_agent

### 3. 보고서 작성 Agent

#### `dday_report_agent.py`
- **역할**: D-day 투자 보고서 작성
- **기능**: 종합 분석을 통한 투자 결정 보고서 생성
- **협업 대상**: 모든 분석 에이전트

#### `dplus1_report_agent.py`
- **역할**: D+1 후속 보고서 작성
- **기능**: D-day 이후의 시장 반응과 새로운 정보를 종합하여 D+1 후속 보고서를 작성합니다.
- **협업 대상**: 모든 분석 에이전트

### 4. 지원 Agent

#### `document_processing_agent.py`
- **역할**: 문서 처리 및 구조화
- **기능**: 다양한 문서 형식을 분석 가능한 데이터로 변환
- **협업 대상**: data_quality_agent, supervisor_agent

#### `data_quality_agent.py`
- **역할**: 데이터 품질 관리
- **기능**: 데이터 완성도, 정확도, 일관성 평가
- **협업 대상**: document_processing_agent, supervisor_agent

#### `supervisor_agent.py`
- **역할**: 전체 시스템 감독 및 품질 관리
- **기능**: 모든 에이전트 결과 검토, 품질 관리, 승인 프로세스
- **협업 대상**: 모든 에이전트

## 협업 시스템

### CollaborationManager
- 에이전트 간 요청/응답 관리
- 캐시 시스템으로 성능 최적화
- 브로드캐스트 기능으로 전체 통신 지원

### 협업 방식
1. **직접 요청**: 특정 에이전트에게 데이터 요청
2. **브로드캐스트**: 모든 에이전트에게 동시 요청
3. **캐시 활용**: 중복 요청 방지 및 성능 향상

## 사용 예시

### 기본 사용법
```python
from agents import analyze_financial_statement, analyze_news, assess_risk

# 재무제표 분석
financial_result = await analyze_financial_statement(
    financial_data, "기업", "삼성전자"
)

# 뉴스 분석
news_result = await analyze_news(
    news_data, "기업", "삼성전자"
)

# 리스크 평가
risk_result = await assess_risk(
    risk_data, "기업", "삼성전자"
)
```

### 협업 활용
```python
# 여러 에이전트가 협업하여 종합 분석
from agents import generate_dday_report

report_data = {
    "financial_analysis": financial_result,
    "news_analysis": news_result,
    "risk_assessment": risk_result
}

dday_report = await generate_dday_report(
    report_data, "기업", "삼성전자"
)
```

## 설정 및 커스터마이징

### Temperature 설정
각 에이전트는 작업 특성에 맞는 temperature 값을 가집니다:
- **낮은 temperature (0.3)**: 정확한 분석이 필요한 에이전트
- **중간 temperature (0.4-0.5)**: 일반적인 분석 에이전트
- **높은 temperature (0.6)**: 창의적인 보고서 작성 에이전트

### 협업 대상 설정
각 에이전트의 `_get_collaboration_targets()` 메서드를 수정하여 협업 대상을 조정할 수 있습니다.

## 테스트

새로운 Agent 구조를 테스트하려면:

```bash
python test_new_agents_mock.py
```

이 테스트는 다음을 포함합니다:
- 개별 에이전트 기능 테스트
- 에이전트 간 협업 테스트
- Agent 구조 검증

## 성능 최적화

### 캐시 활용
- 5분 캐시로 중복 요청 방지
- 협업 데이터 재사용으로 성능 향상

### 병렬 처리
- asyncio를 활용한 비동기 처리
- 여러 에이전트 동시 실행 가능

### 리소스 관리
- 메모리 효율적인 데이터 구조
- 에러 처리 및 복구 메커니즘

## 향후 계획

1. **추가 에이전트**: 섹터별 전문 에이전트
2. **고급 협업**: 에이전트 간 학습 및 개선
3. **실시간 처리**: 스트리밍 데이터 처리
4. **확장성**: 클라우드 기반 분산 처리

## 문제 해결

### 일반적인 문제
1. **에이전트 등록 실패**: collaboration_manager 확인
2. **협업 데이터 누락**: 에이전트 간 연결 상태 확인
3. **성능 저하**: 캐시 설정 및 병렬 처리 확인

### 디버깅
- 각 에이전트의 로그 확인
- 협업 데이터 흐름 추적
- 성능 메트릭 모니터링 