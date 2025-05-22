import httpx
import logging
import json
from config import OLLAMA_API_GENERATE_URL, DEFAULT_MODEL, LOGS_PATH, AGENT_MODELS
from pathlib import Path
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# 로그 저장 디렉토리 생성
os.makedirs(LOGS_PATH, exist_ok=True)

async def generate_response(prompt: str, agent_type: str = None, temperature: float = 0.7) -> str:
    """Ollama API를 사용하여 LLM 응답 생성

    Args:
        prompt: 프롬프트 문자열
        agent_type: 에이전트 유형 (summary_agent, analysis_agent, sentiment_agent)
        temperature: 온도 파라미터

    Returns:
        LLM 응답 텍스트
    """

    # 에이전트 유형에 맞는 모델 선택
    if agent_type and agent_type in AGENT_MODELS:
        model = AGENT_MODELS[agent_type]
    else:
        model = DEFAULT_MODEL

    try:
        logger.info(f"LLM API 요청 생성 (에이전트: {agent_type}, 모델: {model}, 온도: {temperature})")

        # 요청 로그 저장
        request_log_path = Path(LOGS_PATH) / f"request_{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(request_log_path, 'w', encoding='utf-8') as f:
            f.write(f"에이전트: {agent_type}\\n")
            f.write(f"모델: {model}\\n")
            f.write(f"온도: {temperature}\\n")
            f.write(f"프롬프트:\\n\\n{prompt}")

        # API 호출
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OLLAMA_API_GENERATE_URL,
                json={
                    "model": model,
                    "prompt": prompt,
                    "temperature": temperature,
                    "stream": False
                },
                timeout=300.0
            )

            if response.status_code == 200:
                result = response.json()
                logger.info("LLM API 응답 수신 완료")

                # 응답 로그 저장
                response_log_path = Path(LOGS_PATH) / f"response_{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(response_log_path, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(result, ensure_ascii=False, indent=2))

                return result.get("response", "")
            else:
                logger.error(f"LLM API 오류: {response.status_code} - {response.text}")
                raise Exception(f"LLM API 오류: {response.status_code} - {response.text}")

    except httpx.TimeoutException as e:
        logger.error(f"LLM API 호출 타임아웃: {str(e)}")
        raise Exception(f"LLM API 호출 타임아웃 (300초 경과): 모델이 응답하지 않습니다. Ollama 서버 상태를 확인하세요.")
    except httpx.ConnectError as e:
        logger.error(f"LLM API 연결 오류: {str(e)}")
        raise Exception(f"LLM API 연결 실패: Ollama 서버가 실행 중인지 확인하세요. ({str(e)})")
    except Exception as e:
        logger.error(f"LLM API 호출 중 오류 발생: {str(e)}", exc_info=True)  # 상세 오류 로깅
        raise Exception(f"LLM API 호출 실패: {str(e)}")

# TO DO: Streaming 응답 처리 함수 구현