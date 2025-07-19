"""
증권사 리포트 분석 에이전트
"""
import json
from typing import Dict, Any, List
from utils.agent_base import DataSourceAgent, AgentType, create_standard_prompt_template


class SecuritiesReportAgent(DataSourceAgent):
    """증권사 리포트 분석 에이전트"""
    
    def __init__(self):
        super().__init__("securities_report_agent", AgentType.SECURITIES_REPORT)
        self.temperature = 0.4  # 리포트 분석을 위한 중간 temperature
    
    def _get_collaboration_targets(self) -> List[str]:
        """협업 가능한 에이전트 목록"""
        return [
            "financial_statement_agent",
            "market_data_agent",
            "valuation_agent",
            "peer_comparison_agent"
        ]
    
    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any]) -> str:
        """프롬프트 생성"""
        
        # 협업 데이터 포맷팅
        collaboration_info = ""
        if collaboration_data:
            collaboration_info = self._format_collaboration_data(collaboration_data)
        
        output_schema = {
            "report_summary": "리포트 주요 내용 요약",
            "analyst_opinion": "애널리스트 의견 및 투자의견",
            "target_price": "목표주가 및 근거",
            "key_insights": "핵심 인사이트",
            "risk_factors": "주요 리스크 요인",
            "growth_drivers": "성장 동력 분석",
            "valuation_analysis": "밸류에이션 분석",
            "peer_comparison": "동종업계 비교",
            "confidence_score": "분석 신뢰도 (0-100)"
        }
        
        template = create_standard_prompt_template(
            agent_name="증권사 리포트 분석 전문가",
            task_description="제공된 증권사 리포트를 분석하여 투자 의견, 목표가, 핵심 논리를 종합적으로 평가합니다.",
            output_schema=output_schema,
            collaboration_info=collaboration_info
        )
        
        # 문자열 포맷팅을 안전하게 수행
        target_type = input_data.get("target_type", "")
        target_name = input_data.get("target_name", "")
        input_data_str = json.dumps(input_data.get("report_data", {}), ensure_ascii=False, indent=2)
        
        return template.replace("{{target_type}}", target_type).replace("{{target_name}}", target_name).replace("{{input_data}}", input_data_str)
    
    def _format_collaboration_data(self, collaboration_data: Dict[str, Any]) -> str:
        """협업 데이터 포맷팅"""
        formatted = []
        
        for agent_name, data in collaboration_data.items():
            if agent_name == "financial_statement_agent":
                formatted.append("재무제표 분석: " + json.dumps(data.get("financial_analysis", {}), ensure_ascii=False))
            elif agent_name == "market_data_agent":
                formatted.append("시장 데이터: " + json.dumps(data.get("market_indicators", {}), ensure_ascii=False))
            elif agent_name == "valuation_agent":
                formatted.append("밸류에이션: " + json.dumps(data.get("valuation_metrics", {}), ensure_ascii=False))
            elif agent_name == "peer_comparison_agent":
                formatted.append("동종업계 비교: " + json.dumps(data.get("peer_analysis", {}), ensure_ascii=False))
        
        return "\n".join(formatted) if formatted else ""


# 전역 인스턴스
securities_report_agent = SecuritiesReportAgent()


async def analyze_securities_report(report_data: Dict[str, Any], target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    """증권사 리포트 분석 실행"""
    input_data = {
        "data_source": "securities_report",
        "report_data": report_data,
        "target_type": target_type,
        "target_name": target_name
    }
    
    return await securities_report_agent.execute(input_data) 