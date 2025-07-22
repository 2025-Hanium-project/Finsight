// src/pages/DPlus1ReportPage.jsx
import React from "react";
import "../css/d_plus1.css";
import Menu from "../components/Menu"; // 메뉴 컴포넌트
// import Chart 등 차트 라이브러리 필요시 추가

function DPlus1ReportPage() {
  return (
    <div className="layout-container">
      {/* 사이드바 */}
      <div className="main-sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <span className="logo-icon">📊</span>
            <span>FinSight</span>
          </div>
        </div>
        <Menu />
      </div>

      {/* 메인 콘텐츠 */}
      <div className="dplus-content">
        <div className="dplus-header">
          <div>
            <h1 className="page-title">D+1 보고서</h1>
            <p className="date-info">
              {(() => {
                const d = new Date();
                d.setDate(d.getDate() - 1);
                return d.toLocaleDateString("ko-KR", { year: "numeric", month: "long", day: "numeric", weekday: "long" });
              })()}
            </p>
          </div>
          <div>
            <button className="export-pdf-button">PDF 내보내기</button>
          </div>
        </div>

        {/* 요약 섹션 */}
        <div className="summary-section">
          <h3 className="summary-title">전일 시장 요약</h3>
          <div className="summary-text">
            <p>
              전일 국내 증시는 미국 증시의 상승 영향과 IT 업종의 호실적 전망으로 상승 마감했습니다. 코스피는 전일 대비 0.82% 상승한 2,654.31포인트로 마감했으며, 코스닥은 0.37% 하락한 892.15로 마감했습니다. 외국인과 기관이 각각 1,234억원, 895억원 순매수를 기록했으며, 개인은 2,129억원 순매도했습니다. 업종별로는 IT 하드웨어(+2.3%), 에너지(+1.8%), 바이오(+1.5%) 업종이 강세를 보였습니다.
            </p>
          </div>
        </div>

        {/* 주요 지수 마감 현황 섹션 */}
        <div className="dashboard-grid">
          <div className="report-card">
            <div className="card-header">
              <h3 className="card-title">국내 지수 마감 결과</h3>
              <div className="card-icon">📈</div>
            </div>
            <div>
              <div className="market-index-row">
                <span className="index-label">코스피</span>
                <span className="index-value up">2,654.31 (+0.82%)</span>
              </div>
              <div className="market-index-row">
                <span className="index-label">코스닥</span>
                <span className="index-value down">892.15 (-0.37%)</span>
              </div>
              <div className="market-index-row">
                <span className="index-label">코스피 200</span>
                <span className="index-value up">348.52 (+0.92%)</span>
              </div>
              <div className="market-index-row">
                <span className="index-label">KRX 300</span>
                <span className="index-value up">1,458.30 (+0.75%)</span>
              </div>
            </div>
            <div className="summary-commentary">
              <p>
                코스피는 외국인과 기관의 동반 매수세에 힘입어 상승 마감했습니다. 특히 반도체 업종의 강세가 지수 상승을 주도했으며, 코스닥은 게임 및 엔터 업종의 약세로 소폭 하락했습니다.
              </p>
            </div>
          </div>

          <div className="report-card">
            <div className="card-header">
              <h3 className="card-title">글로벌 지수 마감 결과</h3>
              <div className="card-icon">🌐</div>
            </div>
            <div>
              <div className="market-index-row">
                <span className="index-label">다우존스</span>
                <span className="index-value up">39,735.31 (+0.92%)</span>
              </div>
              <div className="market-index-row">
                <span className="index-label">나스닥</span>
                <span className="index-value up">17,243.15 (+1.25%)</span>
              </div>
              <div className="market-index-row">
                <span className="index-label">S&amp;P 500</span>
                <span className="index-value up">5,345.31 (+0.82%)</span>
              </div>
              <div className="market-index-row">
                <span className="index-label">필라델피아 반도체</span>
                <span className="index-value up">4,215.75 (+2.34%)</span>
              </div>
              <div className="market-index-row">
                <span className="index-label">니케이 225</span>
                <span className="index-value down">38,245.15 (-0.37%)</span>
              </div>
              <div className="market-index-row">
                <span className="index-label">상해종합</span>
                <span className="index-value up">3,180.50 (+0.45%)</span>
              </div>
            </div>
          </div>
        </div>

        {/* 전일 주요 종목 분석 및 투자 의견 섹션 */}
        <div className="report-card full-width">
          <div className="card-header">
            <h3 className="card-title">전일 주요 종목의 종합 분석 및 의견 제공</h3>
            <div className="card-icon">🔎</div>
          </div>
          <div className="table-box">
            <table>
              <thead>
                <tr>
                  <th>종목</th>
                  <th>종가</th>
                  <th>변동률</th>
                  <th>거래량</th>
                  <th>주요 이슈</th>
                  <th>투자 의견</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>삼성전자</td>
                  <td>74,200원</td>
                  <td className="up">+1.78%</td>
                  <td>8,521,345주</td>
                  <td>1분기 영업이익 컨센서스 상회, AI 반도체 사업 확대 소식</td>
                  <td><span className="badge badge-positive">매수</span></td>
                </tr>
                <tr>
                  <td>SK하이닉스</td>
                  <td>169,500원</td>
                  <td className="up">+2.42%</td>
                  <td>3,254,789주</td>
                  <td>HBM 수요 급증, 메모리 가격 지속 상승 전망</td>
                  <td><span className="badge badge-positive">매수</span></td>
                </tr>
                <tr>
                  <td>LG에너지솔루션</td>
                  <td>408,000원</td>
                  <td className="up">+3.55%</td>
                  <td>987,654주</td>
                  <td>테슬라 실적 호조에 따른 수혜주 부각</td>
                  <td><span className="badge badge-positive">매수</span></td>
                </tr>
                <tr>
                  <td>현대차</td>
                  <td>196,000원</td>
                  <td className="down">-0.76%</td>
                  <td>1,254,789주</td>
                  <td>원화 강세 영향 및 중국 시장 경쟁 심화 우려</td>
                  <td><span className="badge badge-neutral">중립</span></td>
                </tr>
                <tr>
                  <td>카카오</td>
                  <td>60,500원</td>
                  <td className="down">-1.63%</td>
                  <td>2,345,678주</td>
                  <td>실적 우려 및 경쟁 심화로 인한 투자심리 위축</td>
                  <td><span className="badge badge-neutral">중립</span></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="opinion-summary">
            <p>
              <strong>종합 의견:</strong> 전일 시장은 반도체 및 2차전지 관련주의 강세가 뚜렷했습니다. 삼성전자와 SK하이닉스는 AI 반도체 수요 증가 기대감으로 상승했으며, LG에너지솔루션은 테슬라 호실적에 따른 수혜로 강세를 보였습니다. 반면 현대차는 원화 강세에 따른 수출 경쟁력 약화 우려로 약세를 보였고, 카카오는 실적 불확실성으로 하락했습니다. 향후 IT 하드웨어와 2차전지 업종의 강세가 이어질 것으로 전망됩니다.
            </p>
          </div>
        </div>

        {/* 주가 변동률 및 이슈 분석 섹션 */}
        <div className="dashboard-grid">
          {/* 상승률 Top 5 */}
          <div className="report-card">
            <div className="card-header">
              <h3 className="card-title">상승률 Top 5 종목</h3>
              <div className="card-icon">⬆️</div>
            </div>
            <div className="table-box">
              <table>
                <thead>
                  <tr>
                    <th>종목</th>
                    <th>종가</th>
                    <th>변동률</th>
                    <th>종목별 변동 이슈 원인 분석</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>네이버</td>
                    <td>280,500원</td>
                    <td className="up">+5.20%</td>
                    <td>AI 플랫폼 확장 계획 발표, 글로벌 진출 가속화</td>
                  </tr>
                  <tr>
                    <td>LG에너지솔루션</td>
                    <td>408,000원</td>
                    <td className="up">+3.55%</td>
                    <td>테슬라 실적 호조에 따른 수혜주 부각</td>
                  </tr>
                  <tr>
                    <td>POSCO홀딩스</td>
                    <td>452,000원</td>
                    <td className="up">+3.20%</td>
                    <td>이차전지 소재 사업 확대, 리튬 생산량 증가</td>
                  </tr>
                  <tr>
                    <td>SK하이닉스</td>
                    <td>169,500원</td>
                    <td className="up">+2.42%</td>
                    <td>HBM 수요 급증, 메모리 가격 지속 상승 전망</td>
                  </tr>
                  <tr>
                    <td>삼성바이오로직스</td>
                    <td>825,000원</td>
                    <td className="up">+2.10%</td>
                    <td>글로벌 제약사와 대규모 위탁생산 계약 체결 소식</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* 하락률 Top 5 */}
          <div className="report-card">
            <div className="card-header">
              <h3 className="card-title">하락률 Top 5 종목</h3>
              <div className="card-icon">⬇️</div>
            </div>
            <div className="table-box">
              <table>
                <thead>
                  <tr>
                    <th>종목</th>
                    <th>종가</th>
                    <th>변동률</th>
                    <th>종목별 변동 이슈 원인 분석</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>카카오</td>
                    <td>60,500원</td>
                    <td className="down">-3.80%</td>
                    <td>실적 우려 및 플랫폼 경쟁 심화로 인한 투자심리 위축</td>
                  </tr>
                  <tr>
                    <td>현대중공업</td>
                    <td>142,500원</td>
                    <td className="down">-2.73%</td>
                    <td>글로벌 수주 경쟁 격화, 원가 부담 증가</td>
                  </tr>
                  <tr>
                    <td>셀트리온</td>
                    <td>189,000원</td>
                    <td className="down">-2.32%</td>
                    <td>주요 바이오시밀러 제품 판매 부진 우려</td>
                  </tr>
                  <tr>
                    <td>기아</td>
                    <td>112,000원</td>
                    <td className="down">-1.75%</td>
                    <td>현대차 그룹주 동반 약세, 중국/유럽 시장 수요 둔화 우려</td>
                  </tr>
                  <tr>
                    <td>NAVER</td>
                    <td>210,500원</td>
                    <td className="down">-1.63%</td>
                    <td>플랫폼 비즈니스 수익성 저하 우려, 경쟁 심화</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* 컨센서스 변화 분석 섹션 */}
        <div className="report-card full-width">
          <div className="card-header">
            <h3 className="card-title">전일 대비 컨센서스 변화 비교 분석</h3>
            <div className="card-icon">📊</div>
          </div>
          <div className="table-box">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>종목</th>
                  <th>전일 목표가</th>
                  <th>현재 목표가</th>
                  <th>변화</th>
                  <th>전일 투자의견</th>
                  <th>현재 투자의견</th>
                  <th>변화 원인</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>삼성전자</td>
                  <td>80,000원</td>
                  <td>85,000원</td>
                  <td className="up">+6.25%</td>
                  <td>매수 (18)</td>
                  <td>매수 (19)</td>
                  <td>1분기 실적 컨센서스 상회, AI 반도체 수요 증가</td>
                </tr>
                <tr>
                  <td>SK하이닉스</td>
                  <td>185,000원</td>
                  <td>200,000원</td>
                  <td className="up">+8.11%</td>
                  <td>매수 (16)</td>
                  <td>매수 (16)</td>
                  <td>HBM 가격 상승세 지속, 메모리 수급 개선</td>
                </tr>
                <tr>
                  <td>LG에너지솔루션</td>
                  <td>460,000원</td>
                  <td>450,000원</td>
                  <td className="down">-2.17%</td>
                  <td>매수 (10), 중립 (3)</td>
                  <td>매수 (10), 중립 (4)</td>
                  <td>중국 배터리 업체 경쟁 심화, 원자재 원가 부담</td>
                </tr>
                <tr>
                  <td>현대차</td>
                  <td>205,000원</td>
                  <td>210,000원</td>
                  <td className="up">+2.44%</td>
                  <td>매수 (12), 중립 (4)</td>
                  <td>매수 (12), 중립 (4)</td>
                  <td>전기차 라인업 확대, 판매량 증가 전망</td>
                </tr>
                <tr>
                  <td>카카오</td>
                  <td>68,000원</td>
                  <td>65,000원</td>
                  <td className="down">-4.41%</td>
                  <td>매수 (8), 중립 (4)</td>
                  <td>매수 (7), 중립 (5)</td>
                  <td>핀테크 사업 규제 확대 우려, 플랫폼 비즈니스 수익성 악화</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="summary-commentary">
            <p>
              <strong>컨센서스 변화 분석:</strong> 전일 발표된 실적 자료와 글로벌 시장 동향을 반영하여 증권사들이 투자의견과 목표가를 조정했습니다. 특히 반도체 업종의 목표가 상향이 뚜렷했으며, 플랫폼 비즈니스 관련 종목들은 다소 하향 조정되는 경향을 보였습니다. 전체적으로 기술주 중심의 긍정적 전망이 유지되고 있으며, 소비재 및 자동차 업종은 혼조세를 보이고 있습니다.
            </p>
          </div>
        </div>

        {/* 목표가 근접 여부 분석 섹션 */}
        <div className="dashboard-grid">
          {/* 목표가 달성 근접률 */}
          <div className="report-card">
            <div className="card-header">
              <h3 className="card-title">목표가 달성 근접률</h3>
              <div className="card-icon">🎯</div>
            </div>
            <div className="table-box">
              <table>
                <thead>
                  <tr>
                    <th>종목</th>
                    <th>현재가</th>
                    <th>평균 목표가</th>
                    <th>달성률</th>
                    <th>달성 예상 시기</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>삼성전자</td>
                    <td>74,200원</td>
                    <td>85,000원</td>
                    <td>87.3%</td>
                    <td>1~2개월 내</td>
                  </tr>
                  <tr>
                    <td>SK하이닉스</td>
                    <td>169,500원</td>
                    <td>200,000원</td>
                    <td>84.8%</td>
                    <td>1~3개월 내</td>
                  </tr>
                  <tr>
                    <td>LG에너지솔루션</td>
                    <td>408,000원</td>
                    <td>450,000원</td>
                    <td>90.7%</td>
                    <td>1개월 내</td>
                  </tr>
                  <tr>
                    <td>현대차</td>
                    <td>196,000원</td>
                    <td>210,000원</td>
                    <td>93.3%</td>
                    <td>1개월 내</td>
                  </tr>
                  <tr>
                    <td>카카오</td>
                    <td>60,500원</td>
                    <td>65,000원</td>
                    <td>93.1%</td>
                    <td>1~2개월 내</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* 목표가 미달성 원인 분석 */}
          <div className="report-card">
            <div className="card-header">
              <h3 className="card-title">목표가 미달성 원인 분석</h3>
              <div className="card-icon">📉</div>
            </div>
            <div className="gap-reason-analysis">
              <div className="gap-reason-card">
                <div className="gap-reason-title">삼성전자 (87.3%)</div>
                <p>
                  실적 개선 기대감에도 불구하고 글로벌 IT 수요 회복 지연과 지정학적 리스크로 인한 투자심리 위축이 목표가 달성을 지연시키고 있습니다.
                </p>
              </div>
              <div className="gap-reason-card">
                <div className="gap-reason-title">SK하이닉스 (84.8%)</div>
                <p>
                  HBM 수요 증가와 메모리 가격 상승에도 불구하고 메모리 시장의 완전한 회복에 대한 불확실성과 투자비용 증가 우려가 목표가 달성을 제한하고 있습니다.
                </p>
              </div>
              <div className="gap-reason-card">
                <div className="gap-reason-title">LG에너지솔루션 (90.7%)</div>
                <p>
                  전기차 배터리 수요 증가에도 불구하고 중국 경쟁사들과의 가격 경쟁과 원자재 가격 상승으로 인한 수익성 둔화 우려가 존재합니다.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* 시장 심리 및 감성 분석 결과 섹션 */}
        <div className="dashboard-grid">
          {/* 시장 심리 진단 */}
          <div className="report-card">
            <div className="card-header">
              <h3 className="card-title">감성 분석 기반 시장 심리 진단</h3>
              <div className="card-icon">🧠</div>
            </div>
            <div className="sentiment-overview">
              <div className="market-sentiment-score">
                <div className="sentiment-label">전체 시장 심리 지수</div>
                <div className="sentiment-value">65.8</div>
                <div className="sentiment-status positive">적정 낙관</div>
              </div>
              <div className="sentiment-scale-labels">
                <span>비관적</span>
                <span>중립</span>
                <span>낙관적</span>
              </div>
              <div className="sentiment-gauge">
                <div
                  className="sentiment-indicator"
                  style={{ left: "65.8%" }}
                ></div>
              </div>
              <div className="sector-sentiment-list">
                <div className="sector-title">업종별 심리 지수</div>
                <div className="sector-sentiment-bar">
                  <div className="goal-label">반도체</div>
                  <div className="goal-bar">
                    <div
                      className="sentiment-fill progress-positive"
                      style={{ width: "82%" }}
                    ></div>
                  </div>
                  <div className="goal-percent">82.0</div>
                </div>
                <div className="sector-sentiment-bar">
                  <div className="goal-label">2차전지</div>
                  <div className="goal-bar">
                    <div
                      className="sentiment-fill progress-positive"
                      style={{ width: "75%" }}
                    ></div>
                  </div>
                  <div className="goal-percent">75.0</div>
                </div>
                <div className="sector-sentiment-bar">
                  <div className="goal-label">바이오</div>
                  <div className="goal-bar">
                    <div
                      className="sentiment-fill progress-positive"
                      style={{ width: "68%" }}
                    ></div>
                  </div>
                  <div className="goal-percent">68.0</div>
                </div>
                <div className="sector-sentiment-bar">
                  <div className="goal-label">자동차</div>
                  <div className="goal-bar">
                    <div
                      className="sentiment-fill progress-neutral"
                      style={{ width: "62%" }}
                    ></div>
                  </div>
                  <div className="goal-percent">62.0</div>
                </div>
                <div className="sector-sentiment-bar">
                  <div className="goal-label">IT 플랫폼</div>
                  <div className="goal-bar">
                    <div
                      className="sentiment-fill progress-neutral"
                      style={{ width: "54%" }}
                    ></div>
                  </div>
                  <div className="goal-percent">54.0</div>
                </div>
              </div>
            </div>
          </div>
          {/* 감성 분석 결과 상세 */}
          <div className="report-card">
            <div className="card-header">
              <h3 className="card-title">감성 분석 결과 상세</h3>
              <div className="card-icon">📊</div>
            </div>
            <div className="sentiment-details">
              <div className="data-source">
                <div className="source-title">데이터 소스</div>
                <p>
                  증권사 리포트, 뉴스 기사, 소셜 미디어, 투자자 커뮤니티 게시글 데이터 (72시간 내 84,523건 분석)
                </p>
              </div>
              <div className="sentiment-distribution">
                <div className="distribution-title">감성 분포</div>
                <div className="distribution-stats">
                  <div className="stat-item">
                    <div className="stat-value positive">56.2%</div>
                    <div className="stat-label">긍정적</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value neutral">32.5%</div>
                    <div className="stat-label">중립적</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value negative">11.3%</div>
                    <div className="stat-label">부정적</div>
                  </div>
                </div>
              </div>
              <div className="sentiment-keywords">
                <div className="keywords-title">주요 감성 키워드</div>
                <div className="keywords-tags">
                  <span className="tag positive">반도체 호황</span>
                  <span className="tag positive">AI 성장</span>
                  <span className="tag positive">실적 회복</span>
                  <span className="tag warning">인플레이션</span>
                  <span className="tag warning">금리 동결</span>
                  <span className="tag negative">중국 경쟁</span>
                  <span className="tag negative">경기 둔화</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 투자 의견 적중률 및 평균 수익률 결과 섹션 */}
        <div className="dashboard-grid">
          {/* 증권사별 투자 의견 적중률 */}
          <div className="report-card">
            <div className="card-header">
              <h3 className="card-title">증권사별 투자 의견 적중률</h3>
              <div className="card-icon">📈</div>
            </div>
            <div className="table-box">
              <table>
                <thead>
                  <tr>
                    <th>증권사</th>
                    <th>적중률</th>
                    <th>평균 수익률</th>
                    <th>분석 종목수</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>삼성증권</td>
                    <td>78.5%</td>
                    <td className="up">+15.2%</td>
                    <td>128</td>
                  </tr>
                  <tr>
                    <td>미래에셋증권</td>
                    <td>76.8%</td>
                    <td className="up">+14.7%</td>
                    <td>142</td>
                  </tr>
                  <tr>
                    <td>NH투자증권</td>
                    <td>75.3%</td>
                    <td className="up">+13.9%</td>
                    <td>135</td>
                  </tr>
                  <tr>
                    <td>KB증권</td>
                    <td>73.6%</td>
                    <td className="up">+12.8%</td>
                    <td>122</td>
                  </tr>
                  <tr>
                    <td>신한금융투자</td>
                    <td>72.1%</td>
                    <td className="up">+12.4%</td>
                    <td>117</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          {/* 투자 의견 통계 */}
          <div className="report-card">
            <div className="card-header">
              <h3 className="card-title">투자 의견 통계</h3>
              <div className="card-icon">📊</div>
            </div>
            <div className="investment-stats-panel">
              <div className="donut-chart-area">
                <div className="donut-chart">
                  <div className="chart-center">75.2%</div>
                </div>
              </div>
              <div className="legend-box">
                <div className="legend-item">
                  <div className="legend-color success"></div>
                  <span>매수 적중 (75.2%)</span>
                </div>
                <div className="legend-item">
                  <div className="legend-color warning"></div>
                  <span>중립 적중 (15.3%)</span>
                </div>
                <div className="legend-item">
                  <div className="legend-color danger"></div>
                  <span>매도 적중 (9.5%)</span>
                </div>
              </div>
              <div className="double-stat-columns">
                <div className="stats-column">
                  <div className="stats-item">
                    <div className="stats-label">평균 투자 기간</div>
                    <div className="stats-value">6.8개월</div>
                  </div>
                  <div className="stats-item">
                    <div className="stats-label">목표가 달성 비율</div>
                    <div className="stats-value">68.4%</div>
                  </div>
                </div>
                <div className="stats-column">
                  <div className="stats-item">
                    <div className="stats-label">평균 목표가 상향 조정</div>
                    <div className="stats-value">+7.2%</div>
                  </div>
                  <div className="stats-item">
                    <div className="stats-label">목표가 달성 평균 기간</div>
                    <div className="stats-value">4.3개월</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DPlus1ReportPage;
