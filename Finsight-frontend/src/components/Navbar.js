// src/components/Navbar.js
import React, { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import '../css/navbar.css'; // 필요하다면 스타일 분리

function Navbar() {
  const navigate = useNavigate();
  const { logout } = useContext(AuthContext);

  const handleLogout = async (e) => {
    e.preventDefault();
    await logout();       // 로그아웃 함수 호출
    navigate('/login');   // 로그인 페이지로 이동
  };
  return (
    <nav className="navbar">
      <a href="/mypage" onClick={(e) => { e.preventDefault(); navigate('/mypage'); }}>
        마이페이지
      </a>
      <a href="/logout" onClick={handleLogout}>
        로그아웃
      </a>
    </nav>
  );
}

export default Navbar;
