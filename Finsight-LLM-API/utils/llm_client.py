"""
간소화된 LLM 클라이언트
"""
import httpx
import json
import asyncio
import re
from datetime import datetime
from typing import Optional, Dict, Any, Type, TypeVar
import logging
from pydantic import BaseModel, ValidationError
import google.generativeai as genai

from config import (
    OLLAMA_API_GENERATE_URL, DEFAULT_MODEL, AGENT_MODELS, GEMINI_AGENT_MODELS,
    LLM_TIMEOUT, DEFAULT_TEMPERATURE, MAX_TOKENS, MAX_RETRY_ATTEMPTS, RETRY_DELAY,
    LLM_PROVIDER, GEMINI_API_KEY, DEFAULT_GEMINI_MODEL
)
from error_handlers import LLMError, TimeoutError as CustomTimeoutError, ParsingError, get_security_manager

T = TypeVar('T', bound=BaseModel)

logger = logging.getLogger(__name__)
security_manager = get_security_manager()


class LLMClient:
    """간소화된 LLM 클라이언트"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.gemini_client = None
        
        # Gemini API 초기화
        if LLM_PROVIDER == 'gemini' and GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.gemini_client = genai
    
    async def _get_client(self) -> httpx.AsyncClient:
        """HTTP 클라이언트 인스턴스 생성/반환"""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=LLM_TIMEOUT)
        return self.client
    
    async def generate_response(
        self, 
        prompt: str, 
        agent_type: Optional[str] = None, 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None
    ) -> str:
        """LLM 응답 생성"""
        
        # 입력 검증 및 sanitization
        if not prompt or not prompt.strip():
            raise LLMError("프롬프트가 비어있습니다", llm_model=model)
        
        # LLM 프롬프트는 내부적으로 생성되는 안전한 텍스트이므로 sanitization 건너뛰기
        safe_prompt = prompt.strip()
        
        # 파라미터 설정
        temperature = temperature or DEFAULT_TEMPERATURE
        max_tokens = max_tokens or MAX_TOKENS
        model = model or self._get_model_for_agent(agent_type)
        
        # 요청 로깅
        self.logger.info(f"LLM 요청 시작: {agent_type or 'unknown'} - {model} (Provider: {LLM_PROVIDER})")
        start_time = datetime.now()
        
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                if LLM_PROVIDER == 'gemini':
                    response = await self._make_gemini_request(
                        safe_prompt, model, temperature, max_tokens
                    )
                else:
                    response = await self._make_ollama_request(
                        safe_prompt, model, temperature, max_tokens
                    )
                
                processing_time = (datetime.now() - start_time).total_seconds()
                self.logger.info(f"LLM 응답 완료: {processing_time:.3f}s")
                
                return response
                
            except httpx.TimeoutException as e:
                if attempt == MAX_RETRY_ATTEMPTS - 1:
                    raise CustomTimeoutError(
                        message=f"LLM API 타임아웃 ({LLM_TIMEOUT}초)",
                        timeout_seconds=LLM_TIMEOUT,
                        operation="LLM 요청"
                    )
                
                self.logger.warning(f"재시도 중 ({attempt + 1}/{MAX_RETRY_ATTEMPTS})")
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                
            except httpx.ConnectError as e:
                if attempt == MAX_RETRY_ATTEMPTS - 1:
                    raise LLMError(
                        message="LLM API 연결 실패",
                        llm_model=model,
                        details={"error": f"{LLM_PROVIDER} 서버 확인 필요"}
                    )
                
                self.logger.warning(f"연결 재시도 중 ({attempt + 1}/{MAX_RETRY_ATTEMPTS})")
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                
            except Exception as e:
                if attempt == MAX_RETRY_ATTEMPTS - 1:
                    raise LLMError(
                        message=f"LLM 요청 실패: {str(e)}",
                        llm_model=model
                    )
                
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
        
        raise LLMError("모든 재시도 실패", llm_model=model)
    
    async def _make_ollama_request(
        self, 
        prompt: str, 
        model: str, 
        temperature: float, 
        max_tokens: int
    ) -> str:
        """Ollama API 요청 수행"""
        
        client = await self._get_client()
        
        # JSON 형식 강제 프롬프트
        enhanced_prompt = f"""
{prompt}

**중요 지시사항:**
1. 오직 JSON 형식으로만 응답
2. 모든 텍스트는 한국어로 작성
3. 설명이나 부가 텍스트 없이 JSON만 반환

