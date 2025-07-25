"""
리스크 평가 에이전트
"""
import json
from typing import Dict, Any, List
from utils.core.agent_base import AnalysisAgent, AgentType, AgentConfig, AgentCapability


class RiskAssessmentAgent(AnalysisAgent):
    """리스크 평가 에이전트"""
    
    def __init__(self, config: AgentConfig):
        AnalysisAgent.__init__(self, config)
        self.temperature = 0.3  # 정확한 리스크 평가를 위해 낮은 temperature 사용
    
    def _get_collaboration_targets(self) -> List[str]:
        """협업 가능한 에이전트 목록"""
        return [
            "financial_statement_agent",
            "market_data_agent",
            "news_analysis_agent",
            "valuation_agent"
        ]
    
    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any]) -> str:
        """프롬프트 생성"""
        
        # 협업 데이터 포맷팅
        collaboration_info = ""
        if collaboration_data:
            collaboration_info = self._format_collaboration_data(collaboration_data)
        
        output_schema = {
            "risk_level": "전체 리스크 레벨 (low/medium/high)",
            "financial_risks": "재무적 리스크 분석",
            "market_risks": "시장 리스크 분석",
            "operational_risks": "운영 리스크 분석",
            "regulatory_risks": "규제 리스크 분석",
            "credit_risks": "신용 리스크 분석",
            "liquidity_risks": "유동성 리스크 분석",
            "risk_mitigation": "리스크 완화 방안",
            "confidence_score": "분석 신뢰도 (0-100)"
        }
        
        # 개선된 프롬프트 템플릿
        prompt_template = """당신은 전문적인 기업 리스크 평가 분석가입니다. 제공된 리스크 데이터를 분석하여 기업의 다양한 리스크 요인을 종합적으로 평가해주세요.

분석해야 할 리스크 데이터:
{{input_data}}

분석 지침:
1. 시장 리스크: 변동성, 베타, 시장과의 상관관계 등을 분석
2. 재무 리스크: 부채비율, 이자보상배율, 유동비율 등을 분석
3. 운영 리스크: 지역 집중도, 고객 집중도, 공급업체 의존도 등을 분석
4. 규제 리스크: 규정 준수, 규제 변화, 수출 제한 등을 분석
5. 신용 리스크: 신용등급, 부도 확률, 회수율 등을 분석
6. 유동성 리스크: 현금흐름, 유동자산, 단기부채 등을 분석
7. 종합 리스크 평가: 모든 리스크 요인을 종합하여 전체 리스크 레벨 결정
8. 리스크 완화 방안: 각 리스크에 대한 구체적인 완화 전략 제시

{{collaboration_info}}

분석 결과를 다음 JSON 형식으로 제공해주세요:
{
    "risk_level": "전체 리스크 레벨 (low/medium/high, 구체적인 근거 포함)",
    "financial_risks": "재무적 리스크 분석 (부채비율, 이자보상배율, 유동비율 등 구체적 분석)",
    "market_risks": "시장 리스크 분석 (변동성, 베타, 시장 상관관계 등 구체적 분석)",
    "operational_risks": "운영 리스크 분석 (지역/고객/공급업체 집중도 등 구체적 분석)",
    "regulatory_risks": "규제 리스크 분석 (규정 준수, 규제 변화 등 구체적 분석)",
    "credit_risks": "신용 리스크 분석 (신용등급, 부도 확률 등 구체적 분석)",
    "liquidity_risks": "유동성 리스크 분석 (현금흐름, 유동자산 등 구체적 분석)",
    "risk_mitigation": "리스크 완화 방안 (각 리스크에 대한 구체적인 완화 전략)",
    "confidence_score": "분석 신뢰도 (0-100, 데이터 품질과 분석 완성도 기반)"
}

중요: 제공된 리스크 데이터를 기반으로 구체적인 수치와 분석을 제공하세요. 각 리스크 요인에 대해 정량적이고 정성적인 평가를 모두 수행하세요."""
        
        # 문자열 포맷팅을 안전하게 수행
        target_type = input_data.get("target_type", "")
        target_name = input_data.get("target_name", "")
        
        # 다양한 데이터 구조 지원
        risk_data = input_data.get("risk_data", {})
        if not risk_data and isinstance(input_data.get("data", {}), dict):
            risk_data = input_data.get("data", {})
        if not risk_data:
            risk_data = input_data  # 전체 input_data를 사용
        
        input_data_str = json.dumps(risk_data, ensure_ascii=False, indent=2)
        
        return prompt_template.replace("{{input_data}}", input_data_str).replace("{{collaboration_info}}", collaboration_info)
    
    def _format_collaboration_data(self, collaboration_data: Dict[str, Any]) -> str:
        """협업 데이터 포맷팅"""
        formatted = []
        
        for agent_name, data in collaboration_data.items():
            if agent_name == "financial_statement_agent":
                formatted.append("재무 데이터: " + json.dumps(data.get("financial_metrics", {}), ensure_ascii=False))
            elif agent_name == "market_data_agent":
                formatted.append("시장 데이터: " + json.dumps(data.get("market_indicators", {}), ensure_ascii=False))
            elif agent_name == "news_analysis_agent":
                formatted.append("뉴스 분석: " + json.dumps(data.get("news_analysis", {}), ensure_ascii=False))
            elif agent_name == "valuation_agent":
                formatted.append("밸류에이션: " + json.dumps(data.get("valuation_metrics", {}), ensure_ascii=False))
        
        return "\n".join(formatted) if formatted else ""
    
    async def handle_collaboration_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """협업 요청 처리"""
        try:
            if message.get("request_type") == "financial_health_metrics":
                # 재무제표 Agent에게 재무 건전성 정보 요청
                return await self._get_financial_health_metrics(message.get("context"))
            
            elif message.get("request_type") == "negative_news_check":
                # 뉴스 Agent에게 부정적 뉴스 확인 요청
                return await self._check_negative_news(message.get("context"))
            
            elif message.get("request_type") == "market_risk_validation":
                # 시장 데이터 Agent에게 시장 리스크 검증 요청
                return await self._validate_market_risk(message.get("context"))
            
            else:
                return {
                    "error": f"지원하지 않는 요청 타입: {message.get('request_type')}",
                    "status": "failed"
                }
        
        except Exception as e:
            self.logger.error(f"협업 요청 처리 실패: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def _get_financial_health_metrics(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """재무 건전성 지표 조회"""
        try:
            # 재무제표 Agent에게 요청
            response = await self.request_collaboration(
                target_agent="financial_statement_agent",
                request_type="get_financial_metrics",
                context=context,
                priority=0 # MessagePriority.HIGH 제거
            )
            
            if response:
                return {
                    "financial_health": response.get("financial_health", "unknown"),
                    "key_ratios": response.get("key_ratios", {}),
                    "risk_factors": response.get("risk_factors", []),
                    "status": "success"
                }
            else:
                return {
                    "error": "재무제표 Agent로부터 응답을 받지 못했습니다",
                    "status": "failed"
                }
        
        except Exception as e:
            return {
                "error": f"재무 건전성 지표 조회 실패: {str(e)}",
                "status": "failed"
            }
    
    async def _check_negative_news(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """부정적 뉴스 확인"""
        try:
            # 뉴스 분석 Agent에게 요청
            response = await self.request_collaboration(
                target_agent="news_analysis_agent",
                request_type="check_negative_sentiment",
                context=context,
                priority=0 # MessagePriority.HIGH 제거
            )
            
            if response:
                return {
                    "negative_news_count": response.get("negative_news_count", 0),
                    "sentiment_score": response.get("sentiment_score", 0),
                    "risk_implications": response.get("risk_implications", []),
                    "status": "success"
                }
            else:
                return {
                    "error": "뉴스 분석 Agent로부터 응답을 받지 못했습니다",
                    "status": "failed"
                }
        
        except Exception as e:
            return {
                "error": f"부정적 뉴스 확인 실패: {str(e)}",
                "status": "failed"
            }
    
    async def _validate_market_risk(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """시장 리스크 검증"""
        try:
            # 시장 데이터 Agent에게 요청
            response = await self.request_collaboration(
                target_agent="market_data_agent",
                request_type="validate_market_risk",
                context=context,
                priority=0 # MessagePriority.HIGH 제거
            )
            
            if response:
                return {
                    "market_volatility": response.get("market_volatility", 0),
                    "risk_level": response.get("risk_level", "unknown"),
                    "recommendation": response.get("recommendation", ""),
                    "status": "success"
                }
            else:
                return {
                    "error": "시장 데이터 Agent로부터 응답을 받지 못했습니다",
                    "status": "failed"
                }
        
        except Exception as e:
            return {
                "error": f"시장 리스크 검증 실패: {str(e)}",
                "status": "failed"
            }

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """리스크 평가 분석 수행"""
        return await self._execute_analysis(input_data)
    
    async def _execute_analysis(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """분석 실행"""
        try:
            from datetime import datetime
            start_time = datetime.now()
            
            # 프롬프트 생성
            prompt = self._create_prompt(input_data, collaboration_data)
            
            # LLM 호출
            from utils.llm.llm_client import generate_response
            from utils.llm.llm_utils import extract_json_from_response
            response = await generate_response(
                prompt=prompt,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # 응답 파싱
            try:
                json_text = extract_json_from_response(response)
                result = json.loads(json_text)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트 응답으로 처리
                result = {
                    "analysis_type": "risk_assessment",
                    "analysis_result": response,
                    "agent_name": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 성능 통계 업데이트
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 결과에 메타데이터 추가
            result.update({
                "agent_name": self.name,
                "agent_type": "risk_assessment",
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            return {
                "error": str(e),
                "agent_name": self.name,
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }


# 전역 인스턴스
config = AgentConfig(
    name="risk_assessment_agent",
    agent_type=AgentType.RISK_ASSESSMENT
)
risk_assessment_agent = RiskAssessmentAgent(config)


async def analyze_risk(risk_data: Dict[str, Any], target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    """리스크 평가 실행"""
    input_data = {
        "data_source": "risk_assessment",
        "risk_data": risk_data,
        "target_type": target_type,
        "target_name": target_name
    }
    
    return await risk_assessment_agent.execute(input_data) 