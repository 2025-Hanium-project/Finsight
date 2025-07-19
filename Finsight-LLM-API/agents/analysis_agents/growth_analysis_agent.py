"""
성장성 분석 에이전트
"""
import json
from typing import Dict, Any, List
from utils.core.agent_base import AnalysisAgent, AgentType, AgentConfig, AgentCapability


class GrowthAnalysisAgent(AnalysisAgent):
    """성장성 분석 에이전트"""
    
    def __init__(self, config: AgentConfig):
        AnalysisAgent.__init__(self, config)
        self.temperature = 0.5  # 성장성 분석을 위한 중간 temperature 사용
    
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
            "growth_potential": "성장 잠재력 평가 (high/medium/low)",
            "revenue_growth": "매출 성장성 분석",
            "profit_growth": "이익 성장성 분석",
            "market_expansion": "시장 확장 분석",
            "product_development": "제품 개발 분석",
            "competitive_advantage": "경쟁 우위 분석",
            "industry_trends": "산업 트렌드 분석",
            "growth_drivers": "성장 동력 분석",
            "growth_risks": "성장 리스크 분석",
            "confidence_score": "분석 신뢰도 (0-100)"
        }
        
        # 개선된 프롬프트 템플릿
        prompt_template = """당신은 전문적인 기업 성장성 분석가입니다. 제공된 성장 데이터를 분석하여 기업의 성장 잠재력과 동력을 종합적으로 평가해주세요.

분석해야 할 성장 데이터:
{{input_data}}

분석 지침:
1. 과거 성장 추세: 3년간 매출, 이익, 자산, 자본 성장률 분석
2. 미래 성장 전망: 예상 매출/이익 성장률, 시장점유율 성장 분석
3. 시장 확장: 국내/글로벌 시장점유율, 신흥/선진시장 성장 분석
4. 제품 개발: 신제품 매출 비중, 특허 성장률, 혁신 지수 분석
5. 경쟁 우위: 비용/기술/브랜드/규모 우위 분석
6. 산업 트렌드: 반도체, AI, 5G, 자동차 전자제품 등 산업별 성장률 분석
7. 성장 동력: 주요 성장 요인과 동력 분석
8. 성장 리스크: 성장을 저해할 수 있는 위험 요소 분석

{{collaboration_info}}

분석 결과를 다음 JSON 형식으로 제공해주세요:
{
    "growth_potential": "성장 잠재력 평가 (high/medium/low, 구체적인 근거 포함)",
    "revenue_growth": "매출 성장성 분석 (과거 성장률, 미래 전망, 구체적 수치)",
    "profit_growth": "이익 성장성 분석 (영업이익/순이익 성장률, 구체적 수치)",
    "market_expansion": "시장 확장 분석 (국내/글로벌 시장점유율, 신시장 진출)",
    "product_development": "제품 개발 분석 (신제품 비중, 특허, 혁신 지수)",
    "competitive_advantage": "경쟁 우위 분석 (비용/기술/브랜드/규모 우위)",
    "industry_trends": "산업 트렌드 분석 (반도체, AI, 5G 등 산업별 성장률)",
    "growth_drivers": "성장 동력 분석 (주요 성장 요인과 동력)",
    "growth_risks": "성장 리스크 분석 (성장을 저해할 수 있는 위험 요소)",
    "confidence_score": "분석 신뢰도 (0-100, 데이터 품질과 분석 완성도 기반)"
}

중요: 제공된 성장 데이터를 기반으로 구체적인 수치와 분석을 제공하세요. 과거 성장 추세와 미래 성장 전망을 모두 고려하여 종합적인 성장성 평가를 수행하세요."""
        
        # 문자열 포맷팅을 안전하게 수행
        target_type = input_data.get("target_type", "")
        target_name = input_data.get("target_name", "")
        
        # 다양한 데이터 구조 지원
        growth_data = input_data.get("growth_data", {})
        if not growth_data and isinstance(input_data.get("data", {}), dict):
            growth_data = input_data.get("data", {})
        if not growth_data:
            growth_data = input_data  # 전체 input_data를 사용
        
        input_data_str = json.dumps(growth_data, ensure_ascii=False, indent=2)
        
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

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """성장성 분석 수행"""
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
                    "analysis_type": "growth_analysis",
                    "analysis_result": response,
                    "agent_name": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 성능 통계 업데이트
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 결과에 메타데이터 추가
            result.update({
                "agent_name": self.name,
                "agent_type": "growth_analysis",
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
    name="growth_analysis_agent",
    agent_type=AgentType.GROWTH_ANALYSIS
)
growth_analysis_agent = GrowthAnalysisAgent(config)


async def analyze_growth(growth_data: Dict[str, Any], target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    """성장성 분석 실행"""
    input_data = {
        "data_source": "growth_analysis",
        "growth_data": growth_data,
        "target_type": target_type,
        "target_name": target_name
    }
    
    return await growth_analysis_agent.execute(input_data) 