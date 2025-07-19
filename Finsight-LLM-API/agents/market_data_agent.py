"""
시장 데이터 분석 에이전트
"""
import json
from typing import Dict, Any, List
from utils.agent_base import DataSourceAgent, AgentType, create_standard_prompt_template


class MarketDataAgent(DataSourceAgent):
    """시장 데이터 분석 에이전트"""
    
    def __init__(self):
        super().__init__("market_data_agent", AgentType.MARKET_DATA)
        self.temperature = 0.3  # 정확한 시장 분석을 위해 낮은 temperature 사용
    
    def _get_collaboration_targets(self) -> List[str]:
        """협업 가능한 에이전트 목록"""
        return [
            "financial_statement_agent",
            "news_analysis_agent",
            "valuation_agent",
            "risk_assessment_agent"
        ]
    
    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any]) -> str:
        """프롬프트 생성"""
        
        # 협업 데이터 포맷팅
        collaboration_info = ""
        if collaboration_data:
            collaboration_info = self._format_collaboration_data(collaboration_data)
        
        output_schema = {
            "market_trend": "시장 트렌드 분석",
            "price_movement": "가격 움직임 분석",
            "volume_analysis": "거래량 분석",
            "volatility_analysis": "변동성 분석",
            "technical_indicators": "기술적 지표 분석",
            "market_sentiment": "시장 심리 분석",
            "sector_performance": "섹터 성과 분석",
            "market_risks": "시장 리스크 분석",
            "confidence_score": "분석 신뢰도 (0-100)"
        }
        
        # 개선된 프롬프트 템플릿
        prompt_template = """당신은 전문적인 시장 데이터 분석가입니다. 제공된 시장 데이터를 분석하여 주가 움직임과 시장 동향을 종합적으로 평가해주세요.

분석해야 할 시장 데이터:
{{input_data}}

분석 지침:
1. 시장 트렌드: 주가의 전반적인 방향성과 추세 분석
2. 가격 움직임: 현재 주가, 변동폭, 상대적 성과 분석
3. 거래량 분석: 거래량 패턴과 가격과의 관계 분석
4. 변동성 분석: 주가 변동성과 리스크 수준 평가
5. 기술적 지표: PER, PBR, 베타 등 주요 지표 분석
6. 시장 심리: 투자자 심리와 시장 분위기 분석
7. 섹터 성과: 해당 섹터 내 상대적 성과 분석
8. 시장 리스크: 시장 변동성과 외부 요인에 의한 리스크 분석

{{collaboration_info}}

분석 결과를 다음 JSON 형식으로 제공해주세요:
{
    "market_trend": "시장 트렌드 분석 (상승/하락/횡보, 구체적인 근거 포함)",
    "price_movement": "가격 움직임 분석 (현재 주가, 변동폭, 상대적 성과)",
    "volume_analysis": "거래량 분석 (거래량 패턴, 가격과의 관계)",
    "volatility_analysis": "변동성 분석 (변동성 수준, 리스크 평가)",
    "technical_indicators": "기술적 지표 분석 (PER, PBR, 베타 등 구체적 수치)",
    "market_sentiment": "시장 심리 분석 (투자자 심리, 시장 분위기)",
    "sector_performance": "섹터 성과 분석 (섹터 내 상대적 성과)",
    "market_risks": "시장 리스크 분석 (변동성, 외부 요인 리스크)",
    "confidence_score": "분석 신뢰도 (0-100, 데이터 품질과 분석 완성도 기반)"
}

중요: 제공된 시장 데이터를 기반으로 구체적인 수치와 분석을 제공하세요. 주가, 거래량, 기술적 지표 등을 종합적으로 분석하여 시장 동향을 평가하세요."""
        
        # 문자열 포맷팅을 안전하게 수행
        target_type = input_data.get("target_type", "")
        target_name = input_data.get("target_name", "")
        input_data_str = json.dumps(input_data.get("market_data", {}), ensure_ascii=False, indent=2)
        
        return prompt_template.replace("{{input_data}}", input_data_str).replace("{{collaboration_info}}", collaboration_info)
    
    def _format_collaboration_data(self, collaboration_data: Dict[str, Any]) -> str:
        """협업 데이터 포맷팅"""
        formatted = []
        
        for agent_name, data in collaboration_data.items():
            if agent_name == "financial_statement_agent":
                formatted.append("재무 데이터: " + json.dumps(data.get("financial_metrics", {}), ensure_ascii=False))
            elif agent_name == "news_analysis_agent":
                formatted.append("뉴스 분석: " + json.dumps(data.get("news_analysis", {}), ensure_ascii=False))
            elif agent_name == "valuation_agent":
                formatted.append("밸류에이션: " + json.dumps(data.get("valuation_metrics", {}), ensure_ascii=False))
            elif agent_name == "risk_assessment_agent":
                formatted.append("리스크 평가: " + json.dumps(data.get("risk_factors", {}), ensure_ascii=False))
        
        return "\n".join(formatted) if formatted else ""


# 전역 인스턴스
market_data_agent = MarketDataAgent()


async def analyze_market_data(market_data: Dict[str, Any], target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    """시장 데이터 분석 실행"""
    input_data = {
        "data_source": "market_data",
        "market_data": market_data,
        "target_type": target_type,
        "target_name": target_name
    }
    
    return await market_data_agent.execute(input_data) 