"""
이미지 OCR 기능 테스트 - 간단 버전
"""
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.data_agents.securities_report_agent import SecuritiesReportAgent


class TestImageOCR:
    """이미지 OCR 테스트 클래스 - 간단 버전"""
    
    def __init__(self):
        self.securities_agent = SecuritiesReportAgent()
        
        # 테스트 이미지 경로
        self.test_image_dir = "tests/test_images"
        
        # 테스트 이미지 목록 가져오기
        self.test_images = self._get_test_images()
    
    def _get_test_images(self) -> List[str]:
        """테스트 이미지 목록 가져오기"""
        test_images = []
        if os.path.exists(self.test_image_dir):
            for file in os.listdir(self.test_image_dir):
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    image_path = os.path.join(self.test_image_dir, file)
                    test_images.append(image_path)
        
        print(f"발견된 테스트 이미지: {len(test_images)}개")
        for img in test_images:
            print(f"  - {img}")
        
        return test_images
    
    async def test_securities_agent_image(self):
        """증권사 에이전트 이미지 분석 테스트"""
        print("=== 증권사 에이전트 이미지 분석 테스트 ===")
        
        for i, image_path in enumerate(self.test_images):
            print(f"\n이미지 {i+1}: {os.path.basename(image_path)}")
            print("  에이전트 분석 중...")
            
            # 절대 경로로 변환
            abs_image_path = os.path.abspath(image_path)
            input_data = {
                "image_path": abs_image_path,
                "data_type": "image",
                "target_type": "securities_report",
                "target_name": "이미지 분석"
            }
            
            start_time = time.time()
            result = await self.securities_agent.analyze(input_data)
            processing_time = time.time() - start_time
            
            print(f"  분석 성공: {result.get('success', True)}")
            print(f"  총 처리 시간: {processing_time:.3f}초")
            
            print("  분석 결과:")
            if 'analysis_result' in result:
                analysis_text = result['analysis_result']
                
                # JSON 블록 추출 시도
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', analysis_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
                else:
                    # JSON 블록이 없으면 전체 텍스트에서 JSON 찾기
                    json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(0)
                    else:
                        json_text = analysis_text
                
                try:
                    # JSON 파싱 시도
                    parsed_json = json.loads(json_text)
                    print("    추출된 JSON 데이터:")
                    for key, value in parsed_json.items():
                        if key == 'content_text' and len(str(value)) > 100:
                            print(f"      {key}: {str(value)[:100]}...")
                        else:
                            print(f"      {key}: {value}")
                    
                    # JSON 파일로 저장
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"test_results/result_{i+1}_{timestamp}.json"
                    os.makedirs("test_results", exist_ok=True)
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(parsed_json, f, ensure_ascii=False, indent=2)
                    print(f"    JSON 파일 저장: {filename}")
                    
                except json.JSONDecodeError as e:
                    print(f"    JSON 파싱 실패: {e}")
                    print(f"    원본 텍스트: {analysis_text[:500]}...")
                    
                    # 원본 텍스트도 파일로 저장
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"test_results/raw_result_{i+1}_{timestamp}.txt"
                    os.makedirs("test_results", exist_ok=True)
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(analysis_text)
                    print(f"    원본 텍스트 파일 저장: {filename}")
                    
            elif 'error' in result:
                print(f"    오류: {result['error']}")
            else:
                print(f"    결과: {result}")
            
            print()  # 빈 줄 추가
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("이미지 OCR 기능 테스트 시작")
        print(f"테스트 이미지 디렉토리: {self.test_image_dir}")
        print(f"발견된 이미지 수: {len(self.test_images)}")
        print("=" * 50)
        
        await self.test_securities_agent_image()
        
        print("=" * 50)
        print("모든 테스트 완료!")


async def main():
    tester = TestImageOCR()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main()) 