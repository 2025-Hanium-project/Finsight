"""
리스크 평가 에이전트
"""
import json
from typing import Dict, Any, List
from utils.agent_base import AnalysisAgent, AgentType, create_standard_prompt_template


class RiskAssessmentAgent(AnalysisAgent):
    """리스크 평가 에이전트"""
    
    def __init__(self):
        super().__init__("risk_assessment_agent", AgentType.RISK_ASSESSMENT)
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


# 전역 인스턴스
risk_assessment_agent = RiskAssessmentAgent()


async def analyze_risk(risk_data: Dict[str, Any], target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    """리스크 평가 실행"""
    input_data = {
        "data_source": "risk_assessment",
        "risk_data": risk_data,
        "target_type": target_type,
        "target_name": target_name
    }
    
    return await risk_assessment_agent.execute(input_data) 