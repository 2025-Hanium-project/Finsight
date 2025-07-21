"""
LLM 클라이언트 및 응답 생성

기능:
- Google Generative AI 클라이언트
- 응답 생성 및 파싱
- 구조화된 출력 처리
- 에러 처리 및 재시도
"""

import asyncio
import json
import logging
import re
import base64
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

import google.generativeai as genai
from google.generativeai import GenerativeModel
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from config import GEMINI_API_KEY, AGENT_MODELS

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM 클라이언트"""
    
    def __init__(self, api_key: str = None, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name
        self.model = None
        self.logger = logger  # logger 속성 추가
        self.client = None  # client 속성 추가
        self.gemini_client = None  # gemini_client 속성 추가
        self.setup_model()
        
        # 통계
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.average_response_time = 0.0
        
        logger.info(f"LLM 클라이언트 초기화: {model_name}")
    
    def setup_model(self):
        """모델 설정"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = GenerativeModel(self.model_name)
            logger.info(f"모델 설정 완료: {self.model_name}")
        except Exception as e:
            logger.error(f"모델 설정 실패: {str(e)}")
            raise
    
    async def generate_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        retry_count: int = 3
    ) -> str:
        """
        응답 생성
        
        Args:
            prompt: 프롬프트
            temperature: 온도 (0.0-1.0)
            max_tokens: 최대 토큰 수
            retry_count: 재시도 횟수
            
        Returns:
            생성된 응답
        """
        start_time = datetime.now()
        self.total_requests += 1
        
        for attempt in range(retry_count):
            try:
                # 안전 설정
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                }
                
                # 생성 설정
                generation_config = {
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    "top_p": 0.8,
                    "top_k": 40
                }
                
                # 응답 생성
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                
                # 응답 텍스트 추출
                if response.text:
                    execution_time = (datetime.now() - start_time).total_seconds()
                    self.successful_requests += 1
                    
                    if self.total_requests > 0:
                        self.average_response_time = (
                            (self.average_response_time * (self.total_requests - 1) + execution_time) 
                            / self.total_requests
                        )
                    
                    logger.info(f"응답 생성 성공 (시도 {attempt + 1}/{retry_count}): {execution_time:.2f}초")
                    return response.text
                else:
                    raise Exception("빈 응답")
                    
            except Exception as e:
                logger.warning(f"응답 생성 실패 (시도 {attempt + 1}/{retry_count}): {str(e)}")
                if attempt == retry_count - 1:
                    self.failed_requests += 1
                    raise Exception(f"모든 재시도 실패: {str(e)}")
                await asyncio.sleep(1)  # 재시도 전 대기
    
    async def generate_multimodal_response(
        self,
        prompt: str,
        image_path: str = None,
        image_data: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        retry_count: int = 3
    ) -> str:
        """
        멀티모달 응답 생성 (이미지 + 텍스트)
        
        Args:
            prompt: 프롬프트
            image_path: 이미지 파일 경로
            image_data: Base64 인코딩된 이미지 데이터
            temperature: 온도 (0.0-1.0)
            max_tokens: 최대 토큰 수
            retry_count: 재시도 횟수
            
        Returns:
            생성된 응답
        """
        start_time = datetime.now()
        self.total_requests += 1
        
        for attempt in range(retry_count):
            try:
                # 안전 설정
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                }
                
                # 생성 설정
                generation_config = {
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    "top_p": 0.8,
                    "top_k": 40
                }
                
                # 이미지 데이터 준비
                try:
                    if image_path:
                        # 이미지 파일에서 직접 읽기
                        with open(image_path, 'rb') as f:
                            image_bytes = f.read()
                        
                        # MIME 타입 결정
                        if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
                            mime_type = "image/jpeg"
                        elif image_path.lower().endswith('.png'):
                            mime_type = "image/png"
                        else:
                            mime_type = "image/png"  # 기본값
                        
                        image_part = {
                            "mime_type": mime_type,
                            "data": image_bytes
                        }
                    elif image_data:
                        # Base64 디코딩
                        image_bytes = base64.b64decode(image_data)
                        
                        # 기본 dict 형태로 이미지 데이터 생성
                        image_part = {
                            "mime_type": "image/png",
                            "data": image_bytes
                        }
                    else:
                        raise Exception("이미지 경로 또는 이미지 데이터가 제공되지 않았습니다")
                        
                except Exception as e:
                    raise Exception(f"이미지 데이터 처리 실패: {str(e)}")
                
                # 멀티모달 콘텐츠 생성
                content = [
                    prompt,
                    image_part
                ]
                
                # 응답 생성
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    content,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                
                # 응답 텍스트 추출
                if response.text:
                    execution_time = (datetime.now() - start_time).total_seconds()
                    self.successful_requests += 1
                    
                    if self.total_requests > 0:
                        self.average_response_time = (
                            (self.average_response_time * (self.total_requests - 1) + execution_time) 
                            / self.total_requests
                        )
                    
                    logger.info(f"멀티모달 응답 생성 성공 (시도 {attempt + 1}/{retry_count}): {execution_time:.2f}초")
                    return response.text
                else:
                    raise Exception("빈 응답")
                    
            except Exception as e:
                logger.warning(f"멀티모달 응답 생성 실패 (시도 {attempt + 1}/{retry_count}): {str(e)}")
                if attempt == retry_count - 1:
                    self.failed_requests += 1
                    raise Exception(f"모든 재시도 실패: {str(e)}")
                await asyncio.sleep(1)  # 재시도 전 대기
    
    async def generate_structured_response(
        self,
        prompt: str,
        response_schema: Dict[str, Any] = None,
        response_model: Any = None,
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        구조화된 응답 생성
        
        Args:
            prompt: 프롬프트
            response_schema: 응답 스키마 (Dict)
            response_model: 응답 모델 (Pydantic 모델)
            temperature: 온도
            max_tokens: 최대 토큰 수
            
        Returns:
            구조화된 응답
        """
        try:
            # response_model이 제공된 경우 스키마로 변환
            if response_model is not None:
                if hasattr(response_model, '__annotations__'):
                    # Pydantic 모델인 경우
                    schema = {}
                    for field_name, field_type in response_model.__annotations__.items():
                        if field_type == str:
                            schema[field_name] = "문자열"
                        elif field_type == int:
                            schema[field_name] = "정수"
                        elif field_type == float:
                            schema[field_name] = "실수"
                        elif field_type == bool:
                            schema[field_name] = "불린"
                        else:
                            schema[field_name] = "문자열"
                    response_schema = schema
                else:
                    # 일반 클래스인 경우
                    response_schema = response_model
            
            # response_schema가 없으면 기본 스키마 사용
            if response_schema is None:
                response_schema = {
                    "result": "분석 결과",
                    "confidence": "신뢰도 (0-100)"
                }
            
            # JSON 스키마를 포함한 프롬프트 생성
            schema_prompt = f"""
{prompt}

다음 JSON 형식으로 응답해주세요:
{json.dumps(response_schema, ensure_ascii=False, indent=2)}

중요: 반드시 유효한 JSON 형식으로 응답해주세요.
"""
            
            # 응답 생성
            response_text = await self.generate_response(
                prompt=schema_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # JSON 파싱
            try:
                # JSON 블록 추출
                json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
                else:
                    # JSON 블록이 없으면 전체 텍스트에서 JSON 찾기
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(0)
                    else:
                        json_text = response_text
                
                # JSON 파싱
                result = json.loads(json_text)
                
                # response_model이 Pydantic 모델인 경우 변환
                if response_model is not None and hasattr(response_model, '__annotations__'):
                    try:
                        return response_model(**result)
                    except Exception as e:
                        logger.warning(f"Pydantic 모델 변환 실패: {str(e)}")
                        return result
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {str(e)}")
                logger.error(f"응답 텍스트: {response_text}")
                raise Exception(f"유효한 JSON 응답을 찾을 수 없습니다: {str(e)}")
                
        except Exception as e:
            logger.error(f"구조화된 응답 생성 실패: {str(e)}")
            raise
    
    async def generate_agent_response(
        self,
        prompt: str,
        agent_type: str = None,
        agent_name: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        retry_count: int = 3
    ) -> Dict[str, Any]:
        """
        에이전트 응답 생성
        
        Args:
            prompt: 프롬프트
            agent_type: 에이전트 타입
            agent_name: 에이전트 이름 (agent_type과 동일하게 처리)
            temperature: 온도 (0.0-1.0)
            max_tokens: 최대 토큰 수
            retry_count: 재시도 횟수
            
        Returns:
            에이전트 응답
        """
        try:
            # agent_name이 제공되면 agent_type으로 사용
            if agent_name and not agent_type:
                agent_type = agent_name
            
            # 기본 응답 생성
            response_text = await self.generate_response(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                retry_count=retry_count
            )
            
            # 에이전트 응답 형식으로 변환
            result = {
                "agent_type": agent_type,
                "agent_name": agent_name,
                "response": response_text,
                "timestamp": datetime.now().isoformat(),
                "model": self.model_name,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            return result
            
        except Exception as e:
            logger.error(f"에이전트 응답 생성 실패: {str(e)}")
            return {
                "agent_type": agent_type,
                "agent_name": agent_name,
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 반환"""
        success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            "model_name": self.model_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "average_response_time": self.average_response_time
        }
    
    def reset_statistics(self):
        """통계 초기화"""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.average_response_time = 0.0


