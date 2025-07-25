"""
증권사 리포트 분석 에이전트 (이미지 OCR 지원)
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from utils.core.agent_base import AnalysisAgent, AgentType, create_standard_prompt_template
from utils.llm.llm_client import generate_multimodal_response
from utils.image_utils.image_processor import ImageProcessor, ImageProcessingResult
from utils.image_utils.ocr import SecuritiesReportOCR, OCRResult
from utils.image_utils.batch_processor import BatchImageProcessor

logger = logging.getLogger(__name__)

class SecuritiesReportAgent(AnalysisAgent):
    """증권사 리포트 분석 에이전트 (이미지 OCR 지원)"""
    def __init__(self):
        from utils.core.agent_base import AgentConfig
        config = AgentConfig(
            name="securities_report_agent",
            agent_type=AgentType.SECURITIES_REPORT
        )
        AnalysisAgent.__init__(self, config)
        self.temperature = 0.4  # 리포트 분석을 위한 중간 temperature
        self.ocr_processor = SecuritiesReportOCR()
        self.image_processor = ImageProcessor()
        self.batch_processor = BatchImageProcessor()

    def _get_collaboration_targets(self) -> List[str]:
        return [
            "financial_statement_agent",
            "market_data_agent",
            "valuation_agent",
            "peer_comparison_agent",
            "data_quality_agent",
            "document_processing_agent"
        ]

    def _create_image_analysis_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any] = None) -> str:
        collaboration_info = ""
        if collaboration_data:
            collaboration_info = self._format_collaboration_data(collaboration_data)
        output_schema = {
            "report_id": "자동 생성되는 고유 ID (형식: REP_YYYYMMDD_HHMMSS)",
            "stock_code": "종목 코드 (예: 005930)",
            "stock_name": "종목명 (예: 삼성전자)",
            "report_title": "리포트 제목",
            "report_date": "리포트 발행일 (YYYY-MM-DD 형식)",
            "report_type": "리포트 유형 (기업 분석, 산업 분석, 섹터 분석, 시장 전망 등)",
            "analyst_name": "분석가명",
            "company_name": "증권사명",
            "rating": "투자 의견 (매수, 중립, 매도 등)",
            "opinion_change": "의견 변경 여부 (상향, 하향, 유지)",
            "target_price": "목표 주가 (숫자만)",
            "current_price": "현재 주가 (숫자만)",
            "upside_potential": "상승 여력 (퍼센트, 숫자만)",
            "content_text": "리포트 전문 텍스트",
            "summary": "핵심 요약 (3-5문장)",
            "created_at": "처리 시각 (자동 생성)"
        }
        template = create_standard_prompt_template(
            agent_name="증권사 리포트 이미지 분석 전문가",
            task_description="제공된 증권사 리포트 이미지를 직접 분석하여 구조화된 JSON 데이터를 추출합니다.",
            output_schema=output_schema,
            collaboration_info=collaboration_info
        )
        target_type = input_data.get("target_type", "")
        target_name = input_data.get("target_name", "")
        image_analysis_guidance = """
        
이미지 분석 지침:
1. 이미지에서 모든 텍스트를 정확히 읽어서 추출하세요
2. 종목코드, 종목명, 리포트 제목, 분석가명, 증권사명을 정확히 식별하세요
3. 투자의견, 목표가, 현재가를 숫자로 추출하세요 (원화 기호, 쉼표 제거)
4. 날짜는 YYYY-MM-DD 형식으로 통일하세요
5. 없는 정보는 null로 표시하세요
6. JSON 형식으로만 응답하세요
7. 한글 텍스트는 그대로 유지하세요
8. 이미지에서 보이는 모든 정보를 최대한 활용하세요
9. report_id는 자동으로 생성하세요 (형식: REP_YYYYMMDD_HHMMSS)
10. created_at은 현재 시각으로 설정하세요
11. content_text에는 이미지의 모든 텍스트를 포함하세요
12. summary는 핵심 내용을 3-5문장으로 요약하세요

중요: 이미지의 모든 텍스트를 정확히 읽어서 분석하고, 요청된 JSON 형식으로만 응답하세요.
"""
        template = template.replace("{{target_type}}", target_type)
        template = template.replace("{{target_name}}", target_name)
        template = template.replace("{{input_data}}", image_analysis_guidance)
        return template

    def _format_collaboration_data(self, collaboration_data: Dict[str, Any]) -> str:
        formatted = []
        for agent_name, data in collaboration_data.items():
            if agent_name == "financial_statement_agent":
                formatted.append("재무제표 분석: " + json.dumps(data.get("financial_analysis", {}), ensure_ascii=False))
            elif agent_name == "market_data_agent":
                formatted.append("시장 데이터: " + json.dumps(data.get("market_indicators", {}), ensure_ascii=False))
            elif agent_name == "valuation_agent":
                formatted.append("밸류에이션: " + json.dumps(data.get("valuation_metrics", {}), ensure_ascii=False))
            elif agent_name == "peer_comparison_agent":
                formatted.append("동종업계 비교: " + json.dumps(data.get("peer_analysis", {}), ensure_ascii=False))
            elif agent_name == "data_quality_agent":
                formatted.append("데이터 품질 검증: " + json.dumps(data.get("quality_metrics", {}), ensure_ascii=False))
            elif agent_name == "document_processing_agent":
                formatted.append("문서 처리 결과: " + json.dumps(data.get("processing_result", {}), ensure_ascii=False))
        return "\n".join(formatted) if formatted else ""

    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any] = None) -> str:
        return self._create_image_analysis_prompt(input_data, collaboration_data)

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._execute_analysis(input_data)

    async def _execute_analysis(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            start_time = datetime.now()
            image_path = input_data.get("image_path")
            self.logger.info(f"이미지 경로 확인: {image_path}")
            self.logger.info(f"파일 존재 여부: {os.path.exists(image_path) if image_path else False}")
            if not image_path:
                return {
                    "error": "이미지 경로가 제공되지 않았습니다",
                    "agent_name": self.name,
                    "status": "failed",
                    "timestamp": datetime.now().isoformat()
                }
            if not os.path.exists(image_path):
                return {
                    "error": f"이미지 파일을 찾을 수 없습니다: {image_path}",
                    "agent_name": self.name,
                    "status": "failed",
                    "timestamp": datetime.now().isoformat()
                }
            analysis_input = {
                "data_source": "securities_report_image",
                "image_path": image_path,
                "target_type": input_data.get("target_type", ""),
                "target_name": input_data.get("target_name", ""),
                "data_type": "image"
            }
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            import base64
            image_data = base64.b64encode(image_bytes).decode('utf-8')
            prompt = self._create_image_analysis_prompt(input_data, collaboration_data)
            response = await generate_multimodal_response(
                prompt=prompt,
                image_data=image_data,
                model="gemini-2.0-flash-exp",
                temperature=0.1,
                max_tokens=4096
            )
            json_text = self._extract_json_from_response(response)
            try:
                parsed_data = json.loads(json_text)
                parsed_data["created_at"] = datetime.now().isoformat()
                if "report_id" not in parsed_data or not parsed_data["report_id"]:
                    parsed_data["report_id"] = f"REP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                execution_time = (datetime.now() - start_time).total_seconds()
                return {
                    "success": True,
                    "agent_name": self.name,
                    "status": "completed",
                    "analysis_result": json_text,
                    "parsed_data": parsed_data,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat()
                }
            except json.JSONDecodeError as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                return {
                    "success": False,
                    "agent_name": self.name,
                    "status": "json_parse_error",
                    "analysis_result": response,
                    "error": f"JSON 파싱 실패: {str(e)}",
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "success": False,
                "agent_name": self.name,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _extract_json_from_response(self, response: str) -> str:
        import re
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

    async def process_batch_images(self, image_paths: List[str]) -> Dict[str, Any]:
        try:
            start_time = datetime.now()
            results = []
            for image_path in image_paths:
                input_data = {
                    "image_path": image_path,
                    "data_type": "image",
                    "target_type": "securities_report",
                    "target_name": "배치 분석"
                }
                result = await self.analyze(input_data)
                results.append({
                    "image_path": image_path,
                    "result": result
                })
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": True,
                "total_images": len(image_paths),
                "processed_results": results,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def validate_image_quality(self, image_path: str) -> Dict[str, Any]:
        try:
            start_time = datetime.now()
            is_valid, message = self.image_processor.validate_image(image_path)
            if not is_valid:
                return {
                    "success": False,
                    "error": message,
                    "timestamp": datetime.now().isoformat()
                }
            processing_result = self.image_processor.optimize_image(image_path)
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": True,
                "is_valid": is_valid,
                "quality_score": processing_result.quality_score,
                "processing_time": execution_time,
                "metadata": processing_result.metadata,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# 편의 함수들
async def analyze_securities_report_image(image_path: str, target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    agent = SecuritiesReportAgent()
    input_data = {
        "image_path": image_path,
        "data_type": "image",
        "target_type": target_type,
        "target_name": target_name
    }
    return await agent.analyze(input_data)

async def process_batch_securities_reports(image_paths: List[str]) -> Dict[str, Any]:
    agent = SecuritiesReportAgent()
    return await agent.process_batch_images(image_paths)

async def validate_image_quality(image_path: str) -> Dict[str, Any]:
    agent = SecuritiesReportAgent()
    return await agent.validate_image_quality(image_path) 