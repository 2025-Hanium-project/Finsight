// src/pages/IndexPage.jsx

import React, { useEffect, useRef, useState } from "react";
import Menu from "../components/Menu";      // menu.html JSX 변환 필요
import Navbar from "../components/Navbar";  // navbar.html JSX 변환 필요
import Chart from "chart.js/auto"; 
import "../css/dashboard.css";


//const CHART_URL = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js";

function IndexPage() {
  const chartRef = useRef(null);     // canvas ref
  const chartInstance = useRef(null); // chart.js instance ref

  // 시장지수 데이터 상태 추가
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);

  // fetch로 시장지수 데이터 불러오기
  useEffect(() => {
    fetch("/api/direct/market/today")
      .then(res => {
        if (!res.ok) throw new Error("Network response was not ok");
        return res.json();
      })
      .then(data => {
        setMarketData(data);
        setLoading(false);
      })
      .catch(() => {
        setMarketData(null);
        setLoading(false);
      });
  }, []);

  // 카드 디자인을 위한 유틸
  const formatChange = (value) => (value > 0 ? `+${value}` : value);
  const getChangeClass = (value) =>
    value > 0
      ? "change-positive"
      : value < 0
      ? "change-negative"
      : "";

  useEffect(() => {
    // 이전 차트 인스턴스 파괴
    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    // 차트 그리기
    if (chartRef.current) {
      chartInstance.current = new Chart(chartRef.current, {
        type: "line",
        data: {
          labels: ["9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"],
          datasets: [
            {
              label: "코스피",
              data: [2630.11, 2638.27, 2645.18, 2642.35, 2646.89, 2651.72, 2654.31],
              borderColor: "#2d63eb",
              backgroundColor: "rgba(45, 99, 235, 0.1)",
              tension: 0.1,
              pointRadius: 2,
              borderWidth: 1.5
            },
            {
              label: "코스닥",
              data: [885.15, 887.42, 889.76, 888.93, 890.25, 891.38, 892.15],
              borderColor: "#ff6b8b",
              backgroundColor: "rgba(255, 107, 139, 0.1)",
              tension: 0.1,
              pointRadius: 2,
              borderWidth: 1.5
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "top",
              align: "end"
            }
          }
        }
      });
    }

    // 언마운트 시 파괴
    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, []);

  // 시장지수 카드 JSX (로딩/에러 처리)
  const renderMarketIndexGrid = () => {
    if (loading) {
      return (
        <div className="market-index-grid">
          <div style={{ gridColumn: "1/5", textAlign: "center", padding: 20 }}>불러오는 중...</div>
        </div>
      );
    }
    if (!marketData) {
      return (
        <div className="market-index-grid">
          <div style={{ gridColumn: "1/5", textAlign: "center", padding: 20, color: "#ff6b6b" }}>
            시장 지수 데이터를 불러올 수 없습니다.
          </div>
        </div>
      );
    }
    return (
      <div className="market-index-grid">
        {/* 코스피 */}
        <div className="market-index-card">
          <div className="card-header">
            <h3 className="card-title"><i className="fas fa-chart-line"></i>&nbsp;코스피</h3>
            <div className={`card-status-icon ${marketData.kospi.change > 0 ? "caret-up" : "caret-down"}`}>
              <i className={`fas fa-caret-${marketData.kospi.change > 0 ? "up" : "down"}`}></i>
            </div>
          </div>
          <div className="market-index-content">
            <div style={{ display: "flex", flexDirection: "column" }}>
              <span style={{ fontSize: "1.8rem", fontWeight: 700 }}>
                {marketData.kospi.close.toLocaleString()}
              </span>
              <span className={getChangeClass(marketData.kospi.change)} style={{ fontWeight: 500 }}>
                {formatChange(marketData.kospi.change.toFixed(2))} ({formatChange(marketData.kospi.change_rate.toFixed(2))}%)
              </span>
            </div>
          </div>
        </div>
        {/* 코스닥 */}
        <div className="market-index-card">
          <div className="card-header">
            <h3 className="card-title"><i className="fas fa-chart-line"></i> 코스닥</h3>
            <div className={`card-status-icon ${getChangeClass(marketData.kosdaq.change)}`}>
              <i className={`fas fa-caret-${marketData.kosdaq.change > 0 ? "up" : "down"}`}></i>
            </div>
          </div>
          <div className="market-index-content">
            <div style={{ display: "flex", flexDirection: "column" }}>
              <span style={{ fontSize: "1.8rem", fontWeight: 700 }}>
                {marketData.kosdaq.close.toLocaleString()}
              </span>
              <span className={getChangeClass(marketData.kosdaq.change)} style={{ fontWeight: 500 }}>
                {formatChange(marketData.kosdaq.change.toFixed(2))} ({formatChange(marketData.kosdaq.change_rate.toFixed(2))}%)
              </span>
            </div>
          </div>
        </div>
        {/* 원/달러 */}
        <div className="market-index-card">
          <div className="card-header">
            <h3 className="card-title"><i className="fas fa-dollar-sign"></i> 원/달러</h3>
            <div className={`card-status-icon ${getChangeClass(marketData.usdkrw.change)}`}>
              <i className={`fas fa-caret-${marketData.usdkrw.change > 0 ? "up" : "down"}`}></i>
            </div>
          </div>
          <div className="market-index-content">
            <div style={{ display: "flex", flexDirection: "column" }}>
              <span style={{ fontSize: "1.8rem", fontWeight: 700 }}>
                {marketData.usdkrw.today.toLocaleString()}
              </span>
              <span className={getChangeClass(marketData.usdkrw.change)} style={{ fontWeight: 500 }}>
                {formatChange(marketData.usdkrw.change.toFixed(2))} ({formatChange(marketData.usdkrw.change_rate.toFixed(2))}%)
              </span>
            </div>
          </div>
        </div>
        {/* 국채 3년 */}
        <div className="market-index-card">
          <div className="card-header">
            <h3 className="card-title"><i className="fas fa-file-invoice-dollar"></i> 국채 3년</h3>
            <div className={`card-status-icon ${getChangeClass(marketData.bond3y_info.change)}`}>
              <i className={`fas fa-caret-${marketData.bond3y_info.change > 0 ? "up" : "down"}`}></i>
            </div>
          </div>
          <div className="market-index-content">
            <div style={{ display: "flex", flexDirection: "column" }}>
              <span style={{ fontSize: "1.8rem", fontWeight: 700 }}>
                {marketData.bond3y_info.today}%
              </span>
              <span className={getChangeClass(marketData.bond3y_info.change)} style={{ fontWeight: 500 }}>
                {formatChange(marketData.bond3y_info.change.toFixed(2))}%p
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  };

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

      {/* 메인 대시보드 */}
      <div className="main-dashboard-content">
        <div className="main-dashboard-header">
          <h1 className="page-title">메인 대시보드</h1>
          <div>
            <Navbar />
          </div>
        </div>

        {/* 시장 지수 섹션 */}
        {renderMarketIndexGrid()}

        {/* 투자 종목 및 특이 종목 */}
        <div className="stock-section-container">
          {/* 오늘의 투자 추천 종목 */}
          <div className="stock-column">
            <div className="stock-recommend-card">
              <div className="stock-card-header">
                <i className="fas fa-star"></i>
                <h2 className="stock-card-title">오늘의 투자 추천 종목</h2>
              </div>
              {/* 삼성전자 */}
              <div className="stock-item-row">
                <div className="stock-item-header">
                  <div>
                    <div className="stock-name">삼성전자</div>
                    <div className="stock-code">005930</div>
                  </div>
                  <div className="stock-price-container">
                    <div className="stock-price">74,500원</div>
                    <div className="stock-change change-positive">+1.2%</div>
                  </div>
                </div>
                <div className="consensus-bar-container">
                  <div className="consensus-label">
                    <span>컨센서스 강도</span>
                    <span>매수 (92%)</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-bar-fill" data-width="92%" />
                  </div>
                </div>
              </div>
              {/* SK하이닉스 */}
              <div className="stock-item-row">
                <div className="stock-item-header">
                  <div>
                    <div className="stock-name">SK하이닉스</div>
                    <div className="stock-code">000660</div>
                  </div>
                  <div className="stock-price-container">
                    <div className="stock-price">168,500원</div>
                    <div className="stock-change change-positive">+2.8%</div>
                  </div>
                </div>
                <div className="consensus-bar-container">
                  <div className="consensus-label">
                    <span>컨센서스 강도</span>
                    <span>강력매수 (95%)</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-bar-fill" data-width="95%" />
                  </div>
                </div>
              </div>
              {/* NAVER */}
              <div className="stock-item-row">
                <div className="stock-item-header">
                  <div>
                    <div className="stock-name">NAVER</div>
                    <div className="stock-code">035420</div>
                  </div>
                  <div className="stock-price-container">
                    <div className="stock-price">187,000원</div>
                    <div className="stock-change change-negative">-0.5%</div>
                  </div>
                </div>
                <div className="consensus-bar-container">
                  <div className="consensus-label">
                    <span>컨센서스 강도</span>
                    <span>매수 (87%)</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-bar-fill" data-width="87%" />
                  </div>
                </div>
              </div>
              {/* 현대차 */}
              <div className="stock-item-row">
                <div className="stock-item-header">
                  <div>
                    <div className="stock-name">현대차</div>
                    <div className="stock-code">005380</div>
                  </div>
                  <div className="stock-price-container">
                    <div className="stock-price">228,500원</div>
                    <div className="stock-change change-positive">+1.8%</div>
                  </div>
                </div>
                <div className="consensus-bar-container">
                  <div className="consensus-label">
                    <span>컨센서스 강도</span>
                    <span>매수 (85%)</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-bar-fill" data-width="85%" />
                  </div>
                </div>
              </div>
            </div>
          </div>
          {/* 오늘의 특이 종목 */}
          <div className="stock-column">
            <div className="stock-alert-card">
              <div className="stock-card-header">
                <i className="fas fa-exclamation-circle"></i>
                <h2 className="stock-card-title">오늘의 특이 종목</h2>
              </div>
              {/* LG에너지솔루션 */}
              <div className="stock-item-row">
                <div className="stock-item-header">
                  <div>
                    <div className="stock-name">LG에너지솔루션</div>
                    <div className="stock-code">373220</div>
                  </div>
                  <div className="stock-price-container">
                    <div className="stock-price">385,000원</div>
                    <div className="stock-change change-positive">+4.7%</div>
                  </div>
                </div>
                <div className="stock-special-comment">
                  대규모 해외 수주 소식에 급등
                </div>
              </div>
              {/* 카카오 */}
              <div className="stock-item-row">
                <div className="stock-item-header">
                  <div>
                    <div className="stock-name">카카오</div>
                    <div className="stock-code">035720</div>
                  </div>
                  <div className="stock-price-container">
                    <div className="stock-price">46,850원</div>
                    <div className="stock-change change-negative">-5.2%</div>
                  </div>
                </div>
                <div className="stock-special-comment">
                  실적 발표 후 시장 예상치 하회로 급락
                </div>
              </div>
              {/* 셀트리온 */}
              <div className="stock-item-row">
                <div className="stock-item-header">
                  <div>
                    <div className="stock-name">셀트리온</div>
                    <div className="stock-code">068270</div>
                  </div>
                  <div className="stock-price-container">
                    <div className="stock-price">168,500원</div>
                    <div className="stock-change change-positive">+3.5%</div>
                  </div>
                </div>
                <div className="stock-special-comment">
                  신약 FDA 승인 소식으로 강세
                </div>
              </div>
              {/* 현대중공업 */}
              <div className="stock-item-row">
                <div className="stock-item-header">
                  <div>
                    <div className="stock-name">현대중공업</div>
                    <div className="stock-code">329180</div>
                  </div>
                  <div className="stock-price-container">
                    <div className="stock-price">115,000원</div>
                    <div className="stock-change change-positive">+6.2%</div>
                  </div>
                </div>
                <div className="stock-special-comment">
                  대규모 선박 수주 소식에 급등
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 시장 동향 및 주요 일정 */}
        <div className="summary-row">
          <div className="market-summary-section">
            <div className="card-header">
              <h3 className="card-title"><i className="fas fa-chart-bar"></i> 시장 동향 요약</h3>
              <div className="card-status-icon"><i className="fas fa-chart-pie"></i></div>
            </div>
            <div className="market-summary-charts">
              {/* 주요 지수 차트 */}
              <div>
                <h4 className="subchart-title">주요 지수 추이</h4>
                <div className="market-summary-canvas-container">
                </div>
              </div>
              {/* 투자자/업종 차트(두 개의 차트 나란히) */}
              <div className="subcharts-row">
                <div className="subchart-box">
                  <h4 className="subchart-title">투자자별 순매수 (단위: 억원)</h4>
                  <div className="subchart-canvas-container">
                  </div>
                </div>
                <div className="subchart-box">
                  <h4 className="subchart-title">업종별 등락률 (%)</h4>
                  <div className="subchart-canvas-container">
                  </div>
                </div>
              </div>
              <div style={{ fontSize: "0.95rem", lineHeight: 1.5 }}>
                <p>오늘 국내 증시는 미국 증시의 상승 영향과 IT 업종의 호실적 전망으로 상승 마감했습니다. 코스피는 전일 대비 0.82% 상승한 2,654.31포인트로 마감했으며, 코스닥은 0.37% 하락한 892.15로 마감했습니다.</p>
                <p style={{ marginTop: 8 }}>외국인과 기관이 각각 1,234억원, 895억원 순매수를 기록했으며, 개인은 2,129억원 순매도했습니다. 업종별로는 IT 하드웨어(+2.3%), 에너지(+1.8%), 바이오(+1.5%) 업종이 강세를 보였습니다.</p>
              </div>
            </div>
          </div>
          <div className="market-index-card">
            <div className="card-header">
              <h3 className="card-title"><i className="fas fa-calendar-alt"></i> 오늘의 주요 일정</h3>
              <div className="card-status-icon"><i className="fas fa-calendar-check"></i></div>
            </div>
            <div>
              <div className="schedule-entry">
                <div className="schedule-time">09:00</div>
                <div className="schedule-event">한국 4월 무역수지 발표</div>
                <div className="event-source">한국은행</div>
              </div>
              <div className="schedule-entry">
                <div className="schedule-time">10:30</div>
                <div className="schedule-event">삼성전자 실적 컨퍼런스콜</div>
                <div className="event-source">삼성전자</div>
              </div>
              <div className="schedule-entry">
                <div className="schedule-time">14:00</div>
                <div className="schedule-event">한국은행 금융통화위원회</div>
                <div className="event-source">한국은행</div>
              </div>
              <div className="schedule-entry">
                <div className="schedule-time">15:30</div>
                <div className="schedule-event">SK하이닉스 IR 미팅</div>
                <div className="event-source">SK하이닉스</div>
              </div>
              <div className="schedule-entry">
                <div className="schedule-time">21:30</div>
                <div className="schedule-event">미국 4월 고용보고서</div>
                <div className="event-source">미국 노동부</div>
              </div>
            </div>
          </div>
        </div>

        {/* 산업별 투자 전망 및 경제 지표 */}
        <div className="indicator-section-wrapper">
          {/* 산업별 투자 전망 */}
          <div className="indicator-section">
            <div className="indicator-header">
              <i className="fas fa-industry"></i>
              <h2 className="indicator-title">산업별 투자 전망</h2>
            </div>
            <table className="sector-table">
              <thead>
                <tr>
                  <th>산업 분야</th>
                  <th>전망</th>
                  <th>컨센서스</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>반도체</td>
                  <td className="positive">긍정적</td>
                  <td>
                    <div className="consensus-bar">
                      <div className="consensus-bar-fill" style={{ width: "90%" }} />
                    </div>
                  </td>
                </tr>
                <tr>
                  <td>자동차</td>
                  <td className="positive">긍정적</td>
                  <td>
                    <div className="consensus-bar">
                      <div className="consensus-bar-fill" style={{ width: "85%" }} />
                    </div>
                  </td>
                </tr>
                <tr>
                  <td>바이오</td>
                  <td className="neutral">중립</td>
                  <td>
                    <div className="consensus-bar">
                      <div className="consensus-bar-fill" style={{ width: "65%" }} />
                    </div>
                  </td>
                </tr>
                <tr>
                  <td>배터리</td>
                  <td className="positive">긍정적</td>
                  <td>
                    <div className="consensus-bar">
                      <div className="consensus-bar-fill" style={{ width: "88%" }} />
                    </div>
                  </td>
                </tr>
                <tr>
                  <td>소프트웨어</td>
                  <td className="positive">긍정적</td>
                  <td>
                    <div className="consensus-bar">
                      <div className="consensus-bar-fill" style={{ width: "80%" }} />
                    </div>
                  </td>
                </tr>
                <tr>
                  <td>화학</td>
                  <td className="negative">부정적</td>
                  <td>
                    <div className="consensus-bar">
                      <div className="consensus-bar-fill" style={{ width: "40%" }} />
                    </div>
                  </td>
                </tr>
                <tr>
                  <td>유통</td>
                  <td className="neutral">중립</td>
                  <td>
                    <div className="consensus-bar">
                      <div className="consensus-bar-fill" style={{ width: "60%" }} />
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          {/* 주요 경제 지표 */}
          <div className="indicator-section">
            <div className="indicator-header">
              <i className="fas fa-balance-scale"></i>
              <h2 className="indicator-title">주요 경제 지표</h2>
            </div>
            <table className="economic-table">
              <thead>
                <tr>
                  <th>지표</th>
                  <th>수치</th>
                  <th>변동</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>국채 3년물</td>
                  <td>3.52%</td>
                  <td className="positive">+0.03%p</td>
                </tr>
                <tr>
                  <td>국채 10년물</td>
                  <td>3.64%</td>
                  <td className="positive">+0.02%p</td>
                </tr>
                <tr>
                  <td>원자재 (WTI)</td>
                  <td>$82.47</td>
                  <td className="negative">-1.3%</td>
                </tr>
                <tr>
                  <td>금</td>
                  <td>$2,045.60</td>
                  <td className="positive">+0.8%</td>
                </tr>
                <tr>
                  <td>달러 인덱스</td>
                  <td>104.82</td>
                  <td className="positive">+0.4%</td>
                </tr>
                <tr>
                  <td>외국인 순매수</td>
                  <td>2,487억원</td>
                  <td className="positive">매수세</td>
                </tr>
                <tr>
                  <td>기관 순매수</td>
                  <td>-1,358억원</td>
                  <td className="negative">매도세</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default IndexPage;
