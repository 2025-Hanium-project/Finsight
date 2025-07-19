"""
동종업계 비교 에이전트
"""
import json
from typing import Dict, Any, List
from datetime import datetime
from utils.core.agent_base import AnalysisAgent, AgentType, AgentConfig, create_standard_prompt_template


class PeerComparisonAgent(AnalysisAgent):
    """동종업계 비교 에이전트"""
    
    def __init__(self, config: AgentConfig):
        AnalysisAgent.__init__(self, config)
        self.temperature = 0.4  # 동종업계 비교를 위한 중간 temperature
    
    def _get_collaboration_targets(self) -> List[str]:
        """협업 가능한 에이전트 목록"""
        return [
            "financial_statement_agent",
            "market_data_agent",
            "valuation_agent",
            "growth_analysis_agent"
        ]
    
    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any]) -> str:
        """프롬프트 생성"""
        
        # 협업 데이터 포맷팅
        collaboration_info = ""
        if collaboration_data:
            collaboration_info = self._format_collaboration_data(collaboration_data)
        
        output_schema = {
            "peer_companies": "비교 대상 기업 목록",
            "financial_comparison": "재무 지표 비교",
            "valuation_comparison": "밸류에이션 지표 비교",
            "market_position": "시장 내 위치 분석",
            "competitive_advantage": "경쟁 우위 분석",
            "relative_performance": "상대적 성과 분석",
            "industry_ranking": "업계 내 순위",
            "peer_benchmarks": "동종업계 벤치마크",
            "comparative_risks": "비교 리스크 분석",
            "confidence_score": "분석 신뢰도 (0-100)"
        }
        
        template = create_standard_prompt_template(
            agent_name="동종업계 비교 전문가",
            task_description="제공된 데이터를 분석하여 동종업계 기업들과의 비교 분석을 수행합니다.",
            output_schema=output_schema,
            collaboration_info=collaboration_info
        )
        
        # 문자열 포맷팅을 안전하게 수행
        target_type = input_data.get("target_type", "")
        target_name = input_data.get("target_name", "")
        input_data_str = json.dumps(input_data.get("comparison_data", {}), ensure_ascii=False, indent=2)
        
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
            elif agent_name == "growth_analysis_agent":
                formatted.append("성장성 분석: " + json.dumps(data.get("growth_indicators", {}), ensure_ascii=False))
        
        return "\n".join(formatted) if formatted else ""

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """동종업계 비교 분석 수행"""
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
                    "analysis_type": "peer_comparison",
                    "analysis_result": response,
                    "agent_name": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 성능 통계 업데이트
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 결과에 메타데이터 추가
            result.update({
                "agent_name": self.name,
                "agent_type": "peer_comparison",
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
    name="peer_comparison_agent",
    agent_type=AgentType.PEER_COMPARISON
)
peer_comparison_agent = PeerComparisonAgent(config)


async def compare_peers(peer_data: Dict[str, Any], target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    """동종업계 비교 실행"""
    input_data = {
        "analysis_target": "peer_comparison",
        "peer_data": peer_data,
        "target_type": target_type,
        "target_name": target_name
    }
    
    return await peer_comparison_agent.execute(input_data) 