"""
Gemini API 연결 테스트 스크립트
"""
import asyncio
import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_gemini_connection():
    """Gemini API 연결 테스트"""
    logger.info("=== Gemini API 연결 테스트 시작 ===")
    
    # 환경 변수 확인
    api_key = os.getenv('GEMINI_API_KEY')
    model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
    
    if not api_key:
        logger.error("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
        logger.info("Google AI Studio에서 API 키를 발급받아 .env 파일에 설정하세요.")
        return False
    
    try:
        # Gemini API 초기화
        genai.configure(api_key=api_key)
        logger.info(f"✅ Gemini API 초기화 성공 (모델: {model_name})")
        
        # 모델 생성
        model = genai.GenerativeModel(model_name)
        logger.info("✅ Gemini 모델 생성 성공")
        
        # 간단한 테스트 프롬프트
        test_prompt = """
다음 JSON 형식으로 한국어로 응답해주세요:

{
  "test_result": "연결 성공",
  "model_name": "사용된 모델명",
  "status": "정상"
}
"""
        
        # 응답 생성
        response = await asyncio.to_thread(
            model.generate_content,
            test_prompt
        )
        
        if response and response.text:
            logger.info("✅ Gemini API 응답 생성 성공")
            logger.info(f"응답 내용: {response.text[:200]}...")
            return True
        else:
            logger.error("❌ Gemini API 응답이 비어있습니다.")
            return False
            
    except Exception as e:
        logger.error(f"❌ Gemini API 연결 실패: {str(e)}")
        return False


async def test_llm_client():
    """LLM 클라이언트 테스트"""
    logger.info("=== LLM 클라이언트 테스트 시작 ===")
    
    try:
        from utils.llm_client import generate_response
        
        test_prompt = "안녕하세요. 간단한 테스트입니다. '테스트 성공'이라고만 한국어로 응답해주세요."
        
        response = await generate_response(
            prompt=test_prompt,
            agent_type="test_agent",
            temperature=0.1
        )
        
        logger.info("✅ LLM 클라이언트 테스트 성공")
        logger.info(f"응답: {response[:100]}...")
        return True
        
    except Exception as e:
        logger.error(f"❌ LLM 클라이언트 테스트 실패: {str(e)}")
        return False


async def main():
    """메인 실행 함수"""
    logger.info("🚀 Gemini API 테스트 시작")
    
    # LLM 제공자 확인
    llm_provider = os.getenv('LLM_PROVIDER', 'ollama').lower()
    logger.info(f"현재 LLM 제공자: {llm_provider}")
    
    if llm_provider == 'gemini':
        # Gemini API 직접 테스트
        gemini_success = await test_gemini_connection()
        
        if gemini_success:
            # LLM 클라이언트 테스트
            client_success = await test_llm_client()
            
            if client_success:
                logger.info("🎉 모든 테스트 성공!")
                return True
            else:
                logger.error("❌ LLM 클라이언트 테스트 실패")
                return False
        else:
            logger.error("❌ Gemini API 연결 테스트 실패")
            return False
    else:
        logger.info("⚠️  LLM_PROVIDER가 'gemini'로 설정되지 않았습니다.")
        logger.info("Gemini API를 테스트하려면 .env 파일에서 LLM_PROVIDER=gemini로 설정하세요.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 