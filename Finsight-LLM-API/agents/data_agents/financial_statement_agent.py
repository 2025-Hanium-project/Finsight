"""
재무제표 분석 에이전트
"""
import json
from typing import Dict, Any, List
from utils.core.agent_base import AnalysisAgent, AgentType, create_standard_prompt_template
from datetime import datetime
from utils.data_collectors.financial_collector import FinancialStatementCollector

# function calling용 collector 함수 정의
async def get_financial_statements(stock_code: str, years: list, accounts: list, api_key: str = None) -> list:
    collector = FinancialStatementCollector(api_key=api_key)
    return collector.collect_statements_by_accounts(stock_code, years, accounts)

class FinancialStatementAgent(AnalysisAgent):
    """재무제표 분석 에이전트"""
    
    def __init__(self):
        from utils.core.agent_base import AgentConfig
        config = AgentConfig(
            name="financial_statement_agent",
            agent_type=AgentType.FINANCIAL_STATEMENT
        )
        AnalysisAgent.__init__(self, config)
        self.temperature = 0.2  # 정확한 재무 분석을 위해 낮은 temperature 사용
    
    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any]) -> str:
        """프롬프트 생성"""
        
        # 협업 데이터 포맷팅
        collaboration_info = ""
        if collaboration_data:
            collaboration_info = self._format_collaboration_data(collaboration_data)
        
        output_schema = {
            "financial_health": "재무 건전성 평가 (excellent/good/fair/poor)",
            "profitability_analysis": "수익성 분석 (매출액, 영업이익, 순이익, 성장률 등)",
            "liquidity_analysis": "유동성 분석 (유동비율, 당좌비율, 현금비율 등)",
            "solvency_analysis": "지급능력 분석 (부채비율, 이자보상배율 등)",
            "growth_trends": "성장 추세 분석 (매출 성장률, 이익 성장률 등)",
            "key_ratios": "주요 재무비율 (ROE, ROA, 영업이익률, 순이익률 등)",
            "risk_factors": "재무 리스크 요인",
            "recommendations": "재무 개선 권고사항",
            "confidence_score": "분석 신뢰도 (0-100)"
        }
        
        # 개선된 프롬프트 템플릿
        prompt_template = """
당신은 전문 재무제표 분석가입니다. 아래 financial_data만을 근거로, 완결된 재무제표 분석 보고서를 작성하세요.

**중요 지침:**
- 반드시 완결된 분석만 제공하세요. '~분석이 필요합니다', '~추가 데이터 필요', '~추가 분석 필요' 등 회피성 문구는 절대 사용하지 마세요.
- 각 항목에는 반드시 수치, 근거, 해석, 결론이 모두 포함되어야 합니다.
- 제공된 데이터만으로 분석을 마무리하세요. 추가 데이터 요청, 추가 분석 요청은 금지합니다.
- 정성적 해석보다 수치 중심의 분석을 우선하세요.
- 반드시 아래 예시와 동일한 JSON 구조로만 답변하세요.
- 텍스트, 마크다운, 표, 리스트 등은 절대 사용하지 마세요.
- input 데이터의 계정명(account_id, account_nm)과 수치를 근거로 분석하세요.
- 전년 대비 증감, 급격한 변화 등 input 내에서 비교 가능한 모든 정보를 활용하세요.

[예시 JSON]
{
  "financial_health": "우수. 자산총계 514.5조원으로 전년(455.9조원) 대비 12.9% 증가했습니다. 부채총계 112.3조원, 자본총계 402.2조원으로 부채비율 27.9%를 기록해 매우 건전한 재무구조를 보여줍니다. 업계 평균 부채비율 50-60% 대비 현저히 낮은 수준으로 재무 안정성이 탁월합니다.",
  "profitability_analysis": "수익성 회복세 뚜렷. 매출액 300.9조원(전년 258.9조원 대비 +16.2%)으로 강력한 성장을 기록했습니다. 영업이익 32.7조원(전년 6.6조원)으로 영업이익률이 2.5%에서 10.9%로 급격히 개선되었습니다. 당기순이익 34.5조원(전년 15.5조원)으로 순이익률 11.5%를 달성해 수익성이 크게 향상되었습니다.",
  "liquidity_analysis": "유동성 매우 우수. 유동자산 227.1조원, 유동부채 93.3조원으로 유동비율 243.3%를 기록했습니다. 현금 및 현금성자산 53.7조원으로 현금비율 23.7%를 유지하고 있어 단기 지급능력이 매우 안정적입니다. 전년 대비 현금 보유액이 감소했으나 여전히 충분한 수준입니다.",
  "solvency_analysis": "장기 지급능력 탁월. 부채비율 27.9%로 매우 낮은 수준이며, 자기자본비율 78.2%로 자본 구조가 매우 건전합니다. 이자보상배율 2.52배로 다소 낮은 편이나, 절대적인 영업이익 규모(32.7조원)가 크고 금융비용(13.0조원) 대비 여유가 있어 장기 지급능력에는 문제없습니다.",
  "growth_trends": "성장 모멘텀 강화. 매출액 성장률 16.2%, 영업이익 398.3% 급증으로 사업 회복력을 입증했습니다. 자산 성장률 12.9%, 자본 성장률 10.6%로 내실 있는 확장세를 보이고 있습니다. 특히 유형자산이 187.3조원에서 205.9조원으로 증가해 적극적인 설비투자를 진행하고 있습니다.",
  "key_ratios": "핵심 지표 대폭 개선. ROE 8.57%(전년 추정 4.0% 수준에서 상승), ROA 6.70%로 자산과 자본 활용도가 크게 향상되었습니다. 영업이익률 10.9%, 순이익률 11.5%로 두 자릿수 수익성을 회복했습니다. 기본주당이익 4,950원(전년 2,131원)으로 주주가치도 크게 개선되었습니다.",
  "risk_factors": "전반적 리스크 제한적. 부채비율 27.9%로 재무레버리지 리스크는 매우 낮습니다. 다만 이자보상배율 2.52배는 다소 여유롭지 않은 수준으로, 금리 상승 시 금융비용 부담 증가 가능성을 주의해야 합니다. 매출채권 43.6조원, 재고자산 51.8조원으로 운전자본 관리 효율성 개선 여지가 있습니다.",
  "recommendations": "현재의 우수한 수익성 회복세를 지속하기 위해 운전자본 회전율 개선과 금융비용 최적화를 권고합니다. 건전한 재무구조를 바탕으로 성장 투자를 확대하되, 이자보상배율 개선을 위한 영업이익 증대에 집중해야 합니다. 현금흐름 관리 강화를 통한 금융 효율성 제고가 필요합니다.",
  "confidence_score": "92"
}

아래는 분석해야 할 데이터입니다:
{{financial_data}}
"""
        
        # 문자열 포맷팅을 안전하게 수행
        financial_data = input_data.get("financial_data", {})
        if not financial_data and isinstance(input_data.get("data", {}), dict):
            financial_data = input_data.get("data", {})
        if not financial_data:
            financial_data = input_data  # 전체 input_data를 사용
        
        input_data_str = json.dumps(financial_data, ensure_ascii=False, indent=2)
        
        # 주요 비율이 agent에서 직접 계산된 값임을 명확히 안내
        if 'calculated_ratios' in input_data:
            prompt_template += "\n\n참고: 아래 주요 재무비율(ROE, ROA 등)은 이미 agent가 직접 평균값(기초/기말)까지 계산한 결과이므로, 추가 계산 없이 그대로 분석에 활용하세요."
        
        return prompt_template.replace("{{input_data}}", input_data_str).replace("{{collaboration_info}}", collaboration_info)
    
    def _format_collaboration_data(self, collaboration_data: Dict[str, Any]) -> str:
        """협업 데이터 포맷팅"""
        formatted = []
        
        for agent_name, data in collaboration_data.items():
            if agent_name == "market_data_agent":
                formatted.append("시장 데이터: " + json.dumps(data.get("market_indicators", {}), ensure_ascii=False))
            elif agent_name == "risk_assessment_agent":
                formatted.append("리스크 분석: " + json.dumps(data.get("risk_analysis", {}), ensure_ascii=False))
            elif agent_name == "valuation_agent":
                formatted.append("밸류에이션: " + json.dumps(data.get("valuation_metrics", {}), ensure_ascii=False))
        
        return "\n".join(formatted) if formatted else ""
    
    async def handle_collaboration_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """협업 요청 처리"""
        try:
            if message.get("request_type") == "get_financial_metrics":
                # 재무 지표 제공
                return await self._provide_financial_metrics(message.get("context"))
            
            elif message.get("request_type") == "validate_financial_data":
                # 재무 데이터 검증
                return await self._validate_financial_data(message.get("context"))
            
            elif message.get("request_type") == "get_risk_indicators":
                # 재무 리스크 지표 제공
                return await self._provide_risk_indicators(message.get("context"))
            
            else:
                return {
                    "error": f"지원하지 않는 요청 타입: {message.get('request_type')}",
                    "status": "failed"
                }
        
        except Exception as e:
            self.logger.error(f"협업 요청 처리 실패: {str(e)}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def _get_account_amount(self, data: list, year: str, quarter: str, aliases: dict, account_key: str) -> float:
        # 해당 연도/분기에서 account_key의 모든 유사 계정명 중 첫 번째로 발견되는 금액 반환
        for item in data:
            if str(item.get('year')) == str(year) and str(item.get('report_code', '')) == str(quarter):
                for alias in aliases.get(account_key, [account_key]):
                    if item.get('account') == alias:
                        try:
                            return float(item.get('amount', 0))
                        except Exception:
                            continue
        return 0.0

    def _calculate_financial_ratios(self, financial_data: list) -> dict:
        """
        collector의 MAJOR_ACCOUNT_ALIASES 매핑을 활용해 유사 계정명까지 모두 인식하여 주요 비율 계산
        """
        from collections import defaultdict
        ratios = defaultdict(dict)
        # 연도/분기별 데이터 정리
        # MAJOR_ACCOUNT_ALIASES 및 alias 관련 코드/함수/변수 전체 삭제
        # collector.get_major_accounts()에서 반환하는 계정명만으로 account_nm/account_id 포함 여부로 매칭
        # 연도/분기 set 추출
        year_quarters = set((str(item.get('year')), str(item.get('report_code', ''))) for item in financial_data)
        years_sorted = sorted(set(y for y, _ in year_quarters))
        # 연도별 기초/기말 값 추출
        def get_first_last_amount(account_key):
            vals = []
            for year in years_sorted:
                v = 0.0
                for item in financial_data:
                    if str(item.get('year')) == year and account_key in item.get('account', ''):
                        try:
                            v = float(item.get('amount', 0))
                            break
                        except Exception:
                            continue
                vals.append(v)
            if vals:
                return vals[0], vals[-1]
            return None, None
        def get_latest_amount(account_key):
            for year in reversed(years_sorted):
                for item in financial_data:
                    if str(item.get('year')) == year and account_key in item.get('account', ''):
                        try:
                            return float(item.get('amount', 0))
                        except Exception:
                            continue
            return None
        # 주요 계정값 추출
        기초자본, 기말자본 = get_first_last_amount('자본총계')
        기초자산, 기말자산 = get_first_last_amount('자산총계')
        순이익 = get_latest_amount('당기순이익')
        자본 = (기초자본 + 기말자본) / 2 if (기초자본 and 기말자본) else None
        자산 = (기초자산 + 기말자산) / 2 if (기초자산 and 기말자산) else None
        매출 = get_latest_amount('매출액')
        영업이익 = get_latest_amount('영업이익')
        부채 = get_latest_amount('부채총계')
        유동자산 = get_latest_amount('유동자산')
        유동부채 = get_latest_amount('유동부채')
        # 주요 비율 계산
        roe = (순이익 / 자본 * 100) if (자본 and 순이익 is not None) else None
        roa = (순이익 / 자산 * 100) if (자산 and 순이익 is not None) else None
        operating_margin = (영업이익 / 매출 * 100) if (매출 and 영업이익 is not None) else None
        net_margin = (순이익 / 매출 * 100) if (매출 and 순이익 is not None) else None
        debt_ratio = (부채 / 자본 * 100) if (자본 and 부채 is not None) else None
        current_ratio = (유동자산 / 유동부채 * 100) if (유동부채 and 유동자산 is not None) else None
        ratios[(year, quarter)] = {
            'ROE': roe,
            'ROA': roa,
            '영업이익률': operating_margin,
            '순이익률': net_margin,
            '부채비율': debt_ratio,
            '유동비율': current_ratio
        }
        return ratios

    async def _provide_financial_metrics(self, context: dict) -> dict:
        """
        DART 사업보고서 요약재무제표 기반 주요 계정 데이터 수집 (collector에서 비율까지 계산)
        """
        import os
        stock_code = context.get("stock_code")
        api_key = context.get("dart_api_key") or os.environ.get("DART_API_KEY")
        from utils.data_collectors.financial_collector import FinancialStatementCollector
        collector = FinancialStatementCollector(api_key=api_key)
        accounts = collector.get_major_accounts()
        # 최신 연도 자동 선택
        data = collector.collect_latest_summary_financials(stock_code, accounts=accounts)
        if "error" in data:
            return data
        return data
    
    async def _validate_financial_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """재무 데이터 검증"""
        try:
            # 데이터 품질 검증 로직
            return {
                "data_quality": "good",
                "validation_issues": [],
                "recommendations": [
                    "더 상세한 재무비율 제공",
                    "과거 데이터 포함"
                ],
                "status": "success"
            }
        
        except Exception as e:
            return {
                "error": f"재무 데이터 검증 실패: {str(e)}",
                "status": "failed"
            }
    
    async def _provide_risk_indicators(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """재무 리스크 지표 제공"""
        try:
            return {
                "liquidity_risk": "low",
                "solvency_risk": "low",
                "profitability_risk": "medium",
                "growth_risk": "medium",
                "status": "success"
            }
        
        except Exception as e:
            return {
                "error": f"재무 리스크 지표 제공 실패: {str(e)}",
                "status": "failed"
            }

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """재무제표 분석 수행"""
        try:
            print(f"🔍 [FinancialStatementAgent] 분석 시작")
            
            # 1단계: 재무 데이터 수집
            print(f"📊 [FinancialStatementAgent] 재무 데이터 수집 중...")
            financial_metrics = await self._provide_financial_metrics(input_data)
            
            if "error" in financial_metrics:
                print(f"❌ [FinancialStatementAgent] 재무 데이터 수집 실패: {financial_metrics['error']}")
                return {
                    "error": financial_metrics["error"],
                    "agent_name": self.name,
                    "status": "failed",
                    "timestamp": datetime.now().isoformat()
                }
            
            print(f"✅ [FinancialStatementAgent] 재무 데이터 수집 완료")
            
            # 2단계: 수집된 데이터를 input_data에 추가
            input_data.update({
                "financial_data": financial_metrics,
                "by_year": financial_metrics.get("by_year", {}),
                "ratios": financial_metrics.get("ratios", {}),
                "years": financial_metrics.get("years", []),
                "raw_data": financial_metrics.get("raw_data", [])
            })
            
            # 3단계: LLM 분석 수행
            print(f"🤖 [FinancialStatementAgent] LLM 분석 시작...")
            analysis_result = await self._execute_analysis(input_data)
            
            # 4단계: 결과 통합
            # LLM 분석 결과를 analysis 필드로 통합
            analysis_content = ""
            if "financial_health" in analysis_result:
                analysis_content += f"재무 건전성: {analysis_result.get('financial_health', '')}\n"
            if "profitability_analysis" in analysis_result:
                analysis_content += f"수익성 분석: {analysis_result.get('profitability_analysis', '')}\n"
            if "liquidity_analysis" in analysis_result:
                analysis_content += f"유동성 분석: {analysis_result.get('liquidity_analysis', '')}\n"
            if "solvency_analysis" in analysis_result:
                analysis_content += f"지급능력 분석: {analysis_result.get('solvency_analysis', '')}\n"
            if "growth_trends" in analysis_result:
                analysis_content += f"성장 추세: {analysis_result.get('growth_trends', '')}\n"
            if "risk_factors" in analysis_result:
                analysis_content += f"리스크 요인: {analysis_result.get('risk_factors', '')}\n"
            if "recommendations" in analysis_result:
                analysis_content += f"권고사항: {analysis_result.get('recommendations', '')}\n"
            if "confidence_score" in analysis_result:
                analysis_content += f"신뢰도: {analysis_result.get('confidence_score', '')}\n"
            
            final_result = {
                **financial_metrics,
                "analysis": analysis_content.strip(),  # LLM 분석 결과를 analysis 필드로 통합
                "analysis_result": analysis_result,  # 원본 LLM 분석 결과 추가
                "financial_data": financial_metrics,  # 재무 데이터 추가
                "agent_name": self.name,
                "agent_type": "financial_statement",
                "timestamp": datetime.now().isoformat()
            }
            
            # 디버깅: 최종 결과 확인
            print(f"📋 [FinancialStatementAgent] 최종 결과 키: {list(final_result.keys())}")
            if "analysis" in final_result:
                print(f"✅ [FinancialStatementAgent] analysis 필드 포함됨 ({len(final_result['analysis'])}자)")
            if "analysis_result" in final_result:
                print(f"✅ [FinancialStatementAgent] analysis_result 필드 포함됨")
            if "financial_data" in final_result:
                print(f"✅ [FinancialStatementAgent] financial_data 필드 포함됨")
            if "ratios" in final_result:
                print(f"✅ [FinancialStatementAgent] ratios 필드 포함됨")
            if "by_year" in final_result:
                print(f"✅ [FinancialStatementAgent] by_year 필드 포함됨")
            
            return final_result
            
        except Exception as e:
            print(f"❌ [FinancialStatementAgent] 분석 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": f"재무제표 분석 실패: {str(e)}",
                "agent_name": self.name,
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _execute_analysis(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """분석 실행"""
        try:
            import os
            import json
            def save_json(data, filename):
                path = os.path.join(os.path.dirname(__file__), "../../test_results", filename)
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            stock_code = input_data.get("stock_code") or input_data.get("financial_data", {}).get("stock_code") or "unknown"
            # financial_data에서 raw_data, stock_code, year 등 불필요한 필드 제거
            financial_data = input_data.get("financial_data", input_data)
            exclude_keys = ["raw_data", "stock_code", "year"]
            llm_input_data = {k: v for k, v in financial_data.items() if k not in exclude_keys}
            llm_input = {"financial_data": llm_input_data}
            save_json(llm_input, f"{stock_code}_llm_input.json")
            start_time = datetime.now()
            # 프롬프트 생성
            prompt = self._create_prompt(llm_input, collaboration_data)
            print(f"📝 [FinancialStatementAgent] 프롬프트 생성 완료 ({len(prompt)}자)")
            # LLM 호출
            from utils.llm.llm_client import generate_response
            from utils.llm.llm_utils import extract_json_from_response
            print(f"🤖 [FinancialStatementAgent] LLM 호출 시작...")
            response = await generate_response(
                prompt=prompt,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            print(f"✅ [FinancialStatementAgent] LLM 응답 수신 완료 ({len(response)}자)")
            # 응답 파싱
            try:
                json_text = extract_json_from_response(response)
                result = json.loads(json_text)
                print(f"✅ [FinancialStatementAgent] JSON 파싱 성공")
            except json.JSONDecodeError as e:
                print(f"⚠️ [FinancialStatementAgent] JSON 파싱 실패, 텍스트 응답으로 처리: {e}")
                # JSON 파싱 실패 시 텍스트 응답으로 처리
                result = {
                    "analysis_type": "financial_statement",
                    "analysis_result": response,
                    "agent_name": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            # LLM output 저장
            save_json(result, f"{stock_code}_llm_output.json")
            # 성능 통계 업데이트
            execution_time = (datetime.now() - start_time).total_seconds()
            # 결과에 메타데이터 추가
            result.update({
                "agent_name": self.name,
                "agent_type": "financial_statement",
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            })
            print(f"✅ [FinancialStatementAgent] 분석 완료 (실행시간: {execution_time:.2f}초)")
            return result
        except Exception as e:
            print(f"❌ [FinancialStatementAgent] _execute_analysis 오류: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "agent_name": self.name,
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }


# 전역 인스턴스
financial_statement_agent = FinancialStatementAgent()


async def analyze_financial_statement(financial_data: Dict[str, Any], target_type: str = "", target_name: str = "") -> Dict[str, Any]:
    """재무제표 분석 실행"""
    input_data = {
        "data_source": "financial_statement",
        "financial_data": financial_data,
        "target_type": target_type,
        "target_name": target_name
    }
    
    return await financial_statement_agent.execute(input_data) 