import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "../css/signup.css"; 

function SignupPage() {
  const navigate = useNavigate();

  // 아이디 상태
  const [userId, setUserId] = useState("");
  const [userIdMsg, setUserIdMsg] = useState("");
  const [userIdChecked, setUserIdChecked] = useState(false);

  // 기본 정보 상태
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [emailMsg, setEmailMsg] = useState("");
  const [emailVerified, setEmailVerified] = useState(false);

  // 계정 정보 상태
  const [password, setPassword] = useState("");
  const [passwordStrength, setPasswordStrength] = useState(0);
  const [passwordStrengthText, setPasswordStrengthText] = useState("비밀번호 강도");
  const [passwordStrengthColor, setPasswordStrengthColor] = useState("#e5e7eb");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordMsg, setPasswordMsg] = useState("");

  // 투자 정보 상태
  // const [experience, setExperience] = useState("");
  // const [riskTolerance, setRiskTolerance] = useState("");
  // const [investmentAmount, setInvestmentAmount] = useState("");

  // 약관 동의 상태
  const [agreeAll, setAgreeAll] = useState(false);
  const [agreements, setAgreements] = useState({
    terms: false,
    privacy: false,
    investment: false,
    marketing: false,
  });

  // 제출 버튼 활성화 여부
  const [submitActive, setSubmitActive] = useState(false);

  // refs
  const emailVerifyBtn = useRef(null);

  // 비밀번호 강도 체크 함수
  function checkPasswordStrength(pw) {
    let strength = 0;
    if (pw.length >= 8) strength += 1;
    if (/[a-z]/.test(pw)) strength += 1;
    if (/[A-Z]/.test(pw)) strength += 1;
    if (/[0-9]/.test(pw)) strength += 1;
    if (/[^A-Za-z0-9]/.test(pw)) strength += 1;
    setPasswordStrength(strength);

    let percent = (strength / 5) * 100;
    let color = "#ef4444", text = "약함";
    if (strength < 2) {
      color = "#ef4444"; text = "약함";
    } else if (strength < 4) {
      color = "#f59e0b"; text = "보통";
    } else {
      color = "#10b981"; text = "강함";
    }
    setPasswordStrengthColor(color);
    setPasswordStrengthText(text);
    return strength >= 3;
  }

  // 비밀번호 확인
  function checkPasswordMatch(pw = password, confirmPw = confirmPassword) {
    if (confirmPw && pw !== confirmPw) {
      setPasswordMsg("비밀번호를 다시 입력하세요");
      return false;
    } else if (confirmPw && pw === confirmPw) {
      setPasswordMsg("비밀번호가 일치합니다.");
      return true;
    }
    setPasswordMsg("");
    return false;
  }

  // 전체 동의 처리
  const handleAgreeAll = (checked) => {
    setAgreeAll(checked);
    setAgreements({
      terms: checked,
      privacy: checked,
      investment: checked,
      marketing: checked,
    });
  };

  // 개별 약관 동의 처리
  const handleAgreementChange = (name, checked) => {
    const next = { ...agreements, [name]: checked };
    setAgreements(next);
    setAgreeAll(Object.values(next).every((v) => v));
  };

  // 이메일 인증 버튼 클릭
  const handleEmailVerify = () => {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setEmailMsg("올바른 이메일 형식을 입력하세요.");
      return;
    }
    setEmailMsg("인증번호가 발송되었습니다.");
    setEmailVerified(true);
    if (emailVerifyBtn.current) {
      emailVerifyBtn.current.innerText = "재발송";
    }
  };

  // 아이디 중복 확인 함수
  const handleUserIdCheck = async () => {
    if (!userId.trim()) {
      setUserIdMsg("아이디를 입력하세요.");
      setUserIdChecked(false);
      return;
    }

    if (!/^[a-zA-Z0-9]{4,}$/.test(userId)) {
      setUserIdMsg("4자 이상 영문/숫자만 사용 가능합니다.");
      setUserIdChecked(false);
      return;
    }

    try {
      const res = await fetch(`/api/auth/check-login-id?login_id=${encodeURIComponent(userId)}`);
      const data = await res.json();

      if (res.ok && data.available) {
        setUserIdMsg("사용 가능한 아이디입니다.");
        setUserIdChecked(true);
      } else {
        setUserIdMsg("이미 사용 중인 아이디입니다.");
        setUserIdChecked(false);
      }
    } catch (err) {
      console.error("중복 확인 오류:", err);
      setUserIdMsg("서버 오류가 발생했습니다.");
      setUserIdChecked(false);
    }
  };
  // 폼 전체 유효성 검사
  React.useEffect(() => {
    const requiredFilled =
      name && email && userIdChecked &&
      password && confirmPassword &&
      agreements.terms && agreements.privacy && agreements.investment;
    const passwordValid = checkPasswordStrength(password);
    const passwordMatches = password === confirmPassword && password.length > 0;
    setSubmitActive(!!(requiredFilled && passwordValid && passwordMatches));
  }, [
    name, email, userIdChecked,
    password, confirmPassword,
    agreements.terms, agreements.privacy, agreements.investment,
  ]);

  // 폼 제출 처리
  async function handleSubmit(e) {
    e.preventDefault();
    if (!submitActive) return;

    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          user_name: name,
          login_id: userId,
          password: password,
          email: email
        })
      });

      const data = await response.json();

      if (response.status === 201) {
        alert("회원가입이 완료되었습니다!");
        navigate("/login");
      } else if (response.status === 409) {
        alert(data.message || "이미 존재하는 사용자입니다.");
      } else {
        alert("회원가입에 실패했습니다. 다시 시도해주세요.");
      }
    } catch (error) {
      console.error("회원가입 오류:", error);
      alert("서버와의 연결에 문제가 발생했습니다.");
    }
  }

  return (
    <div className="signup-container">
      {/* 회원가입 영역 */}
      <div className="signup-side">
        <div className="signup-logo">
          <span className="signup-logo-icon">📊</span>
          <span className="signup-logo-text">FinSight</span>
        </div>
        <p className="signup-subtitle">투자 의사결정을 위한 AI 분석 플랫폼</p>

        <h1 className="signup-title">회원가입</h1>

        <form className="signup-form" onSubmit={handleSubmit} autoComplete="off">
          {/* 기본 정보 */}
          <div className="form-section">
            <h3 className="section-title">기본 정보</h3>

            <div className="input-row">
              <div className="input-field">
                <label htmlFor="name">이름 *</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  placeholder="실명을 입력하세요"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
            </div>

            <div className="input-field">
              <label htmlFor="email">이메일 *</label>
              <div className="input-with-button">
                <input
                  type="email"
                  id="email"
                  name="email"
                  placeholder="example@email.com"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={emailVerified}
                />
                <button
                  type="button"
                  className="verify-button"
                  ref={emailVerifyBtn}
                  onClick={handleEmailVerify}
                  disabled={emailVerified}
                >
                  {emailVerified ? "인증완료" : "인증"}
                </button>
              </div>
              <div className="input-message">{emailMsg}</div>
            </div>
          </div>

          {/* 계정 정보 */}
          <div className="form-section">
            <h3 className="section-title">계정 정보</h3>
            <div className="input-field">
              <label htmlFor="userId">아이디 *</label>
              <div className="input-with-button">
                <input
                  type="text"
                  id="userId"
                  name="userId"
                  placeholder="아이디를 입력하세요"
                  required
                  value={userId}
                  onChange={e => {
                    setUserId(e.target.value);
                    setUserIdChecked(false);
                    setUserIdMsg("");
                  }}
                />
                <button
                  type="button"
                  className="verify-button"
                  onClick={handleUserIdCheck}
                  disabled={userIdChecked}
                >
                  {userIdChecked ? "확인됨" : "중복 확인"}
                </button>
              </div>
              <div className="input-message" style={{ color: userIdChecked ? "#10b981" : "#ef4444" }}>{userIdMsg}</div>
            </div>
            <div className="input-field">
              <label htmlFor="password">비밀번호 *</label>
              <input
                type="password"
                id="password"
                name="password"
                placeholder="8자 이상, 영문/숫자/특수문자 포함"
                required
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (confirmPassword) checkPasswordMatch(e.target.value, confirmPassword);
                }}
              />
              <div className="password-strength">
                <div className="strength-bar">
                  <div
                    className="strength-fill"
                    style={{ width: `${(passwordStrength / 5) * 100}%`, backgroundColor: passwordStrengthColor }}
                  />
                </div>
                <div className="strength-text" style={{ color: passwordStrengthColor }}>
                  {passwordStrengthText}
                </div>
              </div>
            </div>
            <div className="input-field">
              <label htmlFor="confirmPassword">비밀번호 확인 *</label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                placeholder="비밀번호를 다시 입력하세요"
                required
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  checkPasswordMatch(password, e.target.value);
                }}
              />
              <div className="input-message" style={{ color: password === confirmPassword ? "#10b981" : "#ef4444" }}>
                {passwordMsg}
              </div>
            </div>
          </div>

          {/* 투자 정보 */}
          {/* <div className="form-section">
            <h3 className="section-title">투자 정보</h3>
            <div className="input-field">
              <label htmlFor="experience">투자 경험</label>
              <select id="experience" name="experience" value={experience} onChange={e => setExperience(e.target.value)}>
                <option value="">선택하세요</option>
                <option value="beginner">초보자 (1년 미만)</option>
                <option value="intermediate">중급자 (1-5년)</option>
                <option value="advanced">고급자 (5년 이상)</option>
              </select>
            </div>
            <div className="input-field">
              <label htmlFor="riskTolerance">투자 성향</label>
              <select id="riskTolerance" name="riskTolerance" value={riskTolerance} onChange={e => setRiskTolerance(e.target.value)}>
                <option value="">선택하세요</option>
                <option value="conservative">보수적</option>
                <option value="moderate">중도적</option>
                <option value="aggressive">공격적</option>
              </select>
            </div>
            <div className="input-field">
              <label htmlFor="investmentAmount">투자 금액 범위</label>
              <select id="investmentAmount" name="investmentAmount" value={investmentAmount} onChange={e => setInvestmentAmount(e.target.value)}>
                <option value="">선택하세요</option>
                <option value="low">1천만원 이하</option>
                <option value="medium">1천만원 - 5천만원</option>
                <option value="high">5천만원 이상</option>
              </select>
            </div>
          </div> */}

          {/* 약관 동의 */}
          <div className="form-section">
            <h3 className="section-title">약관 동의</h3>
            <div className="agreement-section">
              <label className="agreement-item">
                <input type="checkbox" checked={agreeAll} onChange={e => handleAgreeAll(e.target.checked)} />
                <span className="checkmark"></span>
                <span className="agreement-text main">전체 동의</span>
              </label>
              <div className="agreement-details">
                <label className="agreement-item">
                  <input type="checkbox" checked={agreements.terms} required onChange={e => handleAgreementChange("terms", e.target.checked)} />
                  <span className="checkmark"></span>
                  <span className="agreement-text">[필수] 서비스 이용약관 동의</span>
                  <a href="#" className="agreement-link">보기</a>
                </label>
                <label className="agreement-item">
                  <input type="checkbox" checked={agreements.privacy} required onChange={e => handleAgreementChange("privacy", e.target.checked)} />
                  <span className="checkmark"></span>
                  <span className="agreement-text">[필수] 개인정보 처리방침 동의</span>
                  <a href="#" className="agreement-link">보기</a>
                </label>
                <label className="agreement-item">
                  <input type="checkbox" checked={agreements.investment} required onChange={e => handleAgreementChange("investment", e.target.checked)} />
                  <span className="checkmark"></span>
                  <span className="agreement-text">[필수] 투자정보 활용 동의</span>
                  <a href="#" className="agreement-link">보기</a>
                </label>
                <label className="agreement-item">
                  <input type="checkbox" checked={agreements.marketing} onChange={e => handleAgreementChange("marketing", e.target.checked)} />
                  <span className="checkmark"></span>
                  <span className="agreement-text">[선택] 마케팅 정보 수신 동의</span>
                  <a href="#" className="agreement-link">보기</a>
                </label>
              </div>
            </div>
          </div>
          <button type="submit" className="signup-button" disabled={!submitActive}>회원가입</button>
        </form>
        <div className="login-link">
          <p>
            이미 계정이 있으신가요?{" "}
            <a href="#" onClick={e => { e.preventDefault(); navigate("/login"); }}>
              로그인
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
            AI가 제안하는<br />스마트한 투자 전략
          </h2>
          <p className="showcase-description">
            개인 맞춤형 포트폴리오 추천부터 실시간 시장 분석까지<br />
            FinSight와 함께 투자의 새로운 경험을 시작하세요.
          </p>
          <div className="feature-list">
            <div className="feature-item">
              <div className="feature-icon">🎯</div>
              <div className="feature-content">
                <div className="feature-title">맞춤형 추천</div>
                <div className="feature-desc">투자 성향에 맞는 종목 분석</div>
              </div>
            </div>
            <div className="feature-item">
              <div className="feature-icon">📊</div>
              <div className="feature-content">
                <div className="feature-title">실시간 분석</div>
                <div className="feature-desc">AI 기반 시장 동향 분석</div>
              </div>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🔔</div>
              <div className="feature-content">
                <div className="feature-title">스마트 알림</div>
                <div className="feature-desc">중요한 투자 기회 놓치지 않기</div>
              </div>
            </div>
            <div className="feature-item">
              <div className="feature-icon">🛡️</div>
              <div className="feature-content">
                <div className="feature-title">안전한 서비스</div>
                <div className="feature-desc">금융 보안 표준 준수</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SignupPage;
