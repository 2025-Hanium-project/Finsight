from openai import OpenAI
import re
import requests
import json
class Completions:
    def __init__(self, client):
        self.client = client
    def create(self, model, messages, **kwargs):
        # OpenAI chat messages를  Ollama prompt 형 식 으 로  변 환
        prompt = ''
        for msg in messages:
            role = msg['role']
            content = msg['content']
            if role == 'system':
                prompt += f'System: {content}\n'
            elif role == 'user':
                prompt += f'User: {content}\n'
            elif role == 'assistant':
                prompt += f'Assistant: {content}\n'
        data = {
            'model': model,
            'prompt': prompt,
            'stream': False
        }
        response = requests.post(f'{self.client.base_url}/api/generate',
                               headers=self.client.headers, json=data)
        response.raise_for_status()
        res_json = response.json()
        # Ollama 응 답 에 서  텍 스 트  추 출
        text = res_json.get('response', '')
        # OpenAI 응 답  형 태 로  변 환
        class Choice:
            def __init__(self, content):
                self.message = type('obj', (object,), {'content': content})()
        class Response:
            def __init__(self, content):
                self.choices = [Choice(content)]
        return Response(text)
class ChatCompletions:
    def __init__(self, client):
        self.client = client
        self.completions = Completions(client)  # 이  부 분 이  누 락 되 어  있 었 음
# OpenAI 호 환  클 래 스  정 의
class OpenAICompatClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/').replace('/v1', '')  # /v1 제 거
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        # OpenAI API 호 환 을  위 한  chat 객 체
        self.chat = ChatCompletions(self)
# 공 통  설 정
base_url = 'http://shbank.kro.kr:1401/v1'
api_key = 'thisisshinhanbank-2025_AILAB'
# Ollama인 지  OpenAI인 지  확 인 하 여  적 절 한  클 라 이 언 트  생 성
if 'shbank.kro.kr:1401' in base_url or 'private-cloud.kro.kr:1210' in base_url:
    # Ollama 서 버 인  경 우  호 환  클 라 이 언 트  사 용
    client = OpenAICompatClient(base_url, api_key)
else:
    # 실 제  OpenAI API인  경 우  기 존  클 라 이 언 트  사 용
    client = OpenAI(base_url=base_url, api_key=api_key)
# 원 래  질 문  저 장
original_question = "자 산  증 식 을  위 해  포 트 폴 리 오 를  어 떻 게  구 성 하 는  것 이  좋 은 지  설 명 하 라 . 표 형 태 의  출 력 이  선 호 되 며 , 필 요 하 다 면  마 크 다 운  형 태 로  출 력 하 라 ."

# 첫  번 째  모 델 로  초 기  응 답  얻 기
initial_response = client.chat.completions.create(
    model="qwen3:1.7b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": original_question}
    ]
)
initial_content = initial_response.choices[0].message.content
# 두  번 째  모 델 로  응 답  가 공 하 기
prompt_template = f"""
이  답 변 을  자 연 스 러 운  응 답 으 로  정 정 해  주 세 요 .
본 래 의  질 문 은  {original_question}이 였 습 니 다 .
이 를  고 려 하 여  다 음 의  답 변  내 용 을  정 정 하 세 요
답 변 을  받 는  사 용 자 는  한 국 인 이 라 는  점 을  고 려 하 여  최 대 한  한 국 어 를  사 용 하 세 요 .
꺨 진 글 자 나  중 국 어 , 일 본 어  등 을  제 거 하 거 나  치 환 해 야 합 니 다 .
또 한  사 용 자 는  요 구 된  질 문 에  대 한  답 변 만 을  원 하 기  때 문 에  결 과  답 변 과  관 련  없 이  앞 뒤 에  붙 는  말 은  생 략 하 세 요 .
원 본  답 변 :
{initial_content}
"""
final_response = client.chat.completions.create(
    model="exaone-deep:latest",
    messages=[
        {"role": "system", "content": "You are a helpful assistant that refines and improves content."},
        {"role": "user", "content": prompt_template}
    ]
)
# 응 답 에 서  <thought>...</thought> 패 턴  제 거
raw_content = final_response.choices[0].message.content
cleaned_content = re.sub(r'<thought>.*?</thought>', '', raw_content, flags=re.DOTALL)
# 정 제 된  최 종  응 답  출 력
print(cleaned_content.strip())