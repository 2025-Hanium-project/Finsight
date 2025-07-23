"""
밸류에이션 에이전트
"""
import json
from typing import Dict, Any, List
from utils.core.agent_base import AnalysisAgent, AgentType, AgentConfig, AgentCapability


class ValuationAgent(AnalysisAgent):
    """밸류에이션 에이전트"""
    
    def __init__(self, config: AgentConfig):
        AnalysisAgent.__init__(self, config)
        self.temperature = 0.3  # 정확한 밸류에이션을 위해 낮은 temperature 사용
    
    def _get_collaboration_targets(self) -> List[str]:
        """협업 가능한 에이전트 목록"""
        return [
            "financial_statement_agent",
            "market_data_agent",
            "growth_analysis_agent",
            "risk_assessment_agent"
        ]
    
    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any]) -> str:
        """프롬프트 생성"""
        
        # 협업 데이터 포맷팅
        collaboration_info = ""
        if collaboration_data:
            collaboration_info = self._format_collaboration_data(collaboration_data)
        
        output_schema = {
            "fair_value": "적정 주가 (구체적인 금액)",
            "valuation_methods": "사용된 밸류에이션 방법들",
            "pe_ratio": "PER 분석",
            "pb_ratio": "PBR 분석",
            "ev_ebitda": "EV/EBITDA 분석",
            "dcf_valuation": "DCF 밸류에이션 결과",
            "asset_based": "자산 기반 밸류에이션",
            "relative_valuation": "상대가치 분석",
            "valuation_risks": "밸류에이션 리스크",
            "confidence_score": "분석 신뢰도 (0-100)"
        }
        
        # 개선된 프롬프트 템플릿
        prompt_template = """당신은 전문적인 기업 밸류에이션 분석가입니다. 제공된 밸류에이션 데이터를 분석하여 기업의 적정 가치를 종합적으로 평가해주세요.

분석해야 할 밸류에이션 데이터:
{{input_data}}

분석 지침:
1. PER(Price-Earnings Ratio) 분석: 현재 PER과 업계 평균 PER 비교
2. PBR(Price-Book Ratio) 분석: 현재 PBR과 업계 평균 PBR 비교
3. EV/EBITDA 분석: 기업가치 대비 EBITDA 비율 분석
4. DCF(Discounted Cash Flow) 분석: 미래 현금흐름을 현재가치로 할인
5. 배당수익률 분석: 현재 배당수익률과 성장성 고려
6. 상대가치 분석: 경쟁사와의 밸류에이션 지표 비교
7. 자산 기반 분석: 순자산가치(NAV) 기반 평가
8. 성장성 고려: 미래 성장 전망을 반영한 밸류에이션

{{collaboration_info}}

분석 결과를 다음 JSON 형식으로 제공해주세요:
{
    "fair_value": "적정 주가 (구체적인 금액, 예: 85,000원)",
    "valuation_methods": "사용된 밸류에이션 방법들 (PER, PBR, DCF 등)",
    "pe_ratio": "PER 분석 (현재 PER, 업계 평균, 평가)",
    "pb_ratio": "PBR 분석 (현재 PBR, 업계 평균, 평가)",
    "ev_ebitda": "EV/EBITDA 분석 (현재 비율, 업계 평균, 평가)",
    "dcf_valuation": "DCF 밸류에이션 결과 (할인율, 성장률, 적정가치)",
    "asset_based": "자산 기반 밸류에이션 (순자산가치, 청산가치 등)",
    "relative_valuation": "상대가치 분석 (경쟁사 비교 결과)",
    "valuation_risks": "밸류에이션 리스크 (가정의 불확실성, 시장 변동성 등)",
    "confidence_score": "분석 신뢰도 (0-100, 데이터 품질과 분석 완성도 기반)"
}

중요: 제공된 밸류에이션 데이터를 기반으로 구체적인 수치와 분석을 제공하세요. 각 밸류에이션 방법의 결과를 명확히 제시하고, 적정 주가를 구체적인 금액으로 제시하세요."""
        
        # 문자열 포맷팅을 안전하게 수행
        target_type = input_data.get("target_type", "")
        target_name = input_data.get("target_name", "")
        
        # 다양한 데이터 구조 지원
        valuation_data = input_data.get("valuation_data", {})
        if not valuation_data and isinstance(input_data.get("data", {}), dict):
            valuation_data = input_data.get("data", {})
        if not valuation_data:
            valuation_data = input_data  # 전체 input_data를 사용
        
        input_data_str = json.dumps(valuation_data, ensure_ascii=False, indent=2)
        
        return prompt_template.replace("{{input_data}}", input_data_str).replace("{{collaboration_info}}", collaboration_info)
    
    def _format_collaboration_data(self, collaboration_data: Dict[str, Any]) -> str:
        """협업 데이터 포맷팅"""
        formatted = []
        
        for agent_name, data in collaboration_data.items():
            if agent_name == "financial_statement_agent":
                formatted.append("재무 데이터: " + json.dumps(data.get("financial_metrics", {}), ensure_ascii=False))
            elif agent_name == "market_data_agent":
                formatted.append("시장 데이터: " + json.dumps(data.get("market_indicators", {}), ensure_ascii=False))
            elif agent_name == "growth_analysis_agent":
                formatted.append("성장성 분석: " + json.dumps(data.get("growth_indicators", {}), ensure_ascii=False))
            elif agent_name == "risk_assessment_agent":
                formatted.append("리스크 평가: " + json.dumps(data.get("risk_factors", {}), ensure_ascii=False))
        
        return "\n".join(formatted) if formatted else ""

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """밸류에이션 분석 수행"""
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
                    "analysis_type": "valuation",
                    "analysis_result": response,
                    "agent_name": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 성능 통계 업데이트
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 결과에 메타데이터 추가
            result.update({
                "agent_name": self.name,
                "agent_type": "valuation",
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
    name="valuation_agent",
    agent_type=AgentType.VALUATION
)
valuation_agent = ValuationAgent(config)


async def analyze_valuation(valuation_data: Dict[str, Any], target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    """밸류에이션 분석 실행"""
    input_data = {
        "data_source": "valuation",
        "valuation_data": valuation_data,
        "target_type": target_type,
        "target_name": target_name
    }
    
    return await valuation_agent.execute(input_data) 