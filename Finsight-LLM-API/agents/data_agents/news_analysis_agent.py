"""
뉴스 분석 에이전트
"""
import json
from typing import Dict, Any, List
from utils.core.agent_base import AnalysisAgent, AgentType, create_standard_prompt_template
from datetime import datetime


class NewsAnalysisAgent(AnalysisAgent):
    """뉴스 분석 에이전트"""
    
    def __init__(self):
        from utils.core.agent_base import AgentConfig
        config = AgentConfig(
            name="news_analysis_agent",
            agent_type=AgentType.NEWS_ANALYSIS
        )
        AnalysisAgent.__init__(self, config)
        self.temperature = 0.4  # 뉴스 감정 분석을 위한 적절한 temperature
    
    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any]) -> str:
        """프롬프트 생성"""
        
        # 협업 데이터 포맷팅
        collaboration_info = ""
        if collaboration_data:
            collaboration_info = self._format_collaboration_data(collaboration_data)
        
        output_schema = {
            "sentiment_score": "전체 감정 점수 (0-100, 50이 중립)",
            "impact_level": "뉴스 영향도 (low/medium/high)",
            "key_topics": "주요 토픽 리스트",
            "market_reaction": "예상 시장 반응",
            "related_stocks": "관련 종목 리스트",
            "trend_analysis": "뉴스 트렌드 분석",
            "risk_implications": "리스크 영향 분석",
            "opportunity_analysis": "기회 요인 분석",
            "confidence_score": "분석 신뢰도 (0-100)"
        }
        
        # 개선된 프롬프트 템플릿
        prompt_template = """당신은 전문적인 뉴스 분석가입니다. 제공된 뉴스 데이터를 분석하여 기업과 관련된 뉴스의 감정과 시장 영향을 종합적으로 평가해주세요.

분석해야 할 뉴스 데이터:
{{input_data}}

분석 지침:
1. 감정 분석: 뉴스의 전반적인 감정을 0-100 점수로 평가 (50이 중립)
2. 영향도 평가: 뉴스가 시장에 미칠 영향의 크기를 평가
3. 주요 토픽: 뉴스에서 다루는 핵심 주제들을 추출
4. 시장 반응: 해당 뉴스에 대한 예상 시장 반응 분석
5. 관련 종목: 뉴스와 관련된 주식 종목들 식별
6. 트렌드 분석: 뉴스 트렌드와 패턴 분석
7. 리스크 영향: 부정적 뉴스의 리스크 요인 분석
8. 기회 요인: 긍정적 뉴스의 기회 요인 분석

{{collaboration_info}}

분석 결과를 다음 JSON 형식으로 제공해주세요:
{
    "sentiment_score": "전체 감정 점수 (0-100, 50이 중립, 구체적인 근거 포함)",
    "impact_level": "뉴스 영향도 (low/medium/high, 구체적인 근거 포함)",
    "key_topics": ["주요 토픽 리스트"],
    "market_reaction": "예상 시장 반응 (구체적인 주가 영향 분석)",
    "related_stocks": ["관련 종목 리스트"],
    "trend_analysis": "뉴스 트렌드 분석 (구체적인 트렌드 패턴)",
    "risk_implications": "리스크 영향 분석 (구체적인 리스크 요인들)",
    "opportunity_analysis": "기회 요인 분석 (구체적인 기회 요인들)",
    "confidence_score": "분석 신뢰도 (0-100, 데이터 품질과 분석 완성도 기반)"
}

중요: 제공된 뉴스 데이터를 기반으로 구체적인 분석을 제공하세요. 감정 분석과 시장 영향 분석을 모두 수행하세요."""
        
        # 문자열 포맷팅을 안전하게 수행
        news_data = input_data.get("news_data", {})
        if not news_data and isinstance(input_data.get("data", {}), dict):
            news_data = input_data.get("data", {})
        if not news_data:
            news_data = input_data  # 전체 input_data를 사용
        
        input_data_str = json.dumps(news_data, ensure_ascii=False, indent=2)
        
        return prompt_template.replace("{{input_data}}", input_data_str).replace("{{collaboration_info}}", collaboration_info)
    
    def _format_collaboration_data(self, collaboration_data: Dict[str, Any]) -> str:
        """협업 데이터 포맷팅"""
        formatted = []
        
        for agent_name, data in collaboration_data.items():
            if agent_name == "market_data_agent":
                formatted.append("시장 데이터: " + json.dumps(data.get("market_indicators", {}), ensure_ascii=False))
            elif agent_name == "risk_assessment_agent":
                formatted.append("리스크 분석: " + json.dumps(data.get("risk_analysis", {}), ensure_ascii=False))
            elif agent_name == "financial_statement_agent":
                formatted.append("재무 데이터: " + json.dumps(data.get("financial_metrics", {}), ensure_ascii=False))
        
        return "\n".join(formatted) if formatted else ""
    
    async def handle_collaboration_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """협업 요청 처리"""
        try:
            if message.get("request_type") == "check_negative_sentiment":
                # 부정적 감정 확인
                return await self._check_negative_sentiment(message.get("context"))
            
            elif message.get("request_type") == "get_sentiment_analysis":
                # 감정 분석 제공
                return await self._get_sentiment_analysis(message.get("context"))
            
            elif message.get("request_type") == "analyze_news_impact":
                # 뉴스 영향도 분석
                return await self._analyze_news_impact(message.get("context"))
            
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
    
    async def _check_negative_sentiment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """부정적 감정 확인"""
        try:
            # Mock 데이터 (실제로는 실제 뉴스 데이터를 분석)
            return {
                "sentiment_score": 85,
                "negative_news_count": 2,
                "overall_sentiment": "긍정적",
                "risk_implications": [
                    "반도체 업황 회복세",
                    "AI 반도체 시장 성장"
                ],
                "status": "success"
            }
        
        except Exception as e:
            return {
                "error": f"부정적 감정 확인 실패: {str(e)}",
                "status": "failed"
            }
    
    async def _get_sentiment_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """감정 분석 제공"""
        try:
            return {
                "sentiment_score": 90,
                "impact_level": "high",
                "key_topics": [
                    "삼성전자",
                    "4분기 실적",
                    "AI 반도체",
                    "메모리 반도체"
                ],
                "status": "success"
            }
        
        except Exception as e:
            return {
                "error": f"감정 분석 제공 실패: {str(e)}",
                "status": "failed"
            }
    
    async def _analyze_news_impact(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """뉴스 영향도 분석"""
        try:
            return {
                "market_reaction": "삼성전자 주가 상승 예상",
                "related_stocks": [
                    "삼성전자 (005930)",
                    "SK하이닉스 (000660)"
                ],
                "trend_analysis": "반도체 업황 회복세",
                "status": "success"
            }
        
        except Exception as e:
            return {
                "error": f"뉴스 영향도 분석 실패: {str(e)}",
                "status": "failed"
            }

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """뉴스 분석 수행"""
        return await self._execute_analysis(input_data)
    
    async def _execute_analysis(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """분석 실행"""
        try:
            start_time = datetime.now()
            
            # 프롬프트 생성
            prompt = self._create_prompt(input_data, collaboration_data)
            
            # LLM 호출
            from utils.llm.llm_client import generate_response
            response = await generate_response(
                prompt=prompt,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # 응답 파싱
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트 응답으로 처리
                result = {
                    "analysis_type": "news_analysis",
                    "analysis_result": response,
                    "agent_name": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 성능 통계 업데이트
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 결과에 메타데이터 추가
            result.update({
                "agent_name": self.name,
                "agent_type": "news_analysis",
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