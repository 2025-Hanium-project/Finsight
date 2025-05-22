
import json
import re
import logging
from typing import Dict, Any, List

from utils.llm_client import generate_response

logger = logging.getLogger(__name__)

async def analyze_reports(summaries: List[Dict[str, Any]], target_type: str, target_name: str) -> Dict[str, Any]:
    """요약된 리포트들을 통합 분석하는 에이전트

    Args:
        summaries: 요약된 리포트 목록
        target_type: 분석 유형 (기업 또는 산업)
        target_name: 분석 대상 (기업명 또는 산업명)

    Returns:
        통합 분석 결과
    """

    prompt = _create_analysis_prompt(summaries, target_type, target_name)
    llm_response = await generate_response(prompt, agent_type="analysis_agent")

    # JSON 파싱
    try:
        parsed_data = _parse_json_response(llm_response)

        return {
            "target_type": target_type,
            "target_name": target_name,
            "analysis_summary": parsed_data.get("analysis_summary", ""),
            "investment_points": parsed_data.get("investment_points", []),
            "risk_factors": parsed_data.get("risk_factors", []),
            "consensus": parsed_data.get("consensus")
        }

    except Exception as e:
        logger.error(f"리포트 통합 분석 중 오류 발생: {str(e)}")
        raise Exception(f"리포트 통합 분석 실패: {str(e)}")

def _create_analysis_prompt(summaries: List[Dict[str, Any]], target_type: str, target_name: str) -> str:
    """분석 프롬프트 생성"""

    # 요약된 리포트 내용 포맷팅
    summaries_str = ""
    for i, summary in enumerate(summaries):
        report_info = summary.get("report_info", {})
        summaries_str += f"### 리포트 {i+1}\\n"
        summaries_str += f"- 제목: {report_info.get('title', 'N/A')}\\n"
        summaries_str += f"- 날짜: {report_info.get('date', 'N/A')}\\n"
        summaries_str += f"- 증권사: {report_info.get('company', 'N/A')}\\n"
        summaries_str += f"- 요약: {summary.get('summary', 'N/A')}\\n"
        summaries_str += "- 핵심 포인트:\\n"
        for point in summary.get("key_points", []):
            summaries_str += f"  * {point}\\n"
        summaries_str += "\\n"

    # 분석 대상에 따라 프롬프트 조정
    target_description = "기업" if target_type.lower() == "company" else "산업"

    return f"""당신은 숙련된 증권 애널리스트입니다. 아래 제공된 여러 리포트 요약을 분석하여 {target_name}({target_description})에 대한 통합 분석 보고서를 작성해주세요.

## 분석 대상
- 유형: {target_description}
- 이름: {target_name}

## 요약된 리포트 목록
{summaries_str}

아래 JSON 형식으로 통합 분석 결과를 작성해주세요:

```json
{{
  "analysis_summary": "{target_name}에 대한 종합적인 분석 (300자 이내)",
  "investment_points": [
    "투자 포인트 1",
    "투자 포인트 2",
    "투자 포인트 3"
  ],
  "risk_factors": [
    "리스크 요인 1",
    "리스크 요인 2",
    "리스크 요인 3"
  ],
  "consensus": {{
    "opinion": "종합 투자의견 (매수/중립/매도)",
    "target_price": "목표가 범위 또는 평균",
    "confidence": "컨센서스 확신도 (높음/중간/낮음)"
  }}
}}
```

중요: 응답은 반드시 한국어로 작성하고, 위에 제시된 JSON 형식을 정확히 따라주세요. 
투자 포인트와 리스크 요인은 반드시 3개 이상 제공해주세요. 
컨센서스 정보는 필수로 포함해야 합니다. 
여러 리포트의 내용을 종합적으로 비교 분석하여 객관적인 통합 견해를 제시해주세요. 
"""

def _parse_json_response(response: str) -> Dict[str, Any]:
    """LLM 응답에서 JSON 형식 추출 및 파싱"""
    
    # JSON 코드 블록 추출
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
    if json_match:
        json_str = json_match.group(1)
    else:
        # JSON 블록이 없으면 전체 응답에서 JSON 형식 찾기
        json_match = re.search(r'{[\s\S]*}', response)
        if json_match:
            json_str = json_match.group(0)
        else:
            raise Exception("응답에서 JSON 형식을 찾을 수 없습니다.")
    
    # JSON 파싱
    return json.loads(json_str)

# TO DO: Function Calling 구현으로 포맷 처리 개선
# TO DO: RAG 구현으로 추가 정보 검색 기능 추가