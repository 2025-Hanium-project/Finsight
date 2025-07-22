// src/components/Menu.js

import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../css/menu.css'; // 필요하다면 스타일 분리

function Menu() {
  const navigate = useNavigate();

  return (
    <nav className="sidebar">
      <div className="sidebar-nav-item">
        <i>📈</i>
        <button id="nav-dashboard" onClick={() => navigate('/dashboard')}>
          메인 대시보드
        </button>
      </div>
      <div className="sidebar-nav-item">
        <i>📝</i>
        <button id="nav-dday" onClick={() => navigate('/dday')}>
          D-day 보고서
        </button>
      </div>
      <div className="sidebar-nav-item">
        <i>📊</i>
        <button id="nav-dplus1" onClick={() => navigate('/dplus1')}>
          D+1 보고서
        </button>
      </div>
      <div className="sidebar-nav-item">
        <i>🔍</i>
        <button id="nav-detail" onClick={() => navigate('/detail')}>
          종목 상세 정보
        </button>
      </div>
    </nav>
  );
}

export default Menu;
