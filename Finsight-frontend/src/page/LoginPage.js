// src/page/LoginPage.js

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../css/login.css'; 

function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);

  // 로그인 버튼 클릭 시 처리 함수
  const handleLogin = (e) => {
    e.preventDefault();
    // 실제 로그인 로직(서버 통신) 추가 필요!
    // 성공 시 메인 대시보드로 이동
    navigate('/');
  };

  return (
    <div className="login-container" >
      {/* 왼쪽 로그인 영역 */}
      <div className="login-side">
        <div className="login-logo">
          <span className="login-logo-icon">📊</span>
          <span className="login-logo-text">FinSight</span>
        </div>
        <p className="login-subtitle">투자 의사결정을 위한 AI 분석 플랫폼</p>

        <h1 className="login-title">로그인</h1>

        <form onSubmit={handleLogin}>
          <div className="input-field">
            <label htmlFor="email">이메일</label>
            <input
              type="email"
              id="email"
              placeholder="이메일 주소를 입력하세요"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="input-field">
            <label htmlFor="password">비밀번호</label>
            <input
              type="password"
              id="password"
              placeholder="비밀번호를 입력하세요"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="password-options">
            <div className="remember-me">
              <input
                type="checkbox"
                id="remember"
                checked={remember}
                onChange={() => setRemember(!remember)}
              />
              <label htmlFor="remember">로그인 상태 유지</label>
            </div>
            <a href="#" className="forgot-link" onClick={(e) => {e.preventDefault(); navigate('/findpwd')}}>
              비밀번호 찾기
            </a>
          </div>

          <button type="submit" className="login-button">로그인</button>
        </form>

        <div className="login-divider">
          <span>또는</span>
        </div>

        <div className="social-login">
          <button className="social-button kakao-login" type="button">
            <span className="social-icon">K</span>
            카카오 계정으로 로그인
          </button>
          <button className="social-button naver-login" type="button">
            <span className="social-icon">N</span>
            네이버 계정으로 로그인
          </button>
        </div>

        <div className="signup-link">
          <p>계정이 없으신가요?{' '}
            <a href="#" onClick={(e) => {e.preventDefault(); navigate('/signup')}}>
              회원가입
            </a>
          </p>
        </div>

        <div className="copyright">
          <p>© 2025 FinSight. All rights reserved.</p>
        </div>
      </div>

      {/* 오른쪽 소개 영역 */}
      <div className="showcase-side">
        <div className="showcase-content">
          <h2 className="showcase-title">
            AI 기반 투자 분석으로<br />더 나은 투자 결정을
          </h2>
          <p className="showcase-description">
            실시간 종목 분석, 맞춤형 투자 전략, 최신 시장 동향까지<br />
            투자 애널리스트 AI와 함께 시작하세요.
          </p>
          <div className="feature-list">
            <div className="feature-item">
              <div className="feature-icon">📈</div>
              <div className="feature-text">실시간 종목 분석</div>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🤖</div>
              <div className="feature-text">LLM 기반 투자 추천</div>
            </div>
            <div className="feature-item">
              <div className="feature-icon">📊</div>
              <div className="feature-text">포트폴리오 최적화</div>
            </div>
          </div>
        </div>
        <div className="preview-area">
          <div className="preview-image">
            <div className="chart-box"></div>
            <div className="data-box">
              <div className="data-line"></div>
              <div className="data-line"></div>
              <div className="data-line"></div>
              <div className="data-line"></div>
              <div className="data-line"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
