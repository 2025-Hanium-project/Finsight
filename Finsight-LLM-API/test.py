"""
AI 기반 증시 투자 분석 시스템 API 테스트 스크립트
"""
import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List
import httpx
from pydantic import ValidationError

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# LLM 제공자 확인
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'ollama').lower()
logger.info(f"현재 LLM 제공자: {LLM_PROVIDER}")

class APITester:
    """API 테스트 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        # LLM 요청은 시간이 오래 걸릴 수 있으므로 긴 타임아웃 설정
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(320.0, connect=10.0))
        
    async def test_health_check(self) -> Dict[str, Any]:
        """기본 헬스체크 테스트"""
        logger.info("=== 헬스체크 테스트 시작 ===")
        
        try:
            response = await self.client.get(f"{self.base_url}/")
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ 헬스체크 성공: {data['status']}")
            return {"status": "success", "data": data}
            
        except Exception as e:
            logger.error(f"❌ 헬스체크 실패: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def test_report_summary(self) -> Dict[str, Any]:
        """리포트 요약 테스트"""
        logger.info("=== 리포트 요약 테스트 시작 ===")
        
        test_data = {
            "target_type": "company",
            "target_name": "삼성전자",
            "symbol": "005930",
            "reports": [
                {
                    "content": "삼성전자는 2024년 4분기 실적 발표에서 메모리 사업 회복과 AI 칩 수요 증가로 매출이 증가할 것으로 전망됩니다. 특히 HBM 메모리 매출이 크게 증가하며, 반도체 사업 부문의 수익성 개선이 예상됩니다. 투자의견은 매수를 유지하며 목표주가는 90,000원으로 상향 조정합니다.",
                    "info": {
                        "company": "삼성전자",
                        "title": "2024년 4분기 실적 전망",
                        "date": "2024-01-15",
                        "analyst": "홍길동",
                        "firm": "테스트증권"
                    }
                }
            ]
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/report/summary",
                json=test_data
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ 리포트 요약 성공: {data['result']['summary'][:50]}...")
            return {"status": "success", "data": data}
            
        except Exception as e:
            logger.error(f"❌ 리포트 요약 실패: {str(e)}")
            if hasattr(e, 'response') and e.response:
                try:
                    error_detail = e.response.json()
                    logger.error(f"상세 에러: {error_detail}")
                except:
                    logger.error(f"응답 상태: {e.response.status_code}")
            return {"status": "error", "error": str(e)}
    
    async def test_sentiment_analysis(self) -> Dict[str, Any]:
        """감성 분석 테스트"""
        logger.info("=== 감성 분석 테스트 시작 ===")
        
        test_data = {
            "target_type": "company",
            "target_name": "삼성전자",
            "symbol": "005930",
            "reports": [
                {
                    "content": "삼성전자의 AI 칩 사업이 크게 성장하고 있으며, 매출 증가가 예상됩니다."
                },
                {
                    "content": "메모리 시장 회복과 함께 수익성 개선이 기대됩니다."
                },
                {
                    "content": "다만 중국 시장의 불확실성과 경쟁 심화는 리스크 요인입니다."
                }
            ]
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/report/sentiment",
                json=test_data
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ 감성 분석 성공: {data['result']['overall_sentiment']} (점수: {data['result']['sentiment_score']})")
            return {"status": "success", "data": data}
            
        except Exception as e:
            logger.error(f"❌ 감성 분석 실패: {str(e)}")
            if hasattr(e, 'response') and e.response:
                try:
                    error_detail = e.response.json()
                    logger.error(f"상세 에러: {error_detail}")
                except:
                    logger.error(f"응답 상태: {e.response.status_code}")
            return {"status": "error", "error": str(e)}
    
    async def test_risk_analysis(self) -> Dict[str, Any]:
        """리스크 분석 테스트"""
        logger.info("=== 리스크 분석 테스트 시작 ===")
        
        test_data = {
            "target_type": "company",
            "target_name": "삼성전자",
            "symbol": "005930",
            "reports": [
                {
                    "content": "반도체 업계는 중국 시장 의존도가 높아 지정학적 리스크가 존재합니다."
                },
                {
                    "content": "메모리 가격 변동성과 경쟁사 대비 기술 격차 확대 위험이 있습니다."
                },
                {
                    "content": "환율 변동과 원자재 가격 상승도 주요 리스크 요인입니다."
                }
            ]
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/report/risk",
                json=test_data
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ 리스크 분석 성공: 리스크 점수 {data['result']['risk_score']}, 레벨 {data['result']['risk_level']}")
            return {"status": "success", "data": data}
            
        except Exception as e:
            logger.error(f"❌ 리스크 분석 실패: {str(e)}")
            if hasattr(e, 'response') and e.response:
                try:
                    error_detail = e.response.json()
                    logger.error(f"상세 에러: {error_detail}")
                except:
                    logger.error(f"응답 상태: {e.response.status_code}")
            return {"status": "error", "error": str(e)}
    
    async def test_growth_analysis(self) -> Dict[str, Any]:
        """성장성 분석 테스트"""
        logger.info("=== 성장성 분석 테스트 시작 ===")
        
        test_data = {
            "target_type": "company",
            "target_name": "삼성전자",
            "symbol": "005930",
            "reports": [
                {
                    "content": "AI 칩 시장 성장과 함께 HBM 메모리 수요가 급증하고 있습니다."
                },
                {
                    "content": "파운드리 사업 확대와 시스템 반도체 부문 성장이 기대됩니다."
                },
                {
                    "content": "차세대 메모리 기술 개발로 경쟁우위 확보가 가능합니다."
                }
            ]
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/report/growth",
                json=test_data
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ 성장성 분석 성공: 성장 점수 {data['result']['growth_score']}, 잠재력 {data['result']['growth_potential']}")
            return {"status": "success", "data": data}
            
        except Exception as e:
            logger.error(f"❌ 성장성 분석 실패: {str(e)}")
            if hasattr(e, 'response') and e.response:
                try:
                    error_detail = e.response.json()
                    logger.error(f"상세 에러: {error_detail}")
                except:
                    logger.error(f"응답 상태: {e.response.status_code}")
            return {"status": "error", "error": str(e)}
    
    async def test_supervisor_review(self) -> Dict[str, Any]:
        """품질 검토 테스트"""
        logger.info("=== 품질 검토 테스트 시작 ===")
        
        test_data = {
            "target_type": "company",
            "target_name": "삼성전자",
            "symbol": "005930",
            "context": {
                "agent_results": {
                    "sentiment": {
                        "overall_sentiment": "긍정적",
                        "sentiment_score": 0.7,
                        "positive_factors": ["AI 칩 성장", "메모리 회복"],
                        "negative_factors": ["중국 리스크"]
                    },
                    "risk": {
                        "risk_score": 35,
                        "risk_level": "medium",
                        "risk_factors": ["지정학적 리스크", "가격 변동성"]
                    },
                    "growth": {
                        "growth_score": 75,
                        "growth_potential": "high",
                        "growth_drivers": ["AI 칩", "HBM 메모리"]
                    }
                }
            }
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/report/supervisor/review",
                json=test_data
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ 품질 검토 성공: 종합 점수 {data['result'].get('overall_score', 'N/A')}")
            return {"status": "success", "data": data}
            
        except Exception as e:
            logger.error(f"❌ 품질 검토 실패: {str(e)}")
            if hasattr(e, 'response') and e.response:
                try:
                    error_detail = e.response.json()
                    logger.error(f"상세 에러: {error_detail}")
                except:
                    logger.error(f"응답 상태: {e.response.status_code}")
            return {"status": "error", "error": str(e)}
    
    async def test_d_day_analysis(self) -> Dict[str, Any]:
        """D-day 분석 테스트"""
        logger.info("=== D-day 분석 테스트 시작 ===")
        
        test_data = {
            "target_type": "company",
            "target_name": "삼성전자",
            "symbol": "005930",
            "reports": [
                {
                    "content": "삼성전자 2024년 4분기 실적 발표 전망",
                    "info": {"date": "2024-01-15", "analyst": "홍길동"}
                }
            ],
            "context": {
                "agent_results": {
                    "summary": {
                        "summary": "삼성전자 실적 전망 긍정적",
                        "key_points": ["메모리 회복", "AI 칩 수요 증가"]
                    },
                    "sentiment": {
                        "overall_sentiment": "긍정적",
                        "sentiment_score": 0.7
                    },
                    "risk": {
                        "risk_score": 35,
                        "risk_level": "medium"
                    },
                    "growth": {
                        "growth_score": 75,
                        "growth_potential": "high"
                    }
                }
            }
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/v1/report/analysis/d-day",
                json=test_data
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ D-day 분석 성공")
            return {"status": "success", "data": data}
            
        except Exception as e:
            logger.error(f"❌ D-day 분석 실패: {str(e)}")
            if hasattr(e, 'response') and e.response:
                try:
                    error_detail = e.response.json()
                    logger.error(f"상세 에러: {error_detail}")
                except:
                    logger.error(f"응답 상태: {e.response.status_code}")
            return {"status": "error", "error": str(e)}
    
    async def test_security_status(self) -> Dict[str, Any]:
        """보안 상태 확인 테스트"""
        logger.info("=== 보안 상태 확인 테스트 시작 ===")
        
        try:
            response = await self.client.get(f"{self.base_url}/security/status")
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ 보안 상태 확인 성공: {data['status']}")
            return {"status": "success", "data": data}
            
        except Exception as e:
            logger.error(f"❌ 보안 상태 확인 실패: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        logger.info("🚀 전체 테스트 시작")
        
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "llm_provider": LLM_PROVIDER,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "results": {}
        }
        
        tests = [
            ("health_check", self.test_health_check),
            ("security_status", self.test_security_status),
            ("report_summary", self.test_report_summary),
            ("sentiment_analysis", self.test_sentiment_analysis),
            ("risk_analysis", self.test_risk_analysis),
            ("growth_analysis", self.test_growth_analysis),
            ("supervisor_review", self.test_supervisor_review),
            ("d_day_analysis", self.test_d_day_analysis),
        ]
        
        for test_name, test_func in tests:
            test_results["total_tests"] += 1
            
            try:
                result = await test_func()
                test_results["results"][test_name] = result
                
                if result["status"] == "success":
                    test_results["passed_tests"] += 1
                else:
                    test_results["failed_tests"] += 1
                    
            except Exception as e:
                test_results["failed_tests"] += 1
                test_results["results"][test_name] = {
                    "status": "error",
                    "error": str(e)
                }
                logger.error(f"❌ {test_name} 테스트 예외 발생: {str(e)}")
        
        # 결과 요약
        success_rate = (test_results["passed_tests"] / test_results["total_tests"]) * 100
        logger.info(f"\n📊 테스트 결과 요약 (LLM 제공자: {LLM_PROVIDER}):")
        logger.info(f"   총 테스트: {test_results['total_tests']}")
        logger.info(f"   성공: {test_results['passed_tests']}")
        logger.info(f"   실패: {test_results['failed_tests']}")
        logger.info(f"   성공률: {success_rate:.1f}%")
        
        if success_rate >= 80:
            logger.info("🎉 테스트 전체 성공!")
        elif success_rate >= 60:
            logger.info("⚠️  일부 테스트 실패")
        else:
            logger.info("❌ 다수 테스트 실패")
        
        return test_results
    
    async def close(self):
        """클라이언트 정리"""
        await self.client.aclose()

async def main():
    """메인 실행 함수"""
    logger.info("AI 기반 증시 투자 분석 시스템 API 테스트 시작")
    
    tester = APITester()
    
    try:
        results = await tester.run_all_tests()
        
        # 결과를 JSON 파일로 저장
        with open("test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info("📄 테스트 결과가 test_results.json 파일에 저장되었습니다.")
        
        # 실패한 테스트가 있으면 비정상 종료
        if results["failed_tests"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"💥 테스트 실행 중 오류 발생: {str(e)}")
        sys.exit(1)
        
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(main()) 