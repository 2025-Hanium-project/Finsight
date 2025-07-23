import re

def extract_json_from_response(response: str) -> str:
    """
    LLM 응답에서 ```json ... ``` 또는 ``` ... ``` 블록, 혹은 { ... } JSON 객체만 추출
    """
    json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    json_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        return json_match.group(0)
    json_match = re.search(r'\[.*\]', response, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return response 