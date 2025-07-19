"""
D+1 보고서 작성 에이전트
"""
import json
from typing import Dict, Any, List
from datetime import datetime
from utils.core.agent_base import AnalysisAgent, AgentType, AgentConfig, create_standard_prompt_template


class DPlus1ReportAgent(AnalysisAgent):
    """D+1 보고서 작성 에이전트"""
    
    def __init__(self, config: AgentConfig):
        AnalysisAgent.__init__(self, config)
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
            "follow_up_analysis": "후속 분석 결과",
            "updated_recommendations": "업데이트된 권고사항",
            "market_reaction": "시장 반응 분석",
            "performance_review": "성과 검토",
            "risk_monitoring": "리스크 모니터링",
            "opportunity_assessment": "기회 요인 재평가",
            "next_steps": "다음 단계 계획",
            "lessons_learned": "학습된 교훈",
            "confidence_score": "보고서 신뢰도 (0-100)"
        }
        
        template = create_standard_prompt_template(
            agent_name="D+1 보고서 작성 전문가",
            task_description="제공된 데이터를 종합하여 D+1 투자 보고서를 작성합니다.",
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

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """D+1 보고서 분석 수행"""
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
                    "analysis_type": "dplus1_report",
                    "analysis_result": response,
                    "agent_name": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 성능 통계 업데이트
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 결과에 메타데이터 추가
            result.update({
                "agent_name": self.name,
                "agent_type": "dplus1_report",
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
    name="dplus1_report_agent",
    agent_type=AgentType.DPLUS1_REPORT
)
dplus1_report_agent = DPlus1ReportAgent(config)


async def generate_dplus1_report(report_data: Dict[str, Any], target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    """D+1 보고서 생성 실행"""
    input_data = {
        "report_type": "dplus1_report",
        "report_data": report_data,
        "target_type": target_type,
        "target_name": target_name
    }
    
    return await dplus1_report_agent.execute(input_data) 