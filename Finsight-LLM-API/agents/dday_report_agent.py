"""
D-day 보고서 작성 에이전트
"""
import json
from typing import Dict, Any, List
from utils.agent_base import ReportAgent, AgentType, create_standard_prompt_template


class DDayReportAgent(ReportAgent):
    """D-day 보고서 작성 에이전트"""
    
    def __init__(self):
        super().__init__("dday_report_agent", AgentType.DDAY_REPORT)
        self.temperature = 0.6  # 창의적인 보고서 작성을 위한 높은 temperature
    
    def _get_collaboration_targets(self) -> List[str]:
        """협업 가능한 에이전트 목록"""
        return [
            "financial_statement_agent",
            "news_analysis_agent",
            "market_data_agent",
            "risk_assessment_agent",
            "growth_analysis_agent",
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
            "executive_summary": "실행 요약",
            "key_findings": "주요 발견사항",
            "investment_recommendation": "투자 권고사항",
            "risk_assessment": "리스크 평가",
            "growth_outlook": "성장 전망",
            "valuation_analysis": "밸류에이션 분석",
            "market_analysis": "시장 분석",
            "peer_comparison": "동종업계 비교",
            "action_items": "실행 항목",
            "confidence_score": "보고서 신뢰도 (0-100)"
        }
        
        # 개선된 프롬프트 템플릿
        prompt_template = """당신은 전문적인 투자 보고서 작성 전문가입니다. 제공된 종합 데이터를 분석하여 {target_name}에 대한 D-Day 투자 보고서를 작성해주세요.

분석해야 할 종합 데이터:
{input_data}

분석 지침:
1. 실행 요약: 핵심 투자 포인트와 결론을 간결하게 요약
2. 주요 발견사항: 재무, 시장, 뉴스, 리스크, 성장성 분석의 핵심 결과
3. 투자 권고사항: 매수/매도/보유 권고와 근거
4. 리스크 평가: 주요 리스크 요인과 영향도 분석
5. 성장 전망: 미래 성장 가능성과 동력 분석
6. 밸류에이션 분석: 적정 주가와 밸류에이션 방법론
7. 시장 분석: 시장 상황과 경쟁 환경 분석
8. 동종업계 비교: 경쟁사 대비 강점과 약점
9. 실행 항목: 투자자에게 필요한 구체적 행동 지침

{collaboration_info}

분석 결과를 다음 JSON 형식으로 제공해주세요:
{{
    "executive_summary": "실행 요약 (핵심 투자 포인트와 결론)",
    "key_findings": "주요 발견사항 (재무, 시장, 뉴스, 리스크, 성장성 분석 결과)",
    "investment_recommendation": "투자 권고사항 (매수/매도/보유 권고와 근거)",
    "risk_assessment": "리스크 평가 (주요 리스크 요인과 영향도)",
    "growth_outlook": "성장 전망 (미래 성장 가능성과 동력)",
    "valuation_analysis": "밸류에이션 분석 (적정 주가와 밸류에이션 방법론)",
    "market_analysis": "시장 분석 (시장 상황과 경쟁 환경)",
    "peer_comparison": "동종업계 비교 (경쟁사 대비 강점과 약점)",
    "action_items": "실행 항목 (투자자에게 필요한 구체적 행동 지침)",
    "confidence_score": "보고서 신뢰도 (0-100, 데이터 품질과 분석 완성도 기반)"
}}

중요: 제공된 종합 데이터를 기반으로 구체적이고 실용적인 투자 보고서를 작성하세요. 각 섹션에서 명확한 결론과 근거를 제시하세요."""
        
        # 문자열 포맷팅을 안전하게 수행
        target_type = input_data.get("target_type", "")
        target_name = input_data.get("target_name", "")
        input_data_str = json.dumps(input_data.get("report_data", {}), ensure_ascii=False, indent=2)
        
        return prompt_template.format(
            target_name=target_name,
            input_data=input_data_str,
            collaboration_info=collaboration_info
        )
    
    def _format_collaboration_data(self, collaboration_data: Dict[str, Any]) -> str:
        """협업 데이터 포맷팅"""
        formatted = []
        
        for agent_name, data in collaboration_data.items():
            if agent_name == "financial_statement_agent":
                formatted.append("재무제표 분석: " + json.dumps(data.get("financial_analysis", {}), ensure_ascii=False))
            elif agent_name == "news_analysis_agent":
                formatted.append("뉴스 분석: " + json.dumps(data.get("news_analysis", {}), ensure_ascii=False))
            elif agent_name == "market_data_agent":
                formatted.append("시장 데이터: " + json.dumps(data.get("market_indicators", {}), ensure_ascii=False))
            elif agent_name == "risk_assessment_agent":
                formatted.append("리스크 평가: " + json.dumps(data.get("risk_factors", {}), ensure_ascii=False))
            elif agent_name == "growth_analysis_agent":
                formatted.append("성장성 분석: " + json.dumps(data.get("growth_indicators", {}), ensure_ascii=False))
            elif agent_name == "valuation_agent":
                formatted.append("밸류에이션: " + json.dumps(data.get("valuation_metrics", {}), ensure_ascii=False))
            elif agent_name == "peer_comparison_agent":
                formatted.append("동종업계 비교: " + json.dumps(data.get("peer_analysis", {}), ensure_ascii=False))
        
        return "\n".join(formatted) if formatted else ""


# 전역 인스턴스
dday_report_agent = DDayReportAgent()


async def generate_dday_report(report_data: Dict[str, Any], target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    """D-day 보고서 생성 실행"""
    input_data = {
        "report_type": "dday_report",
        "report_data": report_data,
        "target_type": target_type,
        "target_name": target_name
    }
    
    return await dday_report_agent.execute(input_data) 