# 전역 LLM 클라이언트 인스턴스
_llm_client = None

def get_llm_client(model_name: str = "gemini-2.0-flash") -> LLMClient:
    """LLM 클라이언트 인스턴스 반환"""
    global _llm_client
    if _llm_client is None or _llm_client.model_name != model_name:
        _llm_client = LLMClient(model_name=model_name)
    return _llm_client


# 편의 함수들
async def generate_response(
    prompt: str,
    model: str = "gemini-2.0-flash",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    retry_count: int = 3
) -> str:
    """
    응답 생성 (편의 함수)
    
    Args:
        prompt: 프롬프트
        model: 모델 이름
        temperature: 온도
        max_tokens: 최대 토큰 수
        retry_count: 재시도 횟수
        
    Returns:
        생성된 응답
    """
    client = get_llm_client(model)
    return await client.generate_response(
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        retry_count=retry_count
    )


async def generate_multimodal_response(
    prompt: str,
    image_path: str = None,
    image_data: str = None,
    model: str = "gemini-2.5-flash",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    retry_count: int = 3
) -> str:
    """
    멀티모달 응답 생성 (편의 함수)
    
    Args:
        prompt: 프롬프트
        image_path: 이미지 파일 경로
        image_data: Base64 인코딩된 이미지 데이터
        model: 모델 이름
        temperature: 온도
        max_tokens: 최대 토큰 수
        retry_count: 재시도 횟수
        
    Returns:
        생성된 응답
    """
    client = get_llm_client(model)
    return await client.generate_multimodal_response(
        prompt=prompt,
        image_path=image_path,
        image_data=image_data,
        temperature=temperature,
        max_tokens=max_tokens,
        retry_count=retry_count
    )


async def generate_structured_response(
    prompt: str,
    response_schema: Dict[str, Any] = None,
    response_model: Any = None,
    model: str = "gemini-2.0-flash",
    temperature: float = 0.3,
    max_tokens: int = 4096
) -> Dict[str, Any]:
    """
    구조화된 응답 생성 (편의 함수)
    
    Args:
        prompt: 프롬프트
        response_schema: 응답 스키마 (Dict)
        response_model: 응답 모델 (Pydantic 모델)
        model: 모델 이름
        temperature: 온도
        max_tokens: 최대 토큰 수
        
    Returns:
        구조화된 응답
    """
    client = get_llm_client(model)
    return await client.generate_structured_response(
        prompt=prompt,
        response_schema=response_schema,
        response_model=response_model,
        temperature=temperature,
        max_tokens=max_tokens
    )


# 에러 처리 유틸리티
class LLMError(Exception):
    """LLM 관련 에러"""
    pass


class LLMTimeoutError(LLMError):
    """LLM 타임아웃 에러"""
    pass


class LLMRateLimitError(LLMError):
    """LLM 속도 제한 에러"""
    pass


def handle_llm_error(error: Exception) -> str:
    """
    LLM 에러 처리
    
    Args:
        error: 발생한 예외
        
    Returns:
        에러 메시지
    """
    if "timeout" in str(error).lower():
        return "LLM 응답 시간 초과"
    elif "rate limit" in str(error).lower():
        return "LLM 속도 제한 초과"
    elif "quota" in str(error).lower():
        return "LLM 할당량 초과"
    else:
        return f"LLM 에러: {str(error)}"


# 성능 모니터링
class LLMPerformanceMonitor:
    """LLM 성능 모니터링"""
    
    def __init__(self):
        self.requests = []
        self.max_history = 1000
    
    def add_request(self, model: str, prompt_length: int, response_length: int, 
                   execution_time: float, success: bool):
        """요청 정보 추가"""
        request_info = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'prompt_length': prompt_length,
            'response_length': response_length,
            'execution_time': execution_time,
            'success': success
        }
        
        self.requests.append(request_info)
        
        # 최대 히스토리 유지
        if len(self.requests) > self.max_history:
            self.requests.pop(0)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        if not self.requests:
            return {}
        
        successful_requests = [r for r in self.requests if r['success']]
        failed_requests = [r for r in self.requests if not r['success']]
        
        if successful_requests:
            avg_execution_time = sum(r['execution_time'] for r in successful_requests) / len(successful_requests)
            avg_prompt_length = sum(r['prompt_length'] for r in successful_requests) / len(successful_requests)
            avg_response_length = sum(r['response_length'] for r in successful_requests) / len(successful_requests)
        else:
            avg_execution_time = avg_prompt_length = avg_response_length = 0
        
        return {
            'total_requests': len(self.requests),
            'successful_requests': len(successful_requests),
            'failed_requests': len(failed_requests),
            'success_rate': len(successful_requests) / len(self.requests) * 100 if self.requests else 0,
            'avg_execution_time': avg_execution_time,
            'avg_prompt_length': avg_prompt_length,
            'avg_response_length': avg_response_length,
            'recent_requests': self.requests[-10:] if self.requests else []
        }


# 전역 성능 모니터
_llm_performance_monitor = LLMPerformanceMonitor()

def get_llm_performance_monitor() -> LLMPerformanceMonitor:
    """LLM 성능 모니터 인스턴스 반환"""
    return _llm_performance_monitor 