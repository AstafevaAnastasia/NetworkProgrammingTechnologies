import React, { useState } from 'react';
import AuthForm from '../components/AuthForm';
import '../styles/main.css';

function Auth({ setUser, setPage }) {
  const handleLogin = (email, password) => {
    // В реальном приложении здесь был бы запрос к API
    setUser({ email });
    setPage('home');
  };

  return (
    <div className="auth-page">
      <h1>Вход</h1>
      <AuthForm onSubmit={handleLogin} />
    </div>
  );
}

export default Auth;