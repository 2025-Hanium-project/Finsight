// App.js
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import PrivateRoute from './components/PrivateRoute';

import IndexPage from './page/DashboardPage';
import LoginPage from './page/LoginPage';
import SignupPage from './page/SignupPage';
import FindPwdPage from './page/FindPwdPage';
import MyPage from './page/MyPage';
import ProfileEditPage from './page/ProfileEditPage';
import DdayReportPage from './page/DdayReportPage';
import DPlus1ReportPage from './page/DPlus1ReportPage';
import DetailPage from './page/DetailPage';


function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* 로그인 불필요 */}
          <Route path="/" element={<LoginPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/findpwd" element={<FindPwdPage />} />

          {/* 로그인 필요 */}
          <Route path="/dashboard" element={<IndexPage />} />
          <Route path="/mypage" element={<MyPage />} />
          <Route path="/profileedit" element={<ProfileEditPage />} />
          <Route path="/dday" element={<DdayReportPage />} />
          <Route path="/dplus1" element={<DPlus1ReportPage />} />
          <Route path="/detail/:stockCode" element={<DetailPage />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;

