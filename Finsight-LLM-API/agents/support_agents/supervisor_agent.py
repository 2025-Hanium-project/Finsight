"""
감독자 에이전트
"""
import json
from typing import Dict, Any, List
from datetime import datetime
from utils.core.agent_base import AnalysisAgent, AgentType, AgentConfig, create_standard_prompt_template


class SupervisorAgent(AnalysisAgent):
    """감독자 에이전트"""
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="supervisor_agent",
                agent_type=AgentType.SUPERVISOR
            )
        AnalysisAgent.__init__(self, config)
        self.temperature = 0.4  # 감독을 위한 중간 temperature
    
    def _get_collaboration_targets(self) -> List[str]:
        """협업 가능한 에이전트 목록"""
        return [
            "financial_statement_agent",
            "news_analysis_agent",
            "securities_report_agent",
            "market_data_agent",
            "risk_assessment_agent",
            "growth_analysis_agent",
            "valuation_agent",
            "peer_comparison_agent",
            "dday_report_agent",
            "dplus1_report_agent",
            "document_processing_agent",
            "data_quality_agent"
        ]
    
    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any]) -> str:
        """프롬프트 생성"""
        
        # 협업 데이터 포맷팅
        collaboration_info = ""
        if collaboration_data:
            collaboration_info = self._format_collaboration_data(collaboration_data)
        
        output_schema = {
            "overall_assessment": "전체 평가 결과",
            "quality_review": "품질 검토 결과",
            "consistency_check": "일관성 검사 결과",
            "recommendations": "개선 권고사항",
            "approval_status": "승인 상태 (승인/수정요청/거부)",
            "priority_actions": "우선순위 액션",
            "risk_alerts": "리스크 알림",
            "performance_metrics": "성과 지표",
            "confidence_score": "감독 신뢰도 (0-100)"
        }
        
        template = create_standard_prompt_template(
            agent_name="에이전트 감독 전문가",
            task_description="모든 에이전트의 작업을 감독하고 조율하여 최적의 결과를 도출합니다.",
            output_schema=output_schema,
            collaboration_info=collaboration_info
        )
        
        # 문자열 포맷팅을 안전하게 수행
        target_type = input_data.get("target_type", "")
        target_name = input_data.get("target_name", "")
        input_data_str = json.dumps(input_data.get("supervision_data", {}), ensure_ascii=False, indent=2)
        
        return template.replace("{{target_type}}", target_type).replace("{{target_name}}", target_name).replace("{{input_data}}", input_data_str)
    
    def _format_collaboration_data(self, collaboration_data: Dict[str, Any]) -> str:
        """협업 데이터 포맷팅"""
        formatted = []
        
        for agent_name, data in collaboration_data.items():
            if agent_name == "financial_statement_agent":
                formatted.append("재무제표 분석: " + json.dumps(data.get("financial_analysis", {}), ensure_ascii=False))
            elif agent_name == "news_analysis_agent":
                formatted.append("뉴스 분석: " + json.dumps(data.get("news_analysis", {}), ensure_ascii=False))
            elif agent_name == "securities_report_agent":
                formatted.append("증권사 리포트: " + json.dumps(data.get("report_insights", {}), ensure_ascii=False))
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
            elif agent_name == "dday_report_agent":
                formatted.append("D-day 보고서: " + json.dumps(data.get("report_content", {}), ensure_ascii=False))
            elif agent_name == "dplus1_report_agent":
                formatted.append("D+1 보고서: " + json.dumps(data.get("report_content", {}), ensure_ascii=False))
            elif agent_name == "document_processing_agent":
                formatted.append("문서 처리: " + json.dumps(data.get("processing_results", {}), ensure_ascii=False))
            elif agent_name == "data_quality_agent":
                formatted.append("데이터 품질: " + json.dumps(data.get("quality_metrics", {}), ensure_ascii=False))
        
        return "\n".join(formatted) if formatted else ""

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """감독자 분석 수행"""
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
                    "analysis_type": "supervision",
                    "analysis_result": response,
                    "agent_name": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 성능 통계 업데이트
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 결과에 메타데이터 추가
            result.update({
                "agent_name": self.name,
                "agent_type": "supervision",
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
    name="supervisor_agent",
    agent_type=AgentType.SUPERVISOR
)
supervisor_agent = SupervisorAgent(config)


async def supervise_analysis(supervision_data: Dict[str, Any], target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    """감독자 분석 실행"""
    input_data = {
        "task_type": "supervision",
        "supervision_data": supervision_data,
        "target_type": target_type,
        "target_name": target_name
    }
    
    return await supervisor_agent.execute(input_data)