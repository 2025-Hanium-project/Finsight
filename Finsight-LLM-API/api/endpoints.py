"""
API 엔드포인트
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from workflows.consensus_workflow import ConsensusWorkflow
import os
from typing import Literal, Optional
from datetime import datetime

router = APIRouter()

class WorkflowRequest(BaseModel):
    """워크플로우 처리 요청 모델"""
    request_type: Literal["consensus", "report", "review"] = Field(
        ..., 
        description="워크플로우 타입: consensus, report, review 중 하나"
    )
    
    # consensus용 필드
    file_path: Optional[str] = Field(None, description="PDF 파일 경로 (consensus 타입에서 필수)")
    
    # report, review용 필드
    stock_code: Optional[str] = Field(None, description="종목코드 (report, review 타입에서 필수)")
    base_date: Optional[str] = Field(None, description="기준 날짜 YYYY-MM-DD (report, review 타입에서 필수)")
    
    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v, info):
        """consensus 타입일 때 file_path 필수 검증"""
        request_type = info.data.get('request_type')
        if request_type == 'consensus':
            if not v:
                raise ValueError('consensus 타입에서는 file_path가 필수입니다')
        elif request_type in ['report', 'review']:
            if v is not None:
                raise ValueError('report, review 타입에서는 file_path를 사용할 수 없습니다')
        return v
    
    @field_validator('stock_code')
    @classmethod
    def validate_stock_code(cls, v, info):
        """report, review 타입일 때 stock_code 필수 검증"""
        request_type = info.data.get('request_type')
        if request_type in ['report', 'review']:
            if not v:
                raise ValueError('report, review 타입에서는 stock_code가 필수입니다')
        elif request_type == 'consensus':
            if v is not None:
                raise ValueError('consensus 타입에서는 stock_code를 사용할 수 없습니다')
        return v
    
    @field_validator('base_date')
    @classmethod
    def validate_base_date(cls, v, info):
        """report, review 타입일 때 base_date 필수 검증 및 형식 확인"""
        request_type = info.data.get('request_type')
        if request_type in ['report', 'review']:
            if not v:
                raise ValueError('report, review 타입에서는 base_date가 필수입니다')
            # 날짜 형식 검증 (YYYY-MM-DD)
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('base_date는 YYYY-MM-DD 형식이어야 합니다')
        elif request_type == 'consensus':
            if v is not None:
                raise ValueError('consensus 타입에서는 base_date를 사용할 수 없습니다')
        return v

@router.post("/workflow")
async def process_workflow(request: WorkflowRequest):
    """워크플로우 처리 API (consensus, report, review)"""
    try:
        # Google API 키 확인
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise HTTPException(status_code=500, detail="Google API Key not configured")
        
        # 워크플로우 실행
        workflow = ConsensusWorkflow(google_api_key, request.request_type)
        
        # request_type에 따른 처리 분기
        if request.request_type == "consensus":
            # 파일 존재 확인
            if not os.path.exists(request.file_path):
                raise HTTPException(status_code=400, detail=f"파일을 찾을 수 없습니다: {request.file_path}")
            
            # 워크플로우 실행
            result = workflow.run({"file_path": request.file_path})
            return {"message": "처리 완료", "result": result}
            
        elif request.request_type in ["report", "review"]:
            # report, review 타입 처리 (미래 구현)
            return {"message": f"{request.request_type} 타입은 아직 구현되지 않았습니다"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"처리 중 오류 발생: {str(e)}")