"""
문서 처리 에이전트
"""
import json
from typing import Dict, Any, List
from utils.agent_base import SupportAgent, AgentType, create_standard_prompt_template


class DocumentProcessingAgent(SupportAgent):
    """문서 처리 에이전트"""
    
    def __init__(self):
        super().__init__("document_processing_agent", AgentType.DOCUMENT_PROCESSING)
        self.temperature = 0.3  # 정확한 문서 처리를 위해 낮은 temperature
    
    def _get_collaboration_targets(self) -> List[str]:
        """협업 가능한 에이전트 목록"""
        return [
            "data_quality_agent",
            "supervisor_agent"
        ]
    
    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any]) -> str:
        """프롬프트 생성"""
        
        # 협업 데이터 포맷팅
        collaboration_info = ""
        if collaboration_data:
            collaboration_info = self._format_collaboration_data(collaboration_data)
        
        output_schema = {
            "document_type": "문서 타입 식별",
            "extracted_data": "추출된 데이터",
            "data_structure": "데이터 구조 분석",
            "quality_score": "데이터 품질 점수 (0-100)",
            "processing_errors": "처리 오류 목록",
            "recommendations": "처리 개선 권고사항",
            "confidence_score": "처리 신뢰도 (0-100)"
        }
        
        template = create_standard_prompt_template(
            agent_name="문서 처리 전문가",
            task_description="제공된 문서를 분석하고 처리하여 구조화된 데이터로 변환합니다.",
            output_schema=output_schema,
            collaboration_info=collaboration_info
        )
        
        # 문자열 포맷팅을 안전하게 수행
        target_type = input_data.get("target_type", "")
        target_name = input_data.get("target_name", "")
        input_data_str = json.dumps(input_data.get("document_data", {}), ensure_ascii=False, indent=2)
        
        return template.replace("{{target_type}}", target_type).replace("{{target_name}}", target_name).replace("{{input_data}}", input_data_str)
    
    def _format_collaboration_data(self, collaboration_data: Dict[str, Any]) -> str:
        """협업 데이터 포맷팅"""
        formatted = []
        
        for agent_name, data in collaboration_data.items():
            if agent_name == "data_quality_agent":
                formatted.append("데이터 품질: " + json.dumps(data.get("quality_metrics", {}), ensure_ascii=False))
            elif agent_name == "supervisor_agent":
                formatted.append("감독자 피드백: " + json.dumps(data.get("supervisor_feedback", {}), ensure_ascii=False))
        
        return "\n".join(formatted) if formatted else ""


# 전역 인스턴스
document_processing_agent = DocumentProcessingAgent()


async def process_document(document_data: Dict[str, Any], target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    """문서 처리 실행"""
    input_data = {
        "task_type": "document_processing",
        "document_data": document_data,
        "target_type": target_type,
        "target_name": target_name
    }
    
    return await document_processing_agent.execute(input_data) 