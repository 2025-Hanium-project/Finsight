import json
import re
import logging
from typing import Dict, Any, List

from utils.llm_client import generate_response

logger = logging.getLogger(__name__)

async def analyze_sentiment(report_contents: List[Dict[str, Any]], target_type: str, target_name: str) -> Dict[str, Any]:
    """리포트의 감성을 분석하는 에이전트

    Args:
        report_contents: 분석할 리포트 목록
        target_type: 분석 유형 (기업 또는 산업)
        target_name: 분석 대상 (기업명 또는 산업명)

    Returns:
        감성 분석 결과
    """

    prompt = _create_sentiment_prompt(report_contents, target_type, target_name)
    llm_response = await generate_response(prompt, agent_type="sentiment_agent")

    # JSON 파싱
    try:
        parsed_data = _parse_json_response(llm_response)

        return {
            "target_type": target_type,
            "target_name": target_name,
            "overall_sentiment": parsed_data.get("overall_sentiment", ""),
            "sentiment_score": parsed_data.get("sentiment_score", 0.0),
            "positive_factors": parsed_data.get("positive_factors", []),
            "negative_factors": parsed_data.get("negative_factors", []),
            "trend_analysis": parsed_data.get("trend_analysis", {})
        }

    except Exception as e:
        logger.error(f"감성 분석 중 오류 발생: {str(e)}")
        raise Exception(f"감성 분석 실패: {str(e)}")

def _create_sentiment_prompt(report_contents: List[Dict[str, Any]], target_type: str, target_name: str) -> str:
    """감성 분석 프롬프트 생성"""

    # 리포트 내용 포맷팅
    reports_str = ""
    for i, report in enumerate(report_contents):
        reports_str += f"### 리포트 {i+1}\\n"
        for key, value in report.items():
            if key == "content":
                # 내용이 너무 길 경우 잘라내기
                content = value[:1500] + "..." if len(value) > 1500 else value
                reports_str += f"- 내용: {content}\\n"
            else:
                reports_str += f"- {key}: {value}\\n"
        reports_str += "\\n"

    # 분석 대상에 따라 프롬프트 조정
    target_description = "기업" if target_type.lower() == "company" else "산업"

    return f"""당신은 금융 텍스트 감성 분석 전문가입니다. 아래 제공된 리포트 내용을 바탕으로 {target_name}({target_description})에 대한 감성을 분석해주세요.

## 분석 대상
- 유형: {target_description}
- 이름: {target_name}

## 분석할 리포트 내용
{reports_str}

아래 JSON 형식으로 감성 분석 결과를 작성해주세요:

```json
{{
  "overall_sentiment": "전체 감성 상태 (매우 부정적/부정적/중립/긍정적/매우 긍정적)",
  "sentiment_score": -1.0에서 1.0 사이의 감성 점수(소수점 둘째자리까지),
  "positive_factors": [
    "주요 긍정 요인 1",
    "주요 긍정 요인 2",
    "주요 긍정 요인 3"
  ],
  "negative_factors": [
    "주요 부정 요인 1",
    "주요 부정 요인 2",
    "주요 부정 요인 3"
  ],
  "trend_analysis": {{
    "trend": "감성 트렌드 (하락/횡보/상승)",
    "momentum": "트렌드 강도 (약함/중간/강함)",
    "turning_point": true/false (현재 전환점 가능성 여부)
  }}
}}
```

중요: 응답은 반드시 한국어로 작성하고, 위에 제시된 JSON 형식을 정확히 따라주세요.
객관적인 데이터에 기반하여 감성을 분석하고, 핵심 문구나 키워드를 인용하여 근거를 제시해주세요.
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
# TO DO: 감성 분석 알고리즘 개선 및 ReRanker 추가