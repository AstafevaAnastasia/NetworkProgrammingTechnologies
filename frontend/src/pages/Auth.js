import React, { useState } from 'react';
import AuthForm from '../components/AuthForm';
import { useNavigate } from 'react-router-dom';
import '../styles/main.css';

function Auth({ setUser }) {
  const [isLogin, setIsLogin] = useState(true);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleAuth = async (formData) => {
    setIsLoading(true);
    setError(null);

    try {
      const endpoint = isLogin ? '/login' : '/register';
      const body = isLogin
        ? {
            [formData.emailOrUsername.includes('@') ? 'email' : 'username']:
              formData.emailOrUsername,
            password: formData.password
          }
        : {
            username: formData.username,
            email: formData.email,
            password: formData.password
          };

      const response = await fetch(`http://127.0.0.1:5000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Authentication failed');

      // Сохраняем данные после успешной аутентификации
      localStorage.setItem('access_token', result.access_token);
      localStorage.setItem('refresh_token', result.refresh_token);
      localStorage.setItem('user', JSON.stringify(result.user));
      setUser(result.user);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Authentication error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <h1>{isLogin ? 'Вход' : 'Регистрация'}</h1>
      {error && <div className="error-message">{error}</div>}
      {isLoading && <div className="loading">Загрузка...</div>}

      <AuthForm
        isLogin={isLogin}
        onSubmit={handleAuth}
        disabled={isLoading}
      />

      <button
        className="auth-toggle"
        onClick={() => setIsLogin(!isLogin)}
        disabled={isLoading}
      >
        {isLogin ? 'Нет аккаунта? Зарегистрироваться' : 'Уже есть аккаунт? Войти'}
      </button>
    </div>
  );
}

export default Auth;