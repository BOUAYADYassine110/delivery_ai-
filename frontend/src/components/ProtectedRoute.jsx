import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LoadingScreen from '../components/LoadingScreen';

export const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  const { user, loading } = useAuth();

  if (loading) return <LoadingScreen />;

  if (!user) return <Navigate to="/" replace />;

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return children;
};

export const PublicRoute = ({ children }) => {
  const { user, loading, getDashboardRoute } = useAuth();

  if (loading) return <LoadingScreen />;

  if (user) return <Navigate to={getDashboardRoute(user.role)} replace />;

  return children;
};
