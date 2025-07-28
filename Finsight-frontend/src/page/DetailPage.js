// src/pages/DetailPage.jsx

import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Menu from "../components/Menu";
import "../css/detail.css";
import StockCandleChart from "../components/StockCandleChart";
function DetailPage() {
  const { stockCode } = useParams();
  const [searchValue, setSearchValue] = useState("");
  const navigate = useNavigate();

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
        const res = await fetch(`/api/direct/${stockCode}/ohlcv`);
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
    return <div className="container"></div>;
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
            value={searchValue}
            onChange={e => setSearchValue(e.target.value)}
          />
          <button
            className="search-button"
            onClick={async () => {
              const value = searchValue.trim();
              if (!value) return;
              let code = value;
              // 숫자가 아니면 종목명으로 간주
              if (isNaN(Number(value))) {
                try {
                  const res = await fetch(`/api/stocks/name/${encodeURIComponent(value)}`);
                  if (res.ok) {
                    const data = await res.json();
                    if (data.stock_code) {
                      code = data.stock_code;
                    } else {
                      alert('종목명을 찾을 수 없습니다.');
                      return;
                    }
                  } else {
                    alert('종목명을 찾을 수 없습니다.');
                    return;
                  }
                } catch (e) {
                  alert('종목명 변환 중 오류가 발생했습니다.');
                  return;
                }
              }
              navigate(`/detail/${code}`);
            }}
          >
            검색
          </button>
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
            <div
            className="consensus-header mb-15"
            >
              <div>
                <div className="consensus-label">평균 목표가</div>
                <div className="consensus-value">85,000원</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div className="consensus-label">상승여력</div>
                <div className="consensus-value up">+12.1%</div>
              </div>
            </div>
            <div style={{ marginBottom: 15 }}>
            <div className="consensus-row">
                <span>매수</span>
                <span>18개</span>
              </div>
              <div className="consensus-bar">
                <div className="consensus-fill progress-success" style={{ width: "76%" }} />
              </div>
            </div>
            <div style={{ marginBottom: 15 }}>
            <div className="consensus-row">
                <span>중립</span>
                <span>5개</span>
              </div>
              <div className="consensus-bar">
                <div className="consensus-fill progress-warning" style={{ width: "20%" }} />
              </div>
            </div>
            <div>
            <div className="consensus-row">
                <span>매도</span>
                <span>1개</span>
              </div>
              <div className="consensus-bar">
                <div className="consensus-fill progress-danger" style={{ width: "4%" }} />
              </div>
            </div>
          </div>
        </div>

        {/* 리포트 및 컨센서스 영역 */}
        <div className="report-and-summary-row">
          {/* 애널리스트 리포트 요약 */}
          <div className="info-card">
            <div className="item-header">
              <h3 className="item-title">애널리스트 리포트 요약</h3>
              <div className="item-icon">📝</div>
            </div>
            <div className="time-tab-nav">
              <div className="tab active">최근 1주일</div>
              <div className="tab">최근 1개월</div>
              <div className="tab">최근 3개월</div>
            </div>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>날짜</th>
                    <th>증권사</th>
                    <th>투자의견</th>
                    <th>목표가</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>2025.05.03</td>
                    <td>미래증권</td>
                    <td>
                      <span className="badge badge-success">매수</span>
                    </td>
                    <td>85,000원 (+5,000원)</td>
                  </tr>
                  <tr>
                    <td>2025.05.02</td>
                    <td>한국증권</td>
                    <td>
                      <span className="badge badge-success">매수</span>
                    </td>
                    <td>88,000원 (유지)</td>
                  </tr>
                  <tr>
                    <td>2025.04.30</td>
                    <td>글로벌증권</td>
                    <td>
                      <span className="badge badge-warning">중립</span>
                    </td>
                    <td>78,000원 (-2,000원)</td>
                  </tr>
                  <tr>
                    <td>2025.04.29</td>
                    <td>대한증권</td>
                    <td>
                      <span className="badge badge-success">매수</span>
                    </td>
                    <td>86,000원 (+3,000원)</td>
                  </tr>
                  <tr>
                    <td>2025.04.28</td>
                    <td>신한증권</td>
                    <td>
                      <span className="badge badge-success">매수</span>
                    </td>
                    <td>90,000원 (유지)</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* LLM 기반 투자 요약 */}
          <div className="info-card">
            <div className="item-header">
              <h3 className="item-title">LLM 기반 투자 요약</h3>
              <div className="item-icon">🤖</div>
            </div>
            <div className="llm-summary-box">
              <p style={{ fontWeight: 600, marginBottom: 10 }}>투자 포인트</p>
              <p style={{ marginBottom: 15 }}>
                메모리 반도체 시장의 수급 개선과 가격 상승세가 지속되고 있으며, AI 관련 HBM 수요 급증으로 인한 수익성 개선이 기대됩니다. 파운드리 사업의 고객사 다변화와 선단공정 기술 경쟁력 강화로 시스템 반도체 부문의 성장세가 가속화되고 있습니다.
              </p>
              <p style={{ fontWeight: 600, marginBottom: 10 }}>리스크 요인</p>
              <p style={{ marginBottom: 15 }}>
                글로벌 경기 둔화로 인한 IT 기기 수요 감소 가능성과 미중 무역 갈등으로 인한 지정학적 리스크가 존재합니다. 경쟁사의 기술 추격과 대규모 설비투자로 인한 수급 악화 가능성도 주의가 필요합니다.
              </p>
              <p style={{ fontWeight: 600, marginBottom: 10 }}>종합 의견</p>
              <p>
                반도체 시장의 본격적인 회복세와 AI 관련 수요 증가로 인한 실적 개선이 예상되며, 합리적인 밸류에이션 수준을 고려했을 때 투자매력도가 높습니다. 중장기 투자 관점에서 매수 추천합니다.
              </p>
            </div>
          </div>
        </div>

        {/* 실적 및 재무 정보 */}
        <div className="info-card full-span">
          <div className="item-header">
            <h3 className="item-title">실적 및 재무 정보</h3>
            <div className="item-icon">📊</div>
          </div>
          <div className="time-tab-nav">
            <div className="tab active">분기별</div>
            <div className="tab">연간</div>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>항목</th>
                  <th>2024.1Q</th>
                  <th>2024.2Q</th>
                  <th>2024.3Q</th>
                  <th>2024.4Q</th>
                  <th>2025.1Q</th>
                  <th>YoY</th>
                  <th>QoQ</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>매출액</td>
                  <td>67.8조원</td>
                  <td>71.2조원</td>
                  <td>73.5조원</td>
                  <td>76.1조원</td>
                  <td>78.3조원</td>
                  <td className="up">+15.5%</td>
                  <td className="up">+2.9%</td>
                </tr>
                <tr>
                  <td>영업이익</td>
                  <td>6.2조원</td>
                  <td>8.7조원</td>
                  <td>11.3조원</td>
                  <td>13.5조원</td>
                  <td>14.8조원</td>
                  <td className="up">+138.7%</td>
                  <td className="up">+9.6%</td>
                </tr>
                <tr>
                  <td>영업이익률</td>
                  <td>9.1%</td>
                  <td>12.2%</td>
                  <td>15.4%</td>
                  <td>17.7%</td>
                  <td>18.9%</td>
                  <td className="up">+9.8%p</td>
                  <td className="up">+1.2%p</td>
                </tr>
                <tr>
                  <td>당기순이익</td>
                  <td>4.9조원</td>
                  <td>7.1조원</td>
                  <td>9.2조원</td>
                  <td>10.8조원</td>
                  <td>11.5조원</td>
                  <td className="up">+134.7%</td>
                  <td className="up">+6.5%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* 목표가 및 실적 예상 */}
        <div className="report-and-summary-row">
          {/* 목표가 근접 여부 분석 */}
          <div className="info-card">
            <div className="item-header">
              <h3 className="item-title">목표가 근접 여부 분석</h3>
              <div className="item-icon">📍</div>
            </div>
            <div className="chart-box-detail">
              <div className="chart-placeholder">
                목표가 추이 및 근접도 차트
              </div>
            </div>
            <div className="info-desc info-desc-margin">
              <p>
                현재 평균 목표가인 85,000원 대비 현재가는 75,800원으로, 목표가 달성 근접률은 89.2%입니다. 최근 3개월간 목표가는 평균 12.3% 상향 조정되었으며, 주가는 평균 목표가를 향해 상승 추세를 보이고 있습니다.
              </p>
              <p className="info-desc info-desc-margin">
                목표가 상단은 90,000원(신한증권), 하단은 78,000원(글로벌증권)으로 목표가 컨센서스의 범위는 12,000원입니다.
              </p>
            </div>
          </div>
          {/* 종목 실적 예상 */}
          <div className="info-card">
            <div className="item-header">
              <h3 className="item-title">종목 실적 예상</h3>
              <div className="item-icon">🔮</div>
            </div>
            <div style={{ marginBottom: 15 }}>
            <div className="metric-label-small">2025년 2분기 예상 매출액</div>
            <div className="metric-row">
              <span className="metric-value-large">82.5조원</span>
              <span className="metric-value-up">+15.9% YoY</span>
              </div>
            </div>
            <div style={{ marginBottom: 15 }}>
            <div className="metric-label-small">2025년 2분기 예상 영업이익</div>
            <div className="metric-row">
              <span className="metric-value-large">16.2조원</span>
              <span className="metric-value-up">+86.2% YoY</span>
              </div>
            </div>
            <div className="info-desc info-desc-margin-large">
              <p>
                반도체 부문의 수익성 개선과 메모리 가격 상승이 지속될 것으로 예상되며, AI 관련 HBM 메모리 수요 증가로 인한 실적 개선 효과가 본격화될 전망입니다.
              </p>
            </div>
          </div>
        </div>

        {/* 감성 분석 */}
        <div className="info-card full-span">
          <div className="item-header">
            <h3 className="item-title">시장 심리 및 감성 분석</h3>
            <div className="item-icon">🧠</div>
          </div>
          <div className="sentiment-row">
            <div style={{ flex: 1 }}>
              <div className="chart-box-detail">
                <div className="chart-placeholder">감성 분석 차트</div>
              </div>
            </div>
            <div className="sentiment-summary-text">
              <p className="mb-15">
                최근 1개월간 삼성전자 관련 뉴스, 소셜 미디어, 투자자 게시판 등에서 추출한 감성 분석 결과, 긍정적 심리가 68.5%로 부정적 심리(15.3%)보다 우세한 상황입니다.
              </p>
              <p className="mb-15">
                특히 반도체 업황 회복과 AI 관련 성장성에 대한 긍정적 기대감이 높게 형성되어 있으며, 최근 4분기 연속 실적 개선으로 투자 심리가 강화되고 있습니다.
              </p>
              <p>
                단기적으로는 시장 심리가 매우 낙관적이나, 과도한 기대감으로 인한 단기 조정 가능성에 대한 주의가 필요합니다.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DetailPage;
