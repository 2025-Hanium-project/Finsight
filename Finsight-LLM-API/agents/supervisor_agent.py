"""
감독자 에이전트 - 다른 에이전트 결과의 품질을 검토하고 관리
"""
from typing import Dict, Any, List
from datetime import datetime

from utils.agent_base import BaseAgent
from utils.logging_config import get_agent_logger
from error_handlers import AgentError


class SupervisorAgent(BaseAgent):
    """감독자 에이전트 - 다른 에이전트 결과의 품질을 검토하고 관리"""
    
    def __init__(self):
        super().__init__("supervisor_agent")
    
    async def review_results(self, agent_results: Dict[str, Any], target_type: str, target_name: str) -> Dict[str, Any]:
        """에이전트 결과 검토 메인 함수"""
        return await review_agent_results(agent_results, target_type, target_name)


async def review_agent_results(agent_results: Dict[str, Any], target_type: str, target_name: str) -> Dict[str, Any]:
    """
    에이전트 결과들을 검토하고 품질을 관리
    - 각 에이전트 결과의 품질을 검토
    - 결과가 부족하면 재분석 필요성 판단
    - 적절한 결과들은 그대로 사용자에게 제공
    """
    logger = get_agent_logger("supervisor_agent")
    start_time = datetime.now()
    
    try:
        logger.log_start("에이전트 결과 검토", extra={
            'target_type': target_type,
            'target_name': target_name,
            'agent_results_count': len(agent_results) if agent_results else 0
        })
        
        # 입력 검증
        if not agent_results:
            raise AgentError(
                agent_name="supervisor_agent",
                message="검토할 에이전트 결과가 없습니다",
                details={"target_type": target_type, "target_name": target_name}
            )
        
        # 각 에이전트 결과 품질 검토
        quality_scores = {}
        needs_regeneration = {}
        
        for agent_name, result in agent_results.items():
            quality_score = _evaluate_result_quality(agent_name, result)
            quality_scores[agent_name] = quality_score
            
            # 품질 점수가 0.7 미만이면 재생성 필요
            if quality_score < 0.7:
                needs_regeneration[agent_name] = {
                    "quality_score": quality_score,
                    "reason": _get_quality_issue_reason(agent_name, result)
                }
        
        # 검토 결과 정리
        review_result = {
            "target_type": target_type,
            "target_name": target_name,
            "agent_results": agent_results,
            "quality_scores": quality_scores,
            "needs_regeneration": needs_regeneration,
            "overall_quality": sum(quality_scores.values()) / len(quality_scores) if quality_scores else 0.0,
            "review_status": "needs_regeneration" if needs_regeneration else "approved",
            "generated_at": datetime.now().isoformat()
        }
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.log_completion("에이전트 결과 검토", processing_time, extra={
            'overall_quality': review_result['overall_quality'],
            'approved_agents': len(quality_scores) - len(needs_regeneration),
            'needs_regeneration_count': len(needs_regeneration)
        })
        
        return review_result
        
    except AgentError:
        # 이미 처리된 에러는 그대로 전파
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.log_error("에이전트 결과 검토", e, extra={
            'processing_time': processing_time,
            'target_type': target_type,
            'target_name': target_name
        })
        
        raise AgentError(
            agent_name="supervisor_agent",
            message=f"에이전트 결과 검토 중 오류 발생: {str(e)}",
            details={"target_type": target_type, "target_name": target_name}
        )


def _evaluate_result_quality(agent_name: str, result: Dict[str, Any]) -> float:
    """에이전트 결과의 품질을 평가 (0.0 ~ 1.0)"""
    
    if not result or not isinstance(result, dict):
        return 0.0
    
    quality_score = 0.0
    
    # 공통 품질 기준
    # 1. 필수 필드 존재 여부 (0.3)
    required_fields = ["target_type", "target_name", "generated_at"]
    field_score = sum(1 for field in required_fields if field in result and result[field]) / len(required_fields)
    quality_score += field_score * 0.3
    
    # 2. 내용 품질 (0.7)
    content_score = 0.0
    
    if agent_name == "sentiment_agent":
        content_score = _evaluate_sentiment_quality(result)
    elif agent_name == "risk_agent":
        content_score = _evaluate_risk_quality(result)
    elif agent_name == "growth_agent":
        content_score = _evaluate_growth_quality(result)
    elif agent_name == "summary_agent":
        content_score = _evaluate_summary_quality(result)
    else:
        content_score = 0.5  # 기본값
    
    quality_score += content_score * 0.7
    
    return min(quality_score, 1.0)


