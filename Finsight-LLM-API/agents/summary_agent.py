import json
import re
import logging
from typing import Dict, Any

from utils.llm_client import generate_response

logger = logging.getLogger(__name__)


async def summarize_report(report_content: str, report_info: Dict[str, str]) -> Dict[str, Any]:
    """증권사 애널리스트 리포트를 요약하는 에이전트

    Args:
        report_content: 리포트 원문
        report_info: 리포트 메타 정보

    Returns:
        요약된 리포트 정보 (summary, key_points 포함)
    """
    prompt = _create_summary_prompt(report_content, report_info)
    llm_response = await generate_response(prompt, agent_type="summary_agent")

    # JSON 파싱
    try:
        parsed_data = _parse_json_response(llm_response)
        return {
            "summary": parsed_data.get("summary", ""),
            "key_points": parsed_data.get("key_points", []),
            "report_info": report_info
        }

    except Exception as e:
        logger.error(f"리포트 요약 처리 중 오류 발생: {str(e)}")
        raise Exception(f"리포트 요약 처리 실패: {str(e)}")


def _create_summary_prompt(report_content: str, report_info: Dict[str, str]) -> str:
    """요약 프롬프트 생성"""
    report_info_str = "\n".join([f"- {key}: {value}" for key, value in report_info.items()])

    return f"""당신은 숙련된 증권 애널리스트입니다. 아래 제공된 증권사 리포트를 분석하여 핵심 내용을 요약해주세요.

## 리포트 정보
{report_info_str}

## 리포트 내용
{report_content}

아래 JSON 형식으로 요약 결과를 작성해주세요:

```json
{{
  "summary": "리포트의 핵심 내용을 200자 이내로 요약",
  "key_points": [
    "핵심 포인트 1",
    "핵심 포인트 2",
    "핵심 포인트 3",
    "핵심 포인트 4",
    "핵심 포인트 5"
  ]
}}
```

중요: 응답은 반드시 한국어로 작성하고, 위에 제시된 JSON 형식을 정확히 따라주세요.
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