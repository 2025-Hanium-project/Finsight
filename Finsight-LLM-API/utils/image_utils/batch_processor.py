from typing import List, Dict, Any
from .ocr import SecuritiesReportOCR, OCRResult

class BatchImageProcessor:
    """배치 이미지 처리 클래스"""
    def __init__(self):
        self.ocr_processor = SecuritiesReportOCR()

    async def process_batch(self, image_paths: List[str]) -> List[OCRResult]:
        results = []
        for image_path in image_paths:
            try:
                result = await self.ocr_processor.process_image_report(image_path)
                results.append(result)
            except Exception as e:
                results.append(OCRResult(
                    success=False,
                    error_message=str(e)
                ))
        return results

    def filter_successful_results(self, results: List[OCRResult]) -> List[OCRResult]:
        return [result for result in results if result.success]

    def get_quality_statistics(self, results: List[OCRResult]) -> Dict[str, Any]:
        if not results:
            return {}
        successful_results = self.filter_successful_results(results)
        if not successful_results:
            return {
                "total_count": len(results),
                "success_count": 0,
                "success_rate": 0.0
            }
        avg_confidence = sum(r.confidence_score for r in successful_results) / len(successful_results)
        avg_processing_time = sum(r.processing_time for r in successful_results) / len(successful_results)
        return {
            "total_count": len(results),
            "success_count": len(successful_results),
            "success_rate": len(successful_results) / len(results),
            "avg_confidence": avg_confidence,
            "avg_processing_time": avg_processing_time
        } 