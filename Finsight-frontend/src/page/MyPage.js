import React, { useState } from "react";
import { useNavigate } from 'react-router-dom';
import Menu from "../components/Menu";   
import "../css/mypage.css";

const DEFAULT_WATCHLIST = [
  {
    name: "삼성전자", code: "005930", price: "75,800원", change: "+1,600원 (+2.16%)", up: true,
    target: "85,000원", potential: "+12.1%", consensus: 92, consensusText: "매수 92%", alert: false,
  },
  {
    name: "SK하이닉스", code: "000660", price: "169,500원", change: "+3,000원 (+1.77%)", up: true,
    target: "200,000원", potential: "+18.0%", consensus: 95, consensusText: "강력매수 95%", alert: true,
  },
  {
    name: "네이버", code: "035420", price: "280,500원", change: "+14,600원 (+5.20%)", up: true,
    target: "320,000원", potential: "+14.1%", consensus: 87, consensusText: "매수 87%", alert: false,
  },
  {
    name: "KB금융", code: "105560", price: "72,400원", change: "-800원 (-1.09%)", up: false,
    target: "78,000원", potential: "+7.7%", consensus: 75, consensusText: "매수 75%", alert: false,
  },
  {
    name: "현대차", code: "005380", price: "196,000원", change: "-1,000원 (-0.51%)", up: false,
    target: "210,000원", potential: "+7.1%", consensus: 85, consensusText: "매수 85%", alert: false,
  },
  {
    name: "셀트리온", code: "068270", price: "189,000원", change: "+6,600원 (+3.61%)", up: true,
    target: "220,000원", potential: "+16.4%", consensus: 78, consensusText: "매수 78%", alert: true,
  },
];

const DEFAULT_PROFILE = {
  name: "김투자",
  email: "investor@example.com",
  joined: "2024.03.15",
};

const DEFAULT_SETTINGS = {
  risk: "moderate",
  amount: "medium",
  industries: ["IT/기술", "금융", "자동차"],
  allIndustries: ["IT/기술", "금융", "바이오", "자동차", "에너지", "소비재"],
  notification: {
    price: true,
    result: true,
    report: false,
    market: true,
  },
};

function Mypage() {
  const [watchlist, setWatchlist] = useState(DEFAULT_WATCHLIST);
  const [sort, setSort] = useState("name");
  const [view, setView] = useState("grid");
  const [profile] = useState(DEFAULT_PROFILE);
  const [risk, setRisk] = useState(DEFAULT_SETTINGS.risk);
  const [amount, setAmount] = useState(DEFAULT_SETTINGS.amount);
  const [industries, setIndustries] = useState(DEFAULT_SETTINGS.industries);
  const [notification, setNotification] = useState(DEFAULT_SETTINGS.notification);

  const navigate = useNavigate();

  // 관심 종목 추가 (더미)
  const handleAddStock = () => {
    if (watchlist.length >= 6) {
      alert("관심 종목은 최대 6개까지만 등록할 수 있습니다.");
      return;
    }
    alert("종목 추가 기능은 추후 구현됩니다.");
  };

  // 관심 종목 제거
  const handleRemoveStock = (idx) => {
    if (window.confirm("이 종목을 관심 목록에서 제거하시겠습니까?")) {
      setWatchlist((prev) => prev.filter((_, i) => i !== idx));
    }
  };

  // 알림 설정 토글
  const handleAlertToggle = (idx) => {
    setWatchlist((prev) =>
      prev.map((item, i) => i === idx ? { ...item, alert: !item.alert } : item)
    );
  };

  // 업종 태그 토글
  const handleTagToggle = (tag) => {
    setIndustries((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  // 정렬 기준
  const handleSort = (e) => {
    setSort(e.target.value);
    // 실제 정렬은 서버/DB 연동 시 추가
  };

  // 보기 방식
  const handleView = (v) => setView(v);

  // 알림 설정
  const handleNotificationToggle = (key) => {
    setNotification((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // 투자 설정 (리스크, 금액)
  const handleRiskChange = (e) => setRisk(e.target.value);
  const handleAmountChange = (e) => setAmount(e.target.value);

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
      <div className="mypage-content">
        {/* 헤더 */}
        <div className="mypage-header">
          <div>
            <h1 className="mypage-title">마이페이지</h1>
            <p className="date-info">{new Date().toLocaleDateString("ko-KR", { year: "numeric", month: "long", day: "numeric", weekday: "long" })}</p>
          </div>
          <div className="header-actions"></div>
        </div>
        {/* 프로필 섹션 */}
        <div className="profile-section">
          <div className="profile-card">
            <div className="profile-avatar">
              <span className="avatar-initial">{profile.name[0]}</span>
            </div>
            <div className="profile-info">
              <h2 className="profile-name">{profile.name}</h2>
              <p className="profile-email">{profile.email}</p>
              <div className="profile-stats">
                <div className="stat-item">
                  <div className="stat-label">관심 종목</div>
                  <div className="stat-value">{watchlist.length}개</div>
                </div>
                <div className="stat-item">
                  <div className="stat-label">가입일</div>
                  <div className="stat-value">{profile.joined}</div>
                </div>
              </div>
            </div>
            <div className="profile-actions">
              <button className="btn-edit-profile" onClick={() => navigate('/profileedit')}>프로필 수정</button>
            </div>
          </div>
        </div>
        {/* 관심 종목 섹션 */}
        <div className="mypage-section-title-with-action">
          <h2 className="mypage-section-title">관심 종목</h2>
          <button className="btn-add-watchlist" onClick={handleAddStock} disabled={watchlist.length >= 6}
            style={watchlist.length >= 6 ? { opacity: 0.5, cursor: "not-allowed" } : {}}>
            <i className="fas fa-plus"></i> 종목 추가
          </button>
        </div>
        <div className="watchlist-section">
          {/* 탭 */}
          <div className="watchlist-tabs">
            <div className="tab active">전체 ({watchlist.length})</div>
            <div className="watchlist-limit-info">
              <span className="limit-text">최대 6개까지 등록 가능</span>
              <span className="limit-count">{watchlist.length}/6</span>
            </div>
          </div>
          <div className="watchlist-content">
            {/* 툴바 */}
            <div className="watchlist-toolbar">
              <div className="toolbar-left">
                <select className="sort-select" value={sort} onChange={handleSort}>
                  <option value="name">종목명 순</option>
                  <option value="price">현재가 순</option>
                  <option value="change">변동률 순</option>
                  <option value="volume">거래량 순</option>
                </select>
                <button className={`view-toggle${view === "grid" ? " active" : ""}`} data-view="grid" onClick={() => handleView("grid")}>
                  <i className="fas fa-th"></i>
                </button>
                <button className={`view-toggle${view === "list" ? " active" : ""}`} data-view="list" onClick={() => handleView("list")}>
                  <i className="fas fa-list"></i>
                </button>
              </div>
              <div className="toolbar-right">
                <button className="btn-export" onClick={() => alert("내보내기 기능 구현 필요!")}>
                  <i className="fas fa-download"></i> 내보내기
                </button>
              </div>
            </div>
            {/* 관심 종목 그리드 */}
            <div className={`watchlist-grid ${view === "list" ? "list-view" : "grid-view"}`} id="watchlist-grid">
              {watchlist.map((stock, idx) => (
                <div className="watchlist-item" key={stock.code}>
                  <div className="watchlist-header">
                    <div className="watchlist-actions">
                      <button className={`btn-alert${stock.alert ? " active" : ""}`}
                        title="알림 설정"
                        onClick={() => handleAlertToggle(idx)}>
                        <i className="fas fa-bell"></i>
                      </button>
                      <button className="btn-remove" title="관심 종목에서 제거" onClick={() => handleRemoveStock(idx)}>
                        <i className="fas fa-heart-broken"></i>
                      </button>
                    </div>
                  </div>
                  <div className="stock-info-mp">
                    <h3 className="stock-name-mp">{stock.name}</h3>
                    <p className="stock-code-mp">{stock.code}</p>
                    <div className="price-info-mp">
                      <span className="current-price-mp">{stock.price}</span>
                      <span className={`price-change-mp ${stock.up ? "up" : "down"}`}>{stock.change}</span>
                    </div>
                  </div>
                  <div className="stock-metrics">
                    <div className="metric">
                      <span className="metric-label">목표가</span>
                      <span className="metric-value">{stock.target}</span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">상승여력</span>
                      <span className={`metric-value up`}>{stock.potential}</span>
                    </div>
                  </div>
                  <div className="consensus-info">
                    <div className="consensus-label">컨센서스</div>
                    <div className="consensus-bar">
                      <div className="consensus-fill" style={{ width: `${stock.consensus}%` }}></div>
                    </div>
                    <div className="consensus-text">{stock.consensusText}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        {/* 설정 섹션 */}
        <div className="settings-grid">
          {/* 투자 설정 */}
          <div className="settings-card">
            <div className="card-header">
              <h3 className="card-title">투자 설정</h3>
              <div className="card-icon">⚙️</div>
            </div>
            <div className="settings-content">
              <div className="setting-item">
                <div className="setting-info">
                  <div className="setting-label">투자 성향</div>
                  <div className="setting-description">투자 성향에 맞는 종목 추천을 받으세요</div>
                </div>
                <select className="setting-select" value={risk} onChange={handleRiskChange}>
                  <option value="conservative">보수적</option>
                  <option value="moderate">중도적</option>
                  <option value="aggressive">공격적</option>
                </select>
              </div>
              <div className="setting-item">
                <div className="setting-info">
                  <div className="setting-label">투자 금액 범위</div>
                  <div className="setting-description">목표 투자 금액을 설정하세요</div>
                </div>
                <select className="setting-select" value={amount} onChange={handleAmountChange}>
                  <option value="low">1천만원 이하</option>
                  <option value="medium">1천만원 - 5천만원</option>
                  <option value="high">5천만원 이상</option>
                </select>
              </div>
              <div className="setting-item">
                <div className="setting-info">
                  <div className="setting-label">관심 업종</div>
                  <div className="setting-description">선호하는 업종을 선택하세요</div>
                </div>
                <div className="industry-tags">
                  {DEFAULT_SETTINGS.allIndustries.map((tag) => (
                    <span
                      key={tag}
                      className={`tag${industries.includes(tag) ? " active" : ""}`}
                      onClick={() => handleTagToggle(tag)}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
          {/* 알림 설정 */}
          <div className="settings-card">
            <div className="card-header">
              <h3 className="card-title">알림 설정</h3>
              <div className="card-icon">🔔</div>
            </div>
            <div className="settings-content">
              <div className="notification-item">
                <div className="notification-info">
                  <div className="notification-label">가격 알림</div>
                  <div className="notification-description">목표가 도달 시 알림</div>
                </div>
                <label className="toggle-switch">
                  <input type="checkbox" checked={notification.price}
                    onChange={() => handleNotificationToggle("price")} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
              <div className="notification-item">
                <div className="notification-info">
                  <div className="notification-label">실적 발표</div>
                  <div className="notification-description">관심 종목 실적 발표일 알림</div>
                </div>
                <label className="toggle-switch">
                  <input type="checkbox" checked={notification.result}
                    onChange={() => handleNotificationToggle("result")} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
              <div className="notification-item">
                <div className="notification-info">
                  <div className="notification-label">리포트 업데이트</div>
                  <div className="notification-description">애널리스트 리포트 신규 발행 알림</div>
                </div>
                <label className="toggle-switch">
                  <input type="checkbox" checked={notification.report}
                    onChange={() => handleNotificationToggle("report")} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
              <div className="notification-item">
                <div className="notification-info">
                  <div className="notification-label">시장 동향</div>
                  <div className="notification-description">주요 시장 이슈 및 동향 알림</div>
                </div>
                <label className="toggle-switch">
                  <input type="checkbox" checked={notification.market}
                    onChange={() => handleNotificationToggle("market")} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>
          </div>
        </div>
        {/* (추가로 copyright 등 필요하면 삽입) */}
      </div>
    </div>
  );
}

export default Mypage;
