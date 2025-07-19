"""
시장 데이터 분석 에이전트
"""
import json
from typing import Dict, Any, List
from utils.core.agent_base import AnalysisAgent, AgentType, create_standard_prompt_template
from datetime import datetime


class MarketDataAgent(AnalysisAgent):
    """시장 데이터 분석 에이전트"""
    
    def __init__(self):
        from utils.core.agent_base import AgentConfig
        config = AgentConfig(
            name="market_data_agent",
            agent_type=AgentType.MARKET_DATA
        )
        AnalysisAgent.__init__(self, config)
        self.temperature = 0.3  # 정확한 시장 분석을 위해 낮은 temperature 사용
    
    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any]) -> str:
        """프롬프트 생성"""
        
        # 협업 데이터 포맷팅
        collaboration_info = ""
        if collaboration_data:
            collaboration_info = self._format_collaboration_data(collaboration_data)
        
        output_schema = {
            "market_trend": "시장 트렌드 분석",
            "price_movement": "주가 변동 분석",
            "volume_analysis": "거래량 분석",
            "volatility_analysis": "변동성 분석",
            "technical_indicators": "기술적 지표 분석",
            "market_sentiment": "시장 심리 분석",
            "sector_performance": "섹터 성과 분석",
            "market_risks": "시장 리스크 분석",
            "confidence_score": "분석 신뢰도 (0-100)"
        }
        
        # 개선된 프롬프트 템플릿
        prompt_template = """당신은 전문적인 시장 데이터 분석가입니다. 제공된 시장 데이터를 분석하여 주가와 시장 동향을 종합적으로 평가해주세요.

분석해야 할 시장 데이터:
{{input_data}}

분석 지침:
1. 시장 트렌드: 전반적인 시장 동향과 방향성 분석
2. 주가 변동: 현재 주가와 과거 대비 변동성 분석
3. 거래량 분석: 거래량 패턴과 투자자 관심도 분석
4. 변동성 분석: 주가 변동성과 리스크 수준 평가
5. 기술적 지표: PER, PBR, 베타 등 주요 지표 분석
6. 시장 심리: 투자자 심리와 시장 분위기 분석
7. 섹터 성과: 해당 섹터 내 상대적 성과 분석
8. 시장 리스크: 시장 변동성과 외부 요인에 의한 리스크 분석

{{collaboration_info}}

분석 결과를 다음 JSON 형식으로 제공해주세요:
{
    "market_trend": "시장 트렌드 분석 (구체적인 트렌드 방향과 근거)",
    "price_movement": "주가 변동 분석 (현재 주가, 변동성, 패턴 등 구체적 분석)",
    "volume_analysis": "거래량 분석 (거래량 패턴, 투자자 관심도 등 구체적 분석)",
    "volatility_analysis": "변동성 분석 (변동성 수준, 리스크 평가 등 구체적 분석)",
    "technical_indicators": "기술적 지표 분석 (PER, PBR, 베타 등 구체적 수치와 분석)",
    "market_sentiment": "시장 심리 분석 (투자자 심리, 시장 분위기 등 구체적 분석)",
    "sector_performance": "섹터 성과 분석 (섹터 내 상대적 성과 등 구체적 분석)",
    "market_risks": "시장 리스크 분석 (구체적인 리스크 요인들)",
    "confidence_score": "분석 신뢰도 (0-100, 데이터 품질과 분석 완성도 기반)"
}

중요: 제공된 시장 데이터를 기반으로 구체적인 수치와 분석을 제공하세요. 각 지표에 대해 정량적이고 정성적인 평가를 모두 수행하세요."""
        
        # 문자열 포맷팅을 안전하게 수행
        market_data = input_data.get("market_data", {})
        if not market_data and isinstance(input_data.get("data", {}), dict):
            market_data = input_data.get("data", {})
        if not market_data:
            market_data = input_data  # 전체 input_data를 사용
        
        input_data_str = json.dumps(market_data, ensure_ascii=False, indent=2)
        
        return prompt_template.replace("{{input_data}}", input_data_str).replace("{{collaboration_info}}", collaboration_info)
    
    def _format_collaboration_data(self, collaboration_data: Dict[str, Any]) -> str:
        """협업 데이터 포맷팅"""
        formatted = []
        
        for agent_name, data in collaboration_data.items():
            if agent_name == "financial_statement_agent":
                formatted.append("재무 데이터: " + json.dumps(data.get("financial_metrics", {}), ensure_ascii=False))
            elif agent_name == "news_analysis_agent":
                formatted.append("뉴스 분석: " + json.dumps(data.get("news_analysis", {}), ensure_ascii=False))
            elif agent_name == "risk_assessment_agent":
                formatted.append("리스크 분석: " + json.dumps(data.get("risk_analysis", {}), ensure_ascii=False))
        
        return "\n".join(formatted) if formatted else ""
    
    async def handle_collaboration_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """협업 요청 처리"""
        try:
            if message.get("request_type") == "validate_market_risk":
                # 시장 리스크 검증
                return await self._validate_market_risk(message.get("context"))
            
            elif message.get("request_type") == "get_market_data":
                # 시장 데이터 제공
                return await self._get_market_data(message.get("context"))
            
            elif message.get("request_type") == "analyze_market_trend":
                # 시장 트렌드 분석
                return await self._analyze_market_trend(message.get("context"))
            
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
    
    async def _validate_market_risk(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """시장 리스크 검증"""
        try:
            # Mock 데이터 (실제로는 실제 시장 데이터를 분석)
            return {
                "market_volatility": 0.25,
                "risk_level": "중간",
                "recommendation": "관찰",
                "market_trend": "안정적인 성장세",
                "status": "success"
            }
        
        except Exception as e:
            return {
                "error": f"시장 리스크 검증 실패: {str(e)}",
                "status": "failed"
            }
    
    async def _get_market_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """시장 데이터 제공"""
        try:
            return {
                "current_price": 75000,
                "volume": 50000000,
                "volatility": 0.25,
                "per": 8.8,
                "pbr": 1.7,
                "beta": 1.2,
                "status": "success"
            }
        
        except Exception as e:
            return {
                "error": f"시장 데이터 제공 실패: {str(e)}",
                "status": "failed"
            }
    
    async def _analyze_market_trend(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """시장 트렌드 분석"""
        try:
            return {
                "trend_direction": "상승",
                "trend_strength": "보통",
                "support_level": 70000,
                "resistance_level": 80000,
                "status": "success"
            }
        
        except Exception as e:
            return {
                "error": f"시장 트렌드 분석 실패: {str(e)}",
                "status": "failed"
            }

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """시장 데이터 분석 수행"""
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
                    "analysis_type": "market_data",
                    "analysis_result": response,
                    "agent_name": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 성능 통계 업데이트
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 결과에 메타데이터 추가
            result.update({
                "agent_name": self.name,
                "agent_type": "market_data",
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