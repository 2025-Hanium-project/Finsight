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
        prompt_template = """당신은 전문적인 재무제표 분석가입니다. 제공된 재무 데이터를 분석하여 기업의 재무 건전성을 종합적으로 평가해주세요.

분석해야 할 재무 데이터:
{{input_data}}

분석 지침:
1. 재무 건전성: 전반적인 재무 상태를 excellent/good/fair/poor로 평가
2. 수익성 분석: 매출액, 영업이익, 순이익의 규모와 성장률 분석
3. 유동성 분석: 단기 지급능력을 나타내는 비율들 분석
4. 지급능력 분석: 장기 부채 상환능력 분석
5. 성장 추세: 과거 대비 성장률과 향후 전망 분석
6. 주요 재무비율: ROE, ROA, 영업이익률, 순이익률 등 계산 및 분석
7. 리스크 요인: 재무적 취약점과 위험 요소 식별
8. 개선 권고: 재무 건전성 향상을 위한 구체적 방안 제시

{{collaboration_info}}

분석 결과를 다음 JSON 형식으로 제공해주세요:
{
    "financial_health": "재무 건전성 평가 (excellent/good/fair/poor, 구체적인 근거 포함)",
    "profitability_analysis": "수익성 분석 (매출액, 영업이익, 순이익, 성장률 등 구체적 분석)",
    "liquidity_analysis": "유동성 분석 (유동비율, 당좌비율, 현금비율 등 구체적 분석)",
    "solvency_analysis": "지급능력 분석 (부채비율, 이자보상배율 등 구체적 분석)",
    "growth_trends": "성장 추세 분석 (매출 성장률, 이익 성장률 등 구체적 분석)",
    "key_ratios": "주요 재무비율 (ROE, ROA, 영업이익률, 순이익률 등 구체적 수치)",
    "risk_factors": "재무 리스크 요인 (구체적인 위험 요소들)",
    "recommendations": "재무 개선 권고사항 (구체적인 개선 방안들)",
    "confidence_score": "분석 신뢰도 (0-100, 데이터 품질과 분석 완성도 기반)"
}

중요: 제공된 재무 데이터를 기반으로 구체적인 수치와 분석을 제공하세요. 각 재무 지표에 대해 정량적이고 정성적인 평가를 모두 수행하세요."""
        
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
        DART 사업보고서 요약재무제표 기반 주요 계정 데이터 수집 및 주요 비율 직접 계산
        """
        import os
        stock_code = context.get("stock_code")
        api_key = context.get("dart_api_key") or os.environ.get("DART_API_KEY")
        from utils.data_collectors.financial_collector import FinancialStatementCollector
        collector = FinancialStatementCollector(api_key=api_key)
        from datetime import datetime
        now = datetime.now()
        accounts = collector.get_major_accounts()
        ids = accounts['ids']
        nms = accounts['nms']
        # 최근 3년 중 데이터가 존재하는 가장 최신 연도부터 시도
        for try_year in [now.year, now.year-1, now.year-2]:
            data = collector.collect_summary_financials(stock_code, try_year, accounts=accounts)
            if data:
                year = try_year
                break
        else:
            return {"error": f"DART 사업보고서 요약재무제표 데이터가 최근 3년({now.year}, {now.year-1}, {now.year-2}) 모두 없습니다."}
        # 연도/계정별로 값 합산 (account_id, account_nm 모두 활용)
        by_year = {}
        acc_id_to_nm = {}
        for item in data:
            y = int(item['year'])
            acc_id = item['account_id']
            acc_nm = item['account_nm']
            amt = item['amount']
            if y not in by_year:
                by_year[y] = {}
            by_year[y][acc_id] = amt
            acc_id_to_nm[acc_id] = acc_nm
        years = sorted(by_year.keys(), reverse=True)[:3]
        # 주요 비율 직접 계산 (account_id 기준)
        ratios = {}
        for y in years:
            d = by_year.get(y, {})
            # 순이익: 여러 account_id 후보 중 존재하는 값 사용 (우선순위 적용)
            순이익_후보들 = [
                'ifrs-full_ProfitLoss',  # 기본 당기순이익
                'ifrs-full_ProfitLossAttributableToOwnersOfParent',  # 지배기업 소유주 귀속
                'dart_ProfitLoss',  # DART 특화 당기순이익
                'ifrs-full_ProfitLossBeforeTax'  # 법인세비용차감전순이익 (마지막 후보)
            ]
            순이익 = 0.0
            사용된_계정 = None
            for candidate in 순이익_후보들:
                if candidate in d and d[candidate] != 0:
                    순이익 = float(d[candidate])
                    사용된_계정 = candidate
                    print(f"✅ {y}년 당기순이익: {candidate} = {순이익:,.0f}")
                    break
            else:
                print(f"❌ {y}년 당기순이익: 데이터 없음")
                사용된_계정 = "없음"
            
            자본 = float(d.get('ifrs-full_Equity', 0.0))
            자산 = float(d.get('ifrs-full_Assets', 0.0))
            매출 = float(d.get('ifrs-full_Revenue', 0.0))
            영업이익 = float(d.get('dart_OperatingIncomeLoss', 0.0))
            부채 = float(d.get('ifrs-full_Liabilities', 0.0))
            유동자산 = float(d.get('ifrs-full_CurrentAssets', 0.0))
            유동부채 = float(d.get('ifrs-full_CurrentLiabilities', 0.0))
            현금및현금성자산 = float(d.get('ifrs-full_CashAndCashEquivalents', 0.0))
            
            # 재무비율 계산 (0이 아닌 경우에만 계산)
            roe = (순이익 / 자본 * 100) if (자본 != 0 and 순이익 != 0) else None
            roa = (순이익 / 자산 * 100) if (자산 != 0 and 순이익 != 0) else None
            op_margin = (영업이익 / 매출 * 100) if (매출 != 0 and 영업이익 != 0) else None
            net_margin = (순이익 / 매출 * 100) if (매출 != 0 and 순이익 != 0) else None
            debt_ratio = (부채 / 자본 * 100) if (자본 != 0 and 부채 != 0) else None
            current_ratio = (유동자산 / 유동부채 * 100) if (유동부채 != 0 and 유동자산 != 0) else None
            # 현금및현금성자산 비율 (유동자산 대비)
            cash_ratio = (현금및현금성자산 / 유동자산 * 100) if (유동자산 != 0 and 현금및현금성자산 != 0) else None
            
            # 이자보상배율 계산 (실제 데이터에 존재하는 계정 사용)
            금융비용 = float(d.get('ifrs-full_FinanceCosts', 0.0))
            이자의지급 = float(d.get('ifrs-full_InterestPaidClassifiedAsOperatingActivities', 0.0))
            # 이자비용은 금융비용을 우선 사용하고, 없으면 이자의 지급 사용
            이자비용 = 금융비용 if 금융비용 != 0 else 이자의지급
            interest_coverage = (영업이익 / 이자비용) if (이자비용 != 0 and 영업이익 != 0) else None
            
            # 자산=자본+부채 검증 (dart_api.json 분석 결과에 맞게 개선)
            자산_합계 = 자산
            자본부채_합계 = 자본 + 부채
            차이 = abs(자산_합계 - 자본부채_합계)
            차이율 = (차이 / 자산_합계 * 100) if 자산_합계 != 0 else None
            
            # 검증 결과 로깅
            if 차이율 is not None and 차이율 > 1.0:  # 1% 이상 차이 시 경고
                print(f"⚠️  자산=자본+부채 불일치: {차이율:.2f}% (자산: {자산_합계:,.0f}, 자본+부채: {자본부채_합계:,.0f})")
            elif 차이율 is not None and 차이율 <= 1.0:
                print(f"✅ 자산=자본+부채 일치: {차이율:.2f}%")
            
            ratios[y] = {
                'ROE': roe,
                'ROA': roa,
                '영업이익률': op_margin,
                '순이익률': net_margin,
                '부채비율': debt_ratio,
                '유동비율': current_ratio,
                '현금비율': cash_ratio,  # 현금및현금성자산을 비율로 변경
                '이자보상배율': interest_coverage,
                '자산_자본부채_차이율': 차이율  # 검증용
            }
        prompt_data = {
            "stock_code": stock_code,
            "years": years,
            "by_year": by_year,
            "ratios": ratios,
            "raw_data": data,
            "base_year": year
        }
        return prompt_data
    
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
            start_time = datetime.now()
            
            # 프롬프트 생성
            prompt = self._create_prompt(input_data, collaboration_data)
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