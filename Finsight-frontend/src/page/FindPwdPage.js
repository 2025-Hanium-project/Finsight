import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../css/findpwd.css"; // 기존 findpwd.css 내용 복사해서 사용

function FindPwdPage() {
  const navigate = useNavigate();

  // 단계: 1=이메일, 2=코드, 3=새비번, 4=완료
  const [step, setStep] = useState(1);

  // 1단계: 이메일
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState("");
  const [emailLoading, setEmailLoading] = useState(false);

  // 2단계: 인증코드
  const [code, setCode] = useState("");
  const [codeError, setCodeError] = useState("");
  const [codeSuccess, setCodeSuccess] = useState("");
  const [timer, setTimer] = useState(180); // 3분(초)
  const [timerId, setTimerId] = useState(null);

  // 3단계: 새비밀번호
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [confirmError, setConfirmError] = useState("");
  const [pwReq, setPwReq] = useState({
    length: false, letter: false, number: false, special: false,
  });

  // ---- 타이머 관련 ----
  useEffect(() => {
    if (step === 2 && timer > 0) {
      const id = setInterval(() => setTimer((t) => t - 1), 1000);
      setTimerId(id);
      return () => clearInterval(id);
    }
    if (timer === 0 && timerId) {
      clearInterval(timerId);
      setTimerId(null);
      alert("인증코드가 만료되었습니다. 다시 받기를 클릭하세요.");
    }
    // eslint-disable-next-line
  }, [step, timer]);

  // --- 비밀번호 요구사항 체크 ---
  useEffect(() => {
    setPwReq({
      length: newPassword.length >= 8,
      letter: /[a-zA-Z]/.test(newPassword),
      number: /\d/.test(newPassword),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(newPassword),
    });
    setPasswordError("");
  }, [newPassword]);

  // --- 단계 1: 이메일 인증코드 보내기 ---
  const handleEmailSubmit = (e) => {
    e.preventDefault();
    setEmailError("");
    if (!email) {
      setEmailError("이메일 주소를 입력해주세요.");
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setEmailError("올바른 이메일 주소를 입력해주세요.");
      return;
    }
    setEmailLoading(true);
    setTimeout(() => {
      setEmailLoading(false);
      setStep(2);
      setTimer(180);
      setCode("");
      setCodeError("");
      setCodeSuccess("");
    }, 1200);
  };

  // --- 단계 2: 인증코드 확인 ---
  const handleCodeSubmit = (e) => {
    e.preventDefault();
    setCodeError("");
    setCodeSuccess("");
    if (!code) {
      setCodeError("인증코드를 입력해주세요.");
      return;
    }
    if (code.length !== 6) {
      setCodeError("6자리 인증코드를 입력해주세요.");
      return;
    }
    // 데모: 정답은 123456 (실제는 서버와 통신)
    if (code !== "123456") {
      setCodeError("인증코드가 올바르지 않습니다.");
      return;
    }
    setCodeSuccess("인증 성공! 새 비밀번호를 입력하세요.");
    setTimeout(() => {
      setStep(3);
      setCode("");
      setCodeError("");
      setCodeSuccess("");
      if (timerId) clearInterval(timerId);
    }, 800);
  };

  // --- 인증코드 재발송 ---
  const handleResend = () => {
    setTimer(180);
    setCode("");
    setCodeError("");
    setCodeSuccess("");
    alert("인증코드가 다시 발송되었습니다.");
  };

  // --- 단계 3: 새 비밀번호 설정 ---
  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    setPasswordError("");
    setConfirmError("");
    // 요구사항 체크
    const ok = Object.values(pwReq).every(Boolean);
    if (!ok) {
      setPasswordError("비밀번호 요구사항을 모두 충족해야 합니다.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setConfirmError("비밀번호가 일치하지 않습니다.");
      return;
    }
    setTimeout(() => {
      setStep(4);
    }, 800);
  };

  // ---- 렌더 ----
  return (
    <div className="findpwd-container">
      {/* 왼쪽 비밀번호 찾기 영역 */}
      <div className="findpwd-side">
        <div className="findpwd-logo">
          <span className="findpwd-logo-icon">📊</span>
          <span className="findpwd-logo-text">FinSight</span>
        </div>
        <p className="findpwd-subtitle">투자 의사결정을 위한 AI 분석 플랫폼</p>

        {/* 단계 인디케이터 */}
        <div className="step-indicator">
          <div className="step">
            <div className={`step-number${step > 1 ? "" : ""}`}>1</div>
            <div className="step-text">본인 인증</div>
          </div>
          <div className="step-arrow">→</div>
          <div className="step">
            <div className={`step-number${step > 1 ? "" : " inactive"}`}>2</div>
            <div className="step-text">인증코드 확인</div>
          </div>
          <div className="step-arrow">→</div>
          <div className="step">
            <div className={`step-number${step === 3 || step === 4 ? "" : " inactive"}`}>3</div>
            <div className="step-text">새 비밀번호</div>
          </div>
        </div>

        {/* 1단계: 이메일 입력 */}
        {step === 1 && (
          <form className="findpwd-form" onSubmit={handleEmailSubmit} autoComplete="off">
            <h1 className="findpwd-title">비밀번호 재설정</h1>
            <p className="findpwd-description">
              가입하신 이메일 주소를 입력해주세요.<br />
              본인 확인을 위한 인증코드를 발송해드립니다.
            </p>
            <div className="input-field">
              <label htmlFor="email">이메일 주소</label>
              <input
                type="email"
                id="email"
                placeholder="가입하신 이메일 주소를 입력하세요"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                autoFocus
              />
              <div className="error-message">{emailError}</div>
            </div>
            <button type="submit" className="findpwd-button" disabled={emailLoading}>
              {emailLoading ? "인증코드 발송 중..." : "인증코드 받기"}
            </button>
          </form>
        )}

        {/* 2단계: 코드 입력 */}
        {step === 2 && (
          <form className="findpwd-form" onSubmit={handleCodeSubmit}>
            <h1 className="findpwd-title">인증코드 확인</h1>
            <p className="findpwd-description">
              <span className="accent">{email}</span>로 발송된<br />
              6자리 인증코드를 입력해주세요.
            </p>
            <div className="input-field">
              <label htmlFor="verification-code">인증코드</label>
              <input
                type="text"
                id="verification-code"
                placeholder="6자리 인증코드를 입력하세요"
                maxLength={6}
                value={code}
                onChange={e => setCode(e.target.value.replace(/[^0-9]/g, ""))}
                required
                autoFocus
              />
              <div className="error-message">{codeError}</div>
              <div className="success-message">{codeSuccess}</div>
            </div>
            <div className="code-info">
              <p>
                인증코드가 오지 않나요?{" "}
                <button type="button" className="resend-btn" onClick={handleResend}>
                  다시 받기
                </button>
              </p>
              <p className="timer">
                유효시간:{" "}
                <span>
                  {String(Math.floor(timer / 60)).padStart(2, "0")}:
                  {String(timer % 60).padStart(2, "0")}
                </span>
              </p>
            </div>
            <button type="submit" className="findpwd-button">
              인증코드 확인
            </button>
          </form>
        )}

        {/* 3단계: 새 비밀번호 */}
        {step === 3 && (
          <form className="findpwd-form" onSubmit={handlePasswordSubmit}>
            <h1 className="findpwd-title">새 비밀번호 설정</h1>
            <p className="findpwd-description">
              보안을 위해 이전과 다른 새로운 비밀번호를<br />
              설정해주세요.
            </p>
            <div className="input-field" id="new-password-field">
              <label htmlFor="new-password">새 비밀번호</label>
              <input
                type="password"
                id="new-password"
                placeholder="8자 이상, 영문/숫자/특수문자 포함"
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                required
                autoFocus
              />
              <div className="error-message">{passwordError}</div>
            </div>
            <div className="input-field" id="confirm-password-field">
              <label htmlFor="confirm-password">비밀번호 확인</label>
              <input
                type="password"
                id="confirm-password"
                placeholder="새 비밀번호를 다시 입력하세요"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                required
              />
              <div className="error-message">{confirmError}</div>
            </div>
            <div className="password-requirements">
              <p>비밀번호 요구사항:</p>
              <ul>
                <li className={`requirement${pwReq.length ? " valid" : ""}`}>8자 이상</li>
                <li className={`requirement${pwReq.letter ? " valid" : ""}`}>영문 포함</li>
                <li className={`requirement${pwReq.number ? " valid" : ""}`}>숫자 포함</li>
                <li className={`requirement${pwReq.special ? " valid" : ""}`}>특수문자 포함</li>
              </ul>
            </div>
            <button type="submit" className="findpwd-button">
              비밀번호 변경하기
            </button>
          </form>
        )}

        {/* 4단계: 성공 */}
        {step === 4 && (
          <div className="success-state">
            <div className="success-icon">✅</div>
            <h2 className="success-title">비밀번호 변경 완료!</h2>
            <p className="success-description">
              비밀번호가 성공적으로 변경되었습니다.<br />
              새로운 비밀번호로 로그인해주세요.
            </p>
            <button
              className="findpwd-button"
              onClick={() => navigate("/login")}
            >
              로그인 페이지로 이동
            </button>
          </div>
        )}

        <div className="back-to-login">
          <p>
            로그인 페이지로 돌아가기{" "}
            <a
              href="#"
              onClick={e => {
                e.preventDefault();
                navigate("/login");
              }}
            >
              로그인
            </a>
          </p>
        </div>
        <div className="copyright">
          <p>© 2025 FinSight. All rights reserved.</p>
        </div>
      </div>
      {/* 오른쪽 안내 영역 */}
      <div className="info-side">
        <div className="info-content">
          <h2 className="info-title">
            안전한 비밀번호<br />재설정 프로세스
          </h2>
          <p className="info-description">
            FinSight는 3단계 인증을 통해 고객의 계정을<br />
            안전하게 보호하고 있습니다.
          </p>
          <div className="security-features">
            <div className="security-item">
              <div className="security-icon">📧</div>
              <div className="security-text">
                이메일 본인 인증
                <small>가입하신 이메일로 인증코드를 발송합니다</small>
              </div>
            </div>
            <div className="security-item">
              <div className="security-icon">🔢</div>
              <div className="security-text">
                6자리 인증코드
                <small>3분 이내에 입력해야 하는 일회용 코드</small>
              </div>
            </div>
            <div className="security-item">
              <div className="security-icon">🔐</div>
              <div className="security-text">
                강력한 비밀번호
                <small>영문, 숫자, 특수문자를 포함한 8자 이상</small>
              </div>
            </div>
            <div className="security-item">
              <div className="security-icon">🛡️</div>
              <div className="security-text">
                즉시 적용
                <small>변경된 비밀번호는 바로 적용됩니다</small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default FindPwdPage;
