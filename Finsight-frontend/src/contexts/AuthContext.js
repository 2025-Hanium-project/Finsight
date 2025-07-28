import React, { createContext, useEffect, useState } from 'react';

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const [userInfo, setUserInfo] = useState(null);  // ✅ 사용자 정보 추가

  useEffect(() => {
    fetch('/api/auth/check-session', {
      credentials: 'include',
    })
      .then(res => {
        if (res.ok) return res.json();
        throw new Error('Not logged in');
      })
      .then(data => {
        setIsAuthenticated(data.logged_in);
        if (data.logged_in) setUserInfo({ user_id: data.user_id }); // 필요 시
      })
      .catch(() => setIsAuthenticated(false));
  }, []);

  const logout = async () => {
    try {
      const res = await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });

      if (res.ok) {
        setIsAuthenticated(false);
        setUserInfo(null); // ✅ 사용자 정보도 초기화
      } else {
        console.error('로그아웃 실패');
      }
    } catch (error) {
      console.error('로그아웃 오류:', error);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        setIsAuthenticated,  // ✅ 로그인 성공 시 업데이트 용도
        userInfo,
        setUserInfo,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}