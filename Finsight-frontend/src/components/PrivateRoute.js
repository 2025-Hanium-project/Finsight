import React, { useContext } from 'react';
import { Navigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';

function PrivateRoute({ children }) {
  const { isAuthenticated } = useContext(AuthContext);

  if (isAuthenticated === null) return <div></div>;

  return isAuthenticated ? children : <Navigate to="/login" />;
}

export default PrivateRoute;