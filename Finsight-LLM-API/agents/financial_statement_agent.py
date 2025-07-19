"""
재무제표 분석 에이전트
"""
import json
from typing import Dict, Any, List
from utils.agent_base import DataSourceAgent, AgentType, create_standard_prompt_template


class FinancialStatementAgent(DataSourceAgent):
    """재무제표 분석 에이전트"""
    
    def __init__(self):
        super().__init__("financial_statement_agent", AgentType.FINANCIAL_STATEMENT)
        self.temperature = 0.3  # 정확한 분석을 위해 낮은 temperature 사용
    
    def _get_collaboration_targets(self) -> List[str]:
        """협업 가능한 에이전트 목록"""
        return [
            "market_data_agent",
            "securities_report_agent",
            "risk_assessment_agent",
            "valuation_agent"
        ]
    
    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any]) -> str:
        """프롬프트 생성"""
        
        # 협업 데이터 포맷팅
        collaboration_info = ""
        if collaboration_data:
            collaboration_info = self._format_collaboration_data(collaboration_data)
        
        output_schema = {
            "financial_health": "재무 건전성 평가 (우수/양호/보통/불량)",
            "profitability_analysis": "수익성 분석 결과",
            "liquidity_analysis": "유동성 분석 결과", 
            "solvency_analysis": "지급능력 분석 결과",
            "growth_trends": "성장 추세 분석",
            "key_ratios": "주요 재무비율 분석",
            "risk_factors": "재무적 리스크 요인",
            "recommendations": "재무 개선 권고사항",
            "confidence_score": "분석 신뢰도 (0-100)"
        }
        
        # 개선된 프롬프트 템플릿
        prompt_template = """당신은 전문적인 재무제표 분석가입니다. 제공된 재무 데이터를 분석하여 기업의 재무 건전성을 종합적으로 평가해주세요.

분석해야 할 재무 데이터:
{{input_data}}

분석 지침:
1. 수익성 분석: 매출, 영업이익, 순이익의 규모와 성장률을 분석
2. 유동성 분석: 유동비율, 당좌비율, 현금비율 등을 계산하여 단기 지급능력 평가
3. 지급능력 분석: 부채비율, 이자보상배율 등을 통해 장기 지급능력 평가
4. 성장성 분석: 매출성장률, 이익성장률, 자산성장률 등을 분석
5. 재무비율 분석: ROE, ROA, 영업이익률, 순이익률 등을 계산

{{collaboration_info}}

분석 결과를 다음 JSON 형식으로 제공해주세요:
{
    "financial_health": "재무 건전성 평가 (우수/양호/보통/불량)",
    "profitability_analysis": "수익성 분석 결과 (구체적인 수치와 평가 포함)",
    "liquidity_analysis": "유동성 분석 결과 (유동비율, 당좌비율 등 계산 포함)",
    "solvency_analysis": "지급능력 분석 결과 (부채비율, 이자보상배율 등 포함)",
    "growth_trends": "성장 추세 분석 (매출성장률, 이익성장률 등 포함)",
    "key_ratios": "주요 재무비율 분석 (ROE, ROA, 영업이익률, 순이익률 등)",
    "risk_factors": "재무적 리스크 요인 (구체적인 위험 요소들)",
    "recommendations": "재무 개선 권고사항 (구체적인 개선 방안)",
    "confidence_score": "분석 신뢰도 (0-100, 데이터 품질과 분석 완성도 기반)"
}

중요: 제공된 데이터를 기반으로 구체적인 수치와 분석을 제공하세요. 데이터가 충분하지 않은 경우에도 가능한 분석을 수행하고 신뢰도를 낮게 설정하세요."""
        
        # 문자열 포맷팅을 안전하게 수행
        target_type = input_data.get("target_type", "")
        target_name = input_data.get("target_name", "")
        input_data_str = json.dumps(input_data.get("financial_data", {}), ensure_ascii=False, indent=2)
        
        return prompt_template.replace("{{input_data}}", input_data_str).replace("{{collaboration_info}}", collaboration_info)
    
    def _format_collaboration_data(self, collaboration_data: Dict[str, Any]) -> str:
        """협업 데이터 포맷팅"""
        formatted = []
        
        for agent_name, data in collaboration_data.items():
            if agent_name == "market_data_agent":
                formatted.append("시장 데이터: " + json.dumps(data.get("market_indicators", {}), ensure_ascii=False))
            elif agent_name == "securities_report_agent":
                formatted.append("증권사 리포트: " + json.dumps(data.get("report_insights", {}), ensure_ascii=False))
            elif agent_name == "risk_assessment_agent":
                formatted.append("리스크 평가: " + json.dumps(data.get("risk_factors", {}), ensure_ascii=False))
            elif agent_name == "valuation_agent":
                formatted.append("밸류에이션: " + json.dumps(data.get("valuation_metrics", {}), ensure_ascii=False))
        
        return "\n".join(formatted) if formatted else ""


# 전역 인스턴스
financial_statement_agent = FinancialStatementAgent()


async def analyze_financial_statement(financial_data: Dict[str, Any], target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    """재무제표 분석 실행"""
    input_data = {
        "data_source": "financial_statement",
        "financial_data": financial_data,
        "target_type": target_type,
        "target_name": target_name
    }
    
    return await financial_statement_agent.execute(input_data) 