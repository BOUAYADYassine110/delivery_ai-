import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = () => {
    const token = localStorage.getItem('token') || localStorage.getItem('driver_token') || localStorage.getItem('admin_token');
    const userRole = localStorage.getItem('user_role');
    const userData = localStorage.getItem('user_data');

    if (token && userRole && userData) {
      // Map 'client' to 'customer' for consistency
      const role = userRole === 'client' ? 'customer' : userRole;
      setUser({ ...JSON.parse(userData), role, token });
    }
    setLoading(false);
  };

  const login = (userData, token, role) => {
    const tokenKey = role === 'driver' ? 'driver_token' : role === 'admin' ? 'admin_token' : 'token';
    localStorage.setItem(tokenKey, token);
    localStorage.setItem('user_role', role);
    localStorage.setItem('user_data', JSON.stringify(userData));
    setUser({ ...userData, role, token });
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('driver_token');
    localStorage.removeItem('admin_token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_data');
    setUser(null);
    navigate('/');
  };

  const getDashboardRoute = (role) => {
    // Map 'client' to 'customer' for consistency
    const normalizedRole = role === 'client' ? 'customer' : role;
    switch (normalizedRole) {
      case 'admin': return '/admin/dashboard';
      case 'driver': return '/driver/dashboard';
      case 'customer': return '/dashboard';
      default: return '/';
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, getDashboardRoute }}>
      {children}
    </AuthContext.Provider>
  );
};