def _evaluate_sentiment_quality(result: Dict[str, Any]) -> float:
    """감성 분석 결과 품질 평가"""
    score = 0.0
    
    # 감성 점수 유효성 (0.3)
    sentiment_score = result.get("sentiment_score", None)
    if sentiment_score is not None and -1.0 <= sentiment_score <= 1.0:
        score += 0.3
    
    # 감성 분류 존재 (0.2)
    if result.get("overall_sentiment") and result.get("overall_sentiment") in ["긍정적", "부정적", "중립적"]:
        score += 0.2
    
    # 긍정/부정 요인 존재 (0.3)
    positive_factors = result.get("positive_factors", [])
    negative_factors = result.get("negative_factors", [])
    if positive_factors and negative_factors and len(positive_factors) >= 2 and len(negative_factors) >= 2:
        score += 0.3
    
    # 트렌드 분석 존재 (0.2)
    trend_analysis = result.get("trend_analysis", {})
    if trend_analysis and trend_analysis.get("trend") and trend_analysis.get("momentum"):
        score += 0.2
    
    return score


def _evaluate_risk_quality(result: Dict[str, Any]) -> float:
    """리스크 분석 결과 품질 평가"""
    score = 0.0
    
    # 리스크 점수 유효성 (0.3)
    risk_score = result.get("risk_score", None)
    if risk_score is not None and 0 <= risk_score <= 100:
        score += 0.3
    
    # 리스크 레벨 존재 (0.2)
    if result.get("risk_level") and result.get("risk_level") in ["high", "medium", "low"]:
        score += 0.2
    
    # 리스크 요인 존재 (0.3)
    risk_factors = result.get("risk_factors", [])
    if risk_factors and len(risk_factors) >= 2:
        score += 0.3
    
    # 완화 전략 존재 (0.2)
    mitigation_strategies = result.get("mitigation_strategies", [])
    if mitigation_strategies and len(mitigation_strategies) >= 2:
        score += 0.2
    
    return score


def _evaluate_growth_quality(result: Dict[str, Any]) -> float:
    """성장성 분석 결과 품질 평가"""
    score = 0.0
    
    # 성장 점수 유효성 (0.3)
    growth_score = result.get("growth_score", None)
    if growth_score is not None and 0 <= growth_score <= 100:
        score += 0.3
    
    # 성장 잠재력 존재 (0.2)
    if result.get("growth_potential") and result.get("growth_potential") in ["high", "medium", "low"]:
        score += 0.2
    
    # 성장 동력 존재 (0.3)
    growth_drivers = result.get("growth_drivers", [])
    if growth_drivers and len(growth_drivers) >= 2:
        score += 0.3
    
    # 투자 기회 존재 (0.2)
    investment_opportunities = result.get("investment_opportunities", [])
    if investment_opportunities and len(investment_opportunities) >= 2:
        score += 0.2
    
    return score


def _evaluate_summary_quality(result: Dict[str, Any]) -> float:
    """요약 결과 품질 평가"""
    score = 0.0
    
    # 요약 내용 존재 (0.4)
    summary = result.get("summary", "")
    if summary and len(summary.strip()) >= 50:  # 최소 50자 이상
        score += 0.4
    
    # 핵심 포인트 존재 (0.4)
    key_points = result.get("key_points", [])
    if key_points and len(key_points) >= 3:
        score += 0.4
    
    # 리포트 정보 존재 (0.2)
    if result.get("report_info"):
        score += 0.2
    
    return score


def _get_quality_issue_reason(agent_name: str, result: Dict[str, Any]) -> str:
    """품질 이슈 원인 파악"""
    issues = []
    
    # 공통 이슈 체크
    if not result.get("target_type"):
        issues.append("대상 타입 누락")
    if not result.get("target_name"):
        issues.append("대상명 누락")
    if not result.get("generated_at"):
        issues.append("생성 시간 누락")
    
    # 에이전트별 이슈 체크
    if agent_name == "sentiment_agent":
        if not result.get("sentiment_score"):
            issues.append("감성 점수 누락")
        if not result.get("positive_factors") or not result.get("negative_factors"):
            issues.append("긍정/부정 요인 부족")
    elif agent_name == "risk_agent":
        if not result.get("risk_score"):
            issues.append("리스크 점수 누락")
        if not result.get("risk_factors"):
            issues.append("리스크 요인 부족")
    elif agent_name == "growth_agent":
        if not result.get("growth_score"):
            issues.append("성장 점수 누락")
        if not result.get("growth_drivers"):
            issues.append("성장 동력 부족")
    elif agent_name == "summary_agent":
        if not result.get("summary"):
            issues.append("요약 내용 누락")
        if not result.get("key_points"):
            issues.append("핵심 포인트 부족")
    
    return "; ".join(issues) if issues else "일반적인 품질 기준 미달"