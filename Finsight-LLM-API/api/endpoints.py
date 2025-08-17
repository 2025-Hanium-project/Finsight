"""
API 엔드포인트 - 최종 응답 형식 개선
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from workflows.consensus_workflow import ConsensusWorkflow
from workflows.report_workflow import ReportWorkflow
from typing import Literal, Optional
from datetime import datetime

router = APIRouter()

class WorkflowRequest(BaseModel):
    request_type: Literal["consensus", "report", "review"] = Field(
        ..., 
        description="워크플로우 타입"
    )
    file_path: Optional[str] = Field(
        None, 
        description="처리할 파일 경로 (consensus 타입에서 필수)"
    )
    stock_code: Optional[str] = Field(
        None,
        description="종목코드 (report, review 타입에서 필수)"
    )
    
    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v, info):
        request_type = info.data.get('request_type')
        if request_type == 'consensus':
            if not v:
                raise ValueError('consensus 타입에서는 file_path가 필수입니다')
            if not os.path.exists(v):
                raise ValueError(f'파일을 찾을 수 없습니다: {v}')
        return v
    
    @field_validator('stock_code')
    @classmethod
    def validate_stock_code(cls, v, info):
        request_type = info.data.get('request_type')
        if request_type in ['report', 'review']:
            if not v:
                raise ValueError(f'{request_type} 타입에서는 stock_code가 필수입니다')
        return v

@router.get("/", summary="API 상태 확인")
async def health_check():
    return {
        "status": "healthy",
        "message": "Finsight LLM API가 정상 작동 중입니다",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/workflow", summary="워크플로우 실행", description="다양한 워크플로우를 실행합니다")
async def run_workflow(request: WorkflowRequest):
    try:
        google_api_key = os.getenv("GOOGLE_API_KEY")
        
        if request.request_type == "consensus":
            # Consensus 워크플로우 - JSON 형식으로 응답
            print(f"🚀 Consensus 워크플로우 시작: {request.file_path}")
            
            consensus_workflow = ConsensusWorkflow(
                google_api_key=google_api_key,
                request_type="consensus"
            )
            result = consensus_workflow.run({
                "file_path": request.file_path
            })
            
            # Consensus는 파싱된 JSON만 반환
            return result
            
        elif request.request_type == "report":
            # Report 워크플로우 - 리포트 텍스트 그대로 응답
            print(f"🚀 Report 워크플로우 시작: {request.stock_code}")
            
            report_workflow = ReportWorkflow(
                google_api_key=google_api_key,
                request_type="report"
            )
            result = report_workflow.run({
                "stock_code": request.stock_code
            })
            
            # Report는 최종 보고서 텍스트만 반환 (메시지 히스토리 제외)
            return result
            
        else:
            return {"error": f"지원하지 않는 워크플로우 타입: {request.request_type}"}
            
    except Exception as e:
        print(f"❌ 워크플로우 실행 오류: {str(e)}")
        return {"error": f"워크플로우 실행 중 오류 발생: {str(e)}"}