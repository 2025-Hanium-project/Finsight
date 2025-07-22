// src/components/Navbar.js
import React from 'react';
import {useNavigate } from 'react-router-dom';
import '../css/navbar.css'; // 필요하다면 스타일 분리

function Navbar() {
  const navigate = useNavigate();

  return (
    <nav className="navbar">
      <a href="/mypage" onClick={(e) => { e.preventDefault(); navigate('/mypage'); }}>
        마이페이지
      </a>
      <a href="/login" onClick={(e) => { e.preventDefault(); navigate('/login'); }}>
        로그아웃
      </a>
    </nav>
  );
}

export default Navbar;
