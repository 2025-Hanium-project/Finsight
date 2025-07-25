// src/pages/DetailPage.jsx

import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import Menu from "../components/Menu";
import "../css/detail.css";
import StockCandleChart from "../components/StockCandleChart";
function DetailPage() {
  const { stockCode } = useParams();

  // API에서 받아올 상태
  const [latest, setLatest] = useState(null);
  const [ohlcv, setOhlcv]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [stockName, setStockName] = useState("");

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        // 추후 endpoint URL을 환경변수로 관리하는 것이 좋아보임.
        const res = await fetch(`http://localhost:5000/api/direct/${stockCode}/ohlcv`);
        if (!res.ok) throw new Error(res.statusText);
        const data = await res.json();
        
        setOhlcv(data.ohlcv);
        setStockName(data.stock_name);
        if (data.ohlcv.length > 0) {
          setLatest(data.ohlcv[data.ohlcv.length - 1]);
        }
      } catch (e) {
        console.error("데이터 로드 실패:", e);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [stockCode]);

  if (loading) {
    return <div className="container">로딩 중...</div>;
  }
  if (!latest) {
    return <div className="container">데이터가 없습니다.</div>;
  }
  // 날짜 포맷
  const formattedDate = new Date(latest.date).toLocaleDateString("ko-KR", {
    year: "numeric", month: "long", day: "numeric", weekday: "long"
  });
  const previous = ohlcv.length > 1
    ? ohlcv[ohlcv.length - 2]
    : null;
  // 변화량 계산
  const diff = previous
    ? latest.close - previous.close
    : 0;
  const diffPct = latest.open > 0
    ? (diff / previous.close * 100).toFixed(2)
    : "0.00";

  return (
    <div className="container">
      {/* 사이드바 */}
      <div className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <span className="logo-icon">📊</span>
            <span>FinSight</span>
          </div>
        </div>
        <Menu />
      </div>

      {/* 메인 콘텐츠 */}
      <div className="main-content">
        {/* 헤더 */}
        <div className="header">
          <div>
            <h1 className="header-title">종목 상세 정보</h1>
            <p className="date-info">{formattedDate}</p>
          </div>
        </div>

        {/* 검색 영역 (하드코딩 유지) */}
        <div className="search-container">
          <input
            type="text"
            className="search-input"
            placeholder="종목명 또는 종목코드 검색"
            defaultValue="삼성전자"
          />
          <button className="search-button">검색</button>
        </div>

        {/* 종목 헤더 (동적) */}
        <div className="stock-summary-header">
          <div className="stock-symbol">
            {stockCode.charAt(0)}
          </div>
          <div className="stock-brief">
            <h2 className="stock-name-detail">{stockName}</h2>
            <p className="stock-code-detail">{stockCode}</p>
            <div className="price-summary">
              <span className="current-price">
                {latest.close.toLocaleString()}원
              </span>
              <span
                className={`price-change ${diff >= 0 ? "up" : "down"}`}
              >
                {(diff >= 0 ? "+" : "") + diff.toLocaleString()}원 (
                { (diff >= 0 ? "+" : "") + diffPct }%)
              </span>
            </div>
            <div className="price-metrics">
              {[
                ["시가", latest.open],
                ["고가", latest.high],
                ["저가", latest.low],
                ["거래량", latest.volume],
                ["시가총액", latest.market_cap]
              ].map(([label, val]) => (
                <div className="price-metric-item" key={label}>
                  <div className="metric-label">{label}</div>
                  <div className="metric-value">
                    {val != null
                      ? label === "거래량"
                        ? `${val.toLocaleString()}주`
                        : `${val.toLocaleString()}원`
                      : "-"}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 차트 영역 (동적 - placeholder) */}
        <div className="info-card full-span">
          <div className="time-tab-nav">
            <div className="tab active">일별</div>
            <div className="tab">주별</div>
            <div className="tab">월별</div>
            <div className="tab">3개월</div>
            <div className="tab">1년</div>
            <div className="tab">3년</div>
          </div>
+        <div className="chart-box-detail">
+          {/* StockChart 에 전체 ohlcv 또는 원하는 slice만 넘겨주세요 */}
+          <StockCandleChart data={ohlcv.slice(-30)} />
+        </div>
        </div>

        {/* 이하 하드코딩된 정보들은 그대로 유지 */}
        {/* 기업 개요 */}
        <div className="stock-insights-grid">
          <div className="info-card">
            <div className="item-header">
              <h3 className="item-title">기업 개요</h3>
              <div className="item-icon">🏢</div>
            </div>
            {/* ... 이하 생략 없이 그대로 */}
            <p className="info-desc mb-15">
              삼성전자는 반도체, 휴대폰, 가전제품 등을 생산하는 대한민국 최대 기업으로, 세계적인 전자 기업입니다. 메모리 반도체 시장에서 글로벌 1위를 차지하고 있으며, 스마트폰, TV 등 다양한 제품군에서 시장을 선도하고 있습니다.
            </p>
            <div className="info-row info-row-top">
              <span>업종</span>
              <span style={{ fontWeight: 500 }}>전기전자</span>
            </div>
            <div className="info-row info-row-margin">
              <span>설립일</span>
              <span style={{ fontWeight: 500 }}>1969년 1월</span>
            </div>
            <div className="info-row info-row-margin">
              <span>대표이사</span>
              <span style={{ fontWeight: 500 }}>경계현, 한종희</span>
            </div>
          </div>

          {/* 투자 지표 */}
          <div className="info-card">
            <div className="item-header">
              <h3 className="item-title">투자 지표</h3>
              <div className="item-icon">📈</div>
            </div>
            <div className="key-metrics">
              <div className="metric-item">
                <div className="metric-label">PER</div>
                <div className="metric-value">16.2배</div>
              </div>
              <div className="metric-item">
                <div className="metric-label">PBR</div>
                <div className="metric-value">1.4배</div>
              </div>
              <div className="metric-item">
                <div className="metric-label">ROE</div>
                <div className="metric-value">8.7%</div>
              </div>
              <div className="metric-item">
                <div className="metric-label">배당수익률</div>
                <div className="metric-value">2.3%</div>
              </div>
              <div className="metric-item">
                <div className="metric-label">베타</div>
                <div className="metric-value">0.95</div>
              </div>
              <div className="metric-item">
                <div className="metric-label">EPS</div>
                <div className="metric-value">4,681원</div>
              </div>
            </div>
          </div>

          {/* 컨센서스 정보 */}
          <div className="info-card">
            <div className="item-header">
              <h3 className="item-title">컨센서스 정보</h3>
              <div className="item-icon">🎯</div>
            </div>
            {/* ... 이하 동일 */}
            <div className="consensus-header mb-15">
              <div>
                <div className="consensus-label">평균 목표가</div>
                <div className="consensus-value">85,000원</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div className="consensus-label">상승여력</div>
                <div className="consensus-value up">+12.1%</div>
              </div>
            </div>
            {/* ... 나머지 하드코딩 내용 계속 */}
          </div>
        </div>

        {/* 이하 리포트 요약, LLM 요약, 재무 정보 등 전부 그대로 유지 */}
      </div>
    </div>
  );
}

export default DetailPage;