응답 형식:
{{
  "필드명": "한국어 값",
  "리스트": ["한국어", "항목들"]
}}
"""
        
        payload = {
            "model": model,
            "prompt": enhanced_prompt,
            "temperature": temperature,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "top_p": 0.9,
                "top_k": 40
            }
        }
        
        response = await client.post(OLLAMA_API_GENERATE_URL, json=payload)
        
        if response.status_code != 200:
            raise LLMError(
                message=f"Ollama API 오류: {response.status_code}",
                llm_model=model,
                status_code=response.status_code
            )
        
        result = response.json()
        llm_response = result.get("response", "")
        
        if not llm_response:
            raise LLMError("Ollama 응답이 비어있습니다", llm_model=model)
        
        return llm_response.strip()
    
    async def _make_gemini_request(
        self, 
        prompt: str, 
        model: str, 
        temperature: float, 
        max_tokens: int
    ) -> str:
        """Gemini API 요청 수행"""
        
        if not self.gemini_client:
            raise LLMError("Gemini 클라이언트가 초기화되지 않았습니다", llm_model=model)
        
        # JSON 형식 강제 프롬프트
        enhanced_prompt = f"""
{prompt}

**중요 지시사항:**
1. 오직 JSON 형식으로만 응답
2. 모든 텍스트는 한국어로 작성
3. 설명이나 부가 텍스트 없이 JSON만 반환

응답 형식:
{{
  "필드명": "한국어 값",
  "리스트": ["한국어", "항목들"]
}}
"""
        
        try:
            # Gemini 모델 생성
            gemini_model = self.gemini_client.GenerativeModel(
                model_name=model,
                generation_config={
                    'temperature': temperature,
                    'max_output_tokens': max_tokens,
                    'top_p': 0.9,
                    'top_k': 40
                }
            )
            
            # 응답 생성
            response = await asyncio.to_thread(
                gemini_model.generate_content,
                enhanced_prompt
            )
            
            if not response or not response.text:
                raise LLMError("Gemini 응답이 비어있습니다", llm_model=model)
            
            return response.text.strip()
            
        except Exception as e:
            raise LLMError(
                message=f"Gemini API 오류: {str(e)}",
                llm_model=model,
                details={"error": str(e)}
            )
    
    async def generate_structured_response(
        self,
        prompt: str,
        response_schema: Type[T],
        agent_type: Optional[str] = None,
        temperature: Optional[float] = 0.1,
        max_tokens: Optional[int] = 4096
    ) -> T:
        """구조화된 JSON 응답 생성"""
        
        model = self._get_model_for_agent(agent_type)
        
        self.logger.info(f"구조화된 응답 생성 시작: {agent_type or 'unknown'} - {response_schema.__name__}")
        start_time = datetime.now()
        
        # 스키마 예시 생성
        schema_example = self._create_schema_example(response_schema)
        
        # JSON 형식 강제 프롬프트
        enhanced_prompt = f"""
{prompt}

**응답 규칙 (절대 준수):**
1. 오직 JSON 형식만 응답 (설명, 주석, 마크다운 금지)
2. 아래 정확한 구조 사용:
{schema_example}

**중요사항:**
- 모든 텍스트는 한국어로 작성
- 분석 불가 시 "분석 불가" 또는 빈 배열 [] 사용
- JSON 외 어떤 텍스트도 포함하지 말 것
- 큰따옴표 사용 필수

응답:
"""
        
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                # LLM 응답 생성
                response = await self.generate_response(
                    enhanced_prompt, agent_type, temperature, max_tokens, model
                )
                
                # JSON 파싱 및 스키마 검증
                structured_response = self._parse_and_validate(response, response_schema)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                self.logger.info(f"구조화된 응답 생성 완료: {processing_time:.3f}s")
                
                return structured_response
                
            except Exception as e:
                if attempt == MAX_RETRY_ATTEMPTS - 1:
                    self.logger.error(f"구조화된 응답 생성 실패: {str(e)}")
                    raise
                
                self.logger.warning(f"재시도 중 ({attempt + 1}/{MAX_RETRY_ATTEMPTS}): {str(e)}")
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
        
        raise LLMError(
            message="모든 재시도 실패",
            llm_model=model,
            details={"max_attempts": MAX_RETRY_ATTEMPTS}
        )
    
    def _parse_and_validate(self, response: str, schema_class: Type[T]) -> T:
        """JSON 파싱 및 스키마 검증"""
        
        # 1단계: 응답 정리
        cleaned_response = self._clean_response(response)
        
        # 2단계: 직접 JSON 파싱 시도
        try:
            parsed_data = json.loads(cleaned_response)
            return schema_class(**parsed_data)
        except (json.JSONDecodeError, ValidationError):
            pass
        
        # 3단계: JSON 추출 시도
        json_content = self._extract_json(response)
        if json_content:
            try:
                parsed_data = json.loads(json_content)
                return schema_class(**parsed_data)
            except (json.JSONDecodeError, ValidationError):
                pass
        
        # 4단계: 필드별 추출
        try:
            extracted_data = self._extract_fields(response, schema_class)
            return schema_class(**extracted_data)
        except Exception as e:
            raise ParsingError(
                message=f"JSON 파싱 실패: {str(e)}",
                raw_response=response[:500],
                expected_schema=schema_class.__name__
            )
    
    def _clean_response(self, response: str) -> str:
        """응답 정리"""
        cleaned = response.strip()
        
        # 마크다운 코드 블록 정리
        cleaned = re.sub(r'```(?:json)?\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'```\s*$', '', cleaned)
        
        # JSON 형태로 텍스트 정리
        cleaned = re.sub(r'^[^{]*', '', cleaned)
        cleaned = re.sub(r'[^}]*$', '', cleaned)
        
        return cleaned
    
    def _extract_json(self, response: str) -> Optional[str]:
        """JSON 블록 추출"""
        # JSON 블록 패턴 찾기
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        # 중괄호로 둘러싸인 JSON 찾기
        brace_pattern = r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})'
        match = re.search(brace_pattern, response, re.DOTALL)
        
        if match:
            return match.group(1)
        
        return None
    
    def _extract_fields(self, response: str, schema_class: Type[T]) -> Dict[str, Any]:
        """필드별 추출"""
        extracted_data = {}
        
        # 스키마 필드 정보 가져오기
        schema_fields = schema_class.__fields__
        
        for field_name, field_info in schema_fields.items():
            # 필드 타입에 따른 추출 패턴
            field_type = field_info.type_
            
            if hasattr(field_type, '__origin__') and field_type.__origin__ == list:
                # 리스트 필드
                pattern = rf'"{field_name}"\s*:\s*\[(.*?)\]'
                match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
                if match:
                    try:
                        # 간단한 리스트 파싱
                        list_content = match.group(1)
                        items = re.findall(r'"([^"]*)"', list_content)
                        extracted_data[field_name] = items
                    except:
                        extracted_data[field_name] = []
                else:
                    extracted_data[field_name] = []
            
            elif field_type == str:
                # 문자열 필드
                pattern = rf'"{field_name}"\s*:\s*"([^"]*)"'
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    extracted_data[field_name] = match.group(1)
                else:
                    extracted_data[field_name] = self._get_example_value(field_name)
            
            elif field_type in (int, float):
                # 숫자 필드
                pattern = rf'"{field_name}"\s*:\s*([0-9]+(?:\.[0-9]+)?)'
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    try:
                        value = float(match.group(1))
                        if field_type == int:
                            value = int(value)
                        extracted_data[field_name] = value
                    except:
                        extracted_data[field_name] = 0
                else:
                    extracted_data[field_name] = 0
        
        return extracted_data
    
    def _create_schema_example(self, schema_class: Type[T]) -> str:
        """스키마 예시 생성"""
        example_data = {}
        
        for field_name, field_info in schema_class.__fields__.items():
            example_data[field_name] = self._get_example_value(field_name)
        
        return json.dumps(example_data, ensure_ascii=False, indent=2)
    
    def _get_example_value(self, field_name: str) -> Any:
        """필드별 예시값"""
        
        examples = {
            'summary': '종합 분석 요약',
            'key_points': ['핵심 포인트 1', '핵심 포인트 2'],
            'sentiment_score': 0.7,
            'positive_factors': ['긍정 요인 1', '긍정 요인 2'],
            'negative_factors': ['부정 요인 1', '부정 요인 2'],
            'risk_factors': ['위험 요인 1', '위험 요인 2'],
            'risk_score': 30,
            'growth_drivers': ['성장 동력 1', '성장 동력 2'],
            'growth_score': 75,
            'target_type': 'company',
            'target_name': '분석 대상 회사'
        }
        
        return examples.get(field_name, "분석 결과")
    
    def _get_model_for_agent(self, agent_type: Optional[str]) -> str:
        """에이전트별 모델 선택"""
        if LLM_PROVIDER == 'gemini':
            if agent_type and agent_type in GEMINI_AGENT_MODELS:
                return GEMINI_AGENT_MODELS[agent_type]
            return DEFAULT_GEMINI_MODEL
        else:
            if agent_type and agent_type in AGENT_MODELS:
                return AGENT_MODELS[agent_type]
            return DEFAULT_MODEL
    
    async def close(self):
        """클라이언트 정리"""
        if self.client:
            await self.client.aclose()
            self.client = None


# 글로벌 인스턴스
_llm_client = None


async def get_llm_client() -> LLMClient:
    """LLM 클라이언트 인스턴스 반환"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


async def generate_response(
    prompt: str, 
    agent_type: Optional[str] = None, 
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    model: Optional[str] = None
) -> str:
    """LLM 응답 생성 (편의 함수)"""
    client = await get_llm_client()
    return await client.generate_response(
        prompt=prompt,
        agent_type=agent_type,
        temperature=temperature,
        max_tokens=max_tokens,
        model=model
    )


async def generate_structured_response(
    prompt: str,
    response_schema: Type[T],
    agent_type: Optional[str] = None,
    temperature: Optional[float] = 0.1,
    max_tokens: Optional[int] = 4096
) -> T:
    """구조화된 JSON 응답 생성 (편의 함수)"""
    client = await get_llm_client()
    return await client.generate_structured_response(
        prompt=prompt,
        response_schema=response_schema,
        agent_type=agent_type,
        temperature=temperature,
        max_tokens=max_tokens
    )