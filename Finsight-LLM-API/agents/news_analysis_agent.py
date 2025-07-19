"""
뉴스 분석 에이전트
"""
import json
from typing import Dict, Any, List
from utils.agent_base import DataSourceAgent, AgentType, create_standard_prompt_template


class NewsAnalysisAgent(DataSourceAgent):
    """뉴스 분석 에이전트"""
    
    def __init__(self):
        super().__init__("news_analysis_agent", AgentType.NEWS_ANALYSIS)
        self.temperature = 0.4  # 뉴스 분석을 위한 적절한 temperature
    
    def _get_collaboration_targets(self) -> List[str]:
        """협업 가능한 에이전트 목록"""
        return [
            "financial_statement_agent",
            "market_data_agent",
            "sentiment_agent",
            "risk_assessment_agent"
        ]
    
    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any]) -> str:
        """프롬프트 생성"""
        
        # 협업 데이터 포맷팅
        collaboration_info = ""
        if collaboration_data:
            collaboration_info = self._format_collaboration_data(collaboration_data)
        
        output_schema = {
            "sentiment_score": "감성 점수 (-100 ~ +100)",
            "impact_level": "시장 영향도 (high/medium/low)",
            "key_topics": "주요 토픽 및 키워드",
            "market_reaction": "예상 시장 반응",
            "related_stocks": "관련 종목들",
            "trend_analysis": "트렌드 분석",
            "risk_implications": "리스크 영향",
            "opportunity_analysis": "기회 요소 분석",
            "confidence_score": "분석 신뢰도 (0-100)"
        }
        
        # 개선된 프롬프트 템플릿
        prompt_template = """당신은 전문적인 금융 뉴스 분석가입니다. 제공된 뉴스 데이터를 분석하여 시장에 미치는 영향을 종합적으로 평가해주세요.

분석해야 할 뉴스 데이터:
{{input_data}}

분석 지침:
1. 감성 분석: 뉴스의 전반적인 톤과 감정을 분석 (-100: 매우 부정적 ~ +100: 매우 긍정적)
2. 영향도 평가: 해당 뉴스가 시장에 미칠 수 있는 영향의 크기를 평가
3. 주요 토픽 추출: 뉴스에서 다루는 핵심 주제와 키워드를 식별
4. 시장 반응 예측: 뉴스가 주가와 시장에 미칠 수 있는 영향을 분석
5. 관련 종목 분석: 뉴스와 관련된 기업들과 종목들을 파악
6. 트렌드 분석: 뉴스가 반영하는 산업적, 시장적 트렌드를 분석
7. 리스크 평가: 뉴스에서 파악할 수 있는 위험 요소들을 분석
8. 기회 요소: 뉴스에서 발견할 수 있는 투자 기회를 분석

{{collaboration_info}}

분석 결과를 다음 JSON 형식으로 제공해주세요:
{
    "sentiment_score": "감성 점수 (-100 ~ +100, 구체적인 수치)",
    "impact_level": "시장 영향도 (high/medium/low)",
    "key_topics": "주요 토픽 및 키워드 (구체적인 주제들)",
    "market_reaction": "예상 시장 반응 (구체적인 영향 분석)",
    "related_stocks": "관련 종목들 (종목코드나 기업명)",
    "trend_analysis": "트렌드 분석 (산업적, 시장적 트렌드)",
    "risk_implications": "리스크 영향 (구체적인 위험 요소들)",
    "opportunity_analysis": "기회 요소 분석 (투자 기회 요소들)",
    "confidence_score": "분석 신뢰도 (0-100, 뉴스 품질과 분석 완성도 기반)"
}

중요: 제공된 뉴스 데이터를 기반으로 구체적인 분석을 제공하세요. 헤드라인, 내용, 감성, 영향도 등을 종합적으로 고려하여 분석하세요."""
        
        # 문자열 포맷팅을 안전하게 수행
        target_type = input_data.get("target_type", "")
        target_name = input_data.get("target_name", "")
        input_data_str = json.dumps(input_data.get("news_data", {}), ensure_ascii=False, indent=2)
        
        return prompt_template.replace("{{input_data}}", input_data_str).replace("{{collaboration_info}}", collaboration_info)
    
    def _format_collaboration_data(self, collaboration_data: Dict[str, Any]) -> str:
        """협업 데이터 포맷팅"""
        formatted = []
        
        for agent_name, data in collaboration_data.items():
            if agent_name == "financial_statement_agent":
                formatted.append("재무 데이터: " + json.dumps(data.get("financial_metrics", {}), ensure_ascii=False))
            elif agent_name == "market_data_agent":
                formatted.append("시장 데이터: " + json.dumps(data.get("market_indicators", {}), ensure_ascii=False))
            elif agent_name == "sentiment_agent":
                formatted.append("감성 분석: " + json.dumps(data.get("sentiment_analysis", {}), ensure_ascii=False))
            elif agent_name == "risk_assessment_agent":
                formatted.append("리스크 평가: " + json.dumps(data.get("risk_factors", {}), ensure_ascii=False))
        
        return "\n".join(formatted) if formatted else ""


# 전역 인스턴스
news_analysis_agent = NewsAnalysisAgent()


async def analyze_news(news_data: Dict[str, Any], target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    """뉴스 분석 실행"""
    input_data = {
        "data_source": "news",
        "news_data": news_data,
        "target_type": target_type,
        "target_name": target_name
    }
    
    return await news_analysis_agent.execute(input_data) 