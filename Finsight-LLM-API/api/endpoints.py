"""
API 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from workflows.consensus_workflow import ConsensusWorkflow
import os

router = APIRouter()

class ConsensusRequest(BaseModel):
    """컨센서스 처리 요청 모델"""
    file_path: str

@router.post("/consensus")
async def process_consensus(request: ConsensusRequest):
    """컨센서스 리포트 처리 API"""
    try:
        # Google API 키 확인
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise HTTPException(status_code=500, detail="Google API Key not configured")
        
        # 워크플로우 실행
        workflow = ConsensusWorkflow(google_api_key)
        
        # 워크플로우 실행 후 최종 결과 수집
        final_result = None
        for chunk in workflow.process(request.file_path):
            final_result = chunk  # 마지막 chunk가 최종 결과
        
        if not final_result:
            raise HTTPException(status_code=500, detail="컨센서스 정보를 추출할 수 없습니다")
        
        # Structured output 결과를 바로 반환
        return {
            "status": "success",
            "data": final_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")