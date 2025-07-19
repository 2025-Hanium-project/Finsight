"""
데이터 품질 관리 에이전트
"""
import json
from typing import Dict, Any, List
from datetime import datetime
from utils.core.agent_base import AnalysisAgent, AgentType, AgentConfig, create_standard_prompt_template


class DataQualityAgent(AnalysisAgent):
    """데이터 품질 관리 에이전트"""
    
    def __init__(self, config: AgentConfig):
        AnalysisAgent.__init__(self, config)
        self.temperature = 0.3  # 정확한 품질 평가를 위해 낮은 temperature
    
    def _get_collaboration_targets(self) -> List[str]:
        """협업 가능한 에이전트 목록"""
        return [
            "document_processing_agent",
            "supervisor_agent"
        ]
    
    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any]) -> str:
        """프롬프트 생성"""
        
        # 협업 데이터 포맷팅
        collaboration_info = ""
        if collaboration_data:
            collaboration_info = self._format_collaboration_data(collaboration_data)
        
        output_schema = {
            "overall_quality_score": "전체 품질 점수 (0-100)",
            "completeness_score": "완성도 점수 (0-100)",
            "accuracy_score": "정확도 점수 (0-100)",
            "consistency_score": "일관성 점수 (0-100)",
            "timeliness_score": "시의성 점수 (0-100)",
            "quality_issues": "품질 이슈 목록",
            "data_validation": "데이터 검증 결과",
            "improvement_suggestions": "품질 개선 제안",
            "confidence_score": "평가 신뢰도 (0-100)"
        }
        
        template = create_standard_prompt_template(
            agent_name="데이터 품질 평가 전문가",
            task_description="제공된 데이터의 품질을 평가하고 개선 방안을 제시합니다.",
            output_schema=output_schema,
            collaboration_info=collaboration_info
        )
        
        # 문자열 포맷팅을 안전하게 수행
        target_type = input_data.get("target_type", "")
        target_name = input_data.get("target_name", "")
        input_data_str = json.dumps(input_data.get("quality_data", {}), ensure_ascii=False, indent=2)
        
        return template.replace("{{target_type}}", target_type).replace("{{target_name}}", target_name).replace("{{input_data}}", input_data_str)
    
    def _format_collaboration_data(self, collaboration_data: Dict[str, Any]) -> str:
        """협업 데이터 포맷팅"""
        formatted = []
        
        for agent_name, data in collaboration_data.items():
            if agent_name == "document_processing_agent":
                formatted.append("문서 처리: " + json.dumps(data.get("processing_results", {}), ensure_ascii=False))
            elif agent_name == "supervisor_agent":
                formatted.append("감독자 피드백: " + json.dumps(data.get("supervisor_feedback", {}), ensure_ascii=False))
        
        return "\n".join(formatted) if formatted else ""

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 품질 분석 수행"""
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
                    "analysis_type": "data_quality",
                    "analysis_result": response,
                    "agent_name": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 성능 통계 업데이트
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 결과에 메타데이터 추가
            result.update({
                "agent_name": self.name,
                "agent_type": "data_quality",
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
    name="data_quality_agent",
    agent_type=AgentType.DATA_QUALITY
)
data_quality_agent = DataQualityAgent(config)


async def assess_data_quality(quality_data: Dict[str, Any], target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    """데이터 품질 평가 실행"""
    input_data = {
        "task_type": "data_quality_assessment",
        "quality_data": quality_data,
        "target_type": target_type,
        "target_name": target_name
    }
    
    return await data_quality_agent.execute(input_data) 