
import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Menu";
import "../css/profile_edit.css";

function ProfileEditPage() {
  const navigate = useNavigate();

  // 프로필 이미지
  const [profileImg, setProfileImg] = useState(null);
  const fileInputRef = useRef();

  // 비밀번호 변경 모달
  const [showPwdModal, setShowPwdModal] = useState(false);

  // 비밀번호 상태
  const [currentPwd, setCurrentPwd] = useState("");
  const [newPwd, setNewPwd] = useState("");
  const [confirmPwd, setConfirmPwd] = useState("");
  const [pwdStrength, setPwdStrength] = useState({ text: "비밀번호 강도", color: "", percent: 0 });
  const [pwdMsg, setPwdMsg] = useState("");

  // 2단계 인증, 로그인 알림
  const [twoFactor, setTwoFactor] = useState(true);
  const [loginNoti, setLoginNoti] = useState(true);

  // 기본 정보 입력값
  const [profile, setProfile] = useState({
    name: "김투자",
    birth: "1990-05-15",
    email: "investor@example.com",
    phone: "010-1234-5678",
    zipcode: "",
    address: "",
    detailAddress: ""
  });

  // 이미지 변경
  const onProfileImgClick = () => {
    fileInputRef.current.click();
  };
  const onProfileImgChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (ev) => setProfileImg(ev.target.result);
      reader.readAsDataURL(file);
    }
  };

  // 비밀번호 강도 체크
  const checkPasswordStrength = (pw) => {
    let strength = 0;
    if (pw.length >= 8) strength += 1;
    if (/[a-z]/.test(pw)) strength += 1;
    if (/[A-Z]/.test(pw)) strength += 1;
    if (/[0-9]/.test(pw)) strength += 1;
    if (/[^A-Za-z0-9]/.test(pw)) strength += 1;
    const percent = (strength / 5) * 100;
    let color = "", text = "";
    if (strength < 2) {
      color = "#ef4444"; text = "약함";
    } else if (strength < 4) {
      color = "#f59e0b"; text = "보통";
    } else {
      color = "#10b981"; text = "강함";
    }
    setPwdStrength({ text, color, percent });
    return strength >= 3;
  };

  // 비밀번호 입력 이벤트
  const handleNewPwd = (e) => {
    setNewPwd(e.target.value);
    checkPasswordStrength(e.target.value);
    if (confirmPwd) handleConfirmPwd({ target: { value: confirmPwd } });
  };
  const handleConfirmPwd = (e) => {
    const val = e.target.value;
    setConfirmPwd(val);
    if (val && newPwd !== val) {
      setPwdMsg("비밀번호가 일치하지 않습니다.");
    } else if (val && newPwd === val) {
      setPwdMsg("비밀번호가 일치합니다.");
    } else {
      setPwdMsg("");
    }
  };

  // 비밀번호 변경 처리
  const handleSavePwd = () => {
    if (!currentPwd || !newPwd || !confirmPwd) {
      alert("모든 필드를 입력해주세요.");
      return;
    }
    if (!checkPasswordStrength(newPwd)) {
      alert("비밀번호가 너무 약합니다.");
      return;
    }
    if (newPwd !== confirmPwd) {
      alert("새 비밀번호가 일치하지 않습니다.");
      return;
    }
    alert("비밀번호가 성공적으로 변경되었습니다.");
    setShowPwdModal(false);
    setCurrentPwd("");
    setNewPwd("");
    setConfirmPwd("");
    setPwdMsg("");
    setPwdStrength({ text: "비밀번호 강도", color: "", percent: 0 });
  };

  // 프로필 폼 저장
  const handleSaveProfile = (e) => {
    e.preventDefault();
    alert("프로필이 성공적으로 저장되었습니다.");
    navigate("/mypage");
  };

  // 주소 검색(실제 구현 필요)
  const handleAddressSearch = () => {
    alert("주소 검색 기능을 구현하세요.");
  };

  // 뒤로가기, 취소
  const handleBack = () => navigate("/mypage");

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
        <Navbar />
      </div>

      {/* 메인 콘텐츠 */}
      <div className="main-dashboard-content">
        {/* 헤더 */}
        <div className="header">
          <div>
            <h1 className="page-title">프로필 수정</h1>
            <p className="date-info">개인정보 및 투자 설정을 관리하세요</p>
          </div>
          <div className="header-actions">
            <button className="btn-back" onClick={handleBack}>
              <i className="fas fa-arrow-left"></i>
              돌아가기
            </button>
          </div>
        </div>

        {/* 프로필 수정 폼 */}
        <form className="profile-form" onSubmit={handleSaveProfile}>
          {/* 프로필 이미지 섹션 */}
          <div className="profile-image-section">
            <div className="profile-card">
              <div className="profile-image-container" onClick={onProfileImgClick}>
                <div className="profile-avatar" id="profileAvatar">
                  {profileImg ? (
                    <img src={profileImg} alt="프로필 이미지" style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: "50%" }} />
                  ) : (
                    <span className="avatar-initial">김</span>
                  )}
                </div>
                <div className="profile-image-overlay">
                  <i className="fas fa-camera"></i>
                  <span>변경</span>
                </div>
                <input type="file" ref={fileInputRef} accept="image/*" hidden onChange={onProfileImgChange} />
              </div>
              <div className="profile-image-info">
                <h3 className="current-name">김투자</h3>
                <p className="image-guide">JPG, PNG 파일만 업로드 가능 (최대 5MB)</p>
              </div>
            </div>
          </div>

          {/* 기본 정보 섹션 */}
          <div className="form-section">
            <h2 className="section-title">기본 정보</h2>
            <div className="form-grid">
              <div className="input-field">
                <label htmlFor="name">이름 *</label>
                <input type="text" id="name" name="name" value={profile.name} required
                  onChange={e => setProfile(p => ({ ...p, name: e.target.value }))} />
              </div>
              <div className="input-field">
                <label htmlFor="birth">생년월일</label>
                <input type="date" id="birth" name="birth" value={profile.birth}
                  onChange={e => setProfile(p => ({ ...p, birth: e.target.value }))} />
              </div>
              <div className="input-field">
                <label htmlFor="email">이메일 *</label>
                <div className="input-with-status">
                  <input type="email" id="email" name="email" value={profile.email} required
                    onChange={e => setProfile(p => ({ ...p, email: e.target.value }))} />
                  <span className="verification-status verified">
                    <i className="fas fa-check-circle"></i>
                    인증됨
                  </span>
                </div>
              </div>
              <div className="input-field">
                <label htmlFor="phone">휴대폰 번호 *</label>
                <div className="input-with-status">
                  <input type="tel" id="phone" name="phone" value={profile.phone} required
                    onChange={e => setProfile(p => ({ ...p, phone: e.target.value }))} />
                  <span className="verification-status verified">
                    <i className="fas fa-check-circle"></i>
                    인증됨
                  </span>
                </div>
              </div>
              <div className="input-field">
                <label htmlFor="address">주소</label>
                <div className="address-input">
                  <div className="address-row">
                    <input type="text" id="zipcode" name="zipcode" placeholder="우편번호" readOnly value={profile.zipcode} />
                    <button type="button" className="btn-address-search" onClick={handleAddressSearch}>주소 검색</button>
                  </div>
                  <input type="text" id="address" name="address" placeholder="기본 주소" readOnly value={profile.address} />
                  <input type="text" id="detailAddress" name="detailAddress" placeholder="상세 주소"
                    value={profile.detailAddress} onChange={e => setProfile(p => ({ ...p, detailAddress: e.target.value }))} />
                </div>
              </div>
            </div>
          </div>

          {/* 보안 설정 섹션 */}
          <div className="form-section">
            <h2 className="section-title">보안 설정</h2>
            <div className="security-settings">
              <div className="security-item">
                <div className="security-info">
                  <h4>비밀번호 변경</h4>
                  <p>계정 보안을 위해 정기적으로 비밀번호를 변경하세요</p>
                </div>
                <button type="button" className="btn-security" onClick={() => setShowPwdModal(true)}>
                  비밀번호 변경
                </button>
              </div>
              <div className="security-item">
                <div className="security-info">
                  <h4>2단계 인증</h4>
                  <p>SMS 또는 앱을 통한 추가 보안 인증</p>
                </div>
                <label className="toggle-switch">
                  <input type="checkbox" checked={twoFactor} onChange={e => setTwoFactor(e.target.checked)} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
              <div className="security-item">
                <div className="security-info">
                  <h4>로그인 알림</h4>
                  <p>새로운 기기에서 로그인 시 이메일 알림</p>
                </div>
                <label className="toggle-switch">
                  <input type="checkbox" checked={loginNoti} onChange={e => setLoginNoti(e.target.checked)} />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>
          </div>

          {/* 저장/취소 */}
          <div className="form-actions">
            <button type="button" className="btn-cancel" onClick={handleBack}>취소</button>
            <button type="submit" className="btn-save">
              <i className="fas fa-save"></i>
              저장하기
            </button>
          </div>
        </form>
      </div>

      {/* 비밀번호 변경 모달 */}
      {showPwdModal && (
        <div className="modal-overlay" id="passwordModal" onClick={e => { if (e.target.className === "modal-overlay") setShowPwdModal(false); }}>
          <div className="modal">
            <div className="modal-header">
              <h3>비밀번호 변경</h3>
              <button type="button" className="modal-close" onClick={() => setShowPwdModal(false)}>
                <i className="fas fa-times"></i>
              </button>
            </div>
            <div className="modal-body">
              <form id="passwordForm" onSubmit={e => e.preventDefault()}>
                <div className="input-field">
                  <label htmlFor="currentPassword">현재 비밀번호 *</label>
                  <input type="password" id="currentPassword" name="currentPassword" required
                    value={currentPwd} onChange={e => setCurrentPwd(e.target.value)} />
                </div>
                <div className="input-field">
                  <label htmlFor="newPassword">새 비밀번호 *</label>
                  <input type="password" id="newPassword" name="newPassword" required
                    value={newPwd} onChange={handleNewPwd}
                    placeholder="8자 이상, 영문/숫자/특수문자 포함" />
                  <div className="password-strength" id="passwordStrength">
                    <div className="strength-bar">
                      <div className="strength-fill" style={{
                        width: `${pwdStrength.percent}%`,
                        backgroundColor: pwdStrength.color
                      }}></div>
                    </div>
                    <div className="strength-text">{pwdStrength.text}</div>
                  </div>
                </div>
                <div className="input-field">
                  <label htmlFor="confirmNewPassword">새 비밀번호 확인 *</label>
                  <input type="password" id="confirmNewPassword" name="confirmNewPassword" required
                    value={confirmPwd} onChange={handleConfirmPwd} />
                  <div className="input-message" id="passwordMessage"
                    style={{ color: pwdMsg === "비밀번호가 일치합니다." ? "#10b981" : (pwdMsg ? "#ef4444" : undefined) }}
                  >{pwdMsg}</div>
                </div>
              </form>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn-cancel" onClick={() => setShowPwdModal(false)}>취소</button>
              <button type="button" className="btn-save" onClick={handleSavePwd}>변경하기</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ProfileEditPage;
