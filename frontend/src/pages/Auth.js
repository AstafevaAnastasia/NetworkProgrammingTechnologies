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
      if (isLogin) {
        // Логика входа
        const response = await fetch('http://127.0.0.1:5000/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            [formData.emailOrUsername.includes('@') ? 'email' : 'username']: formData.emailOrUsername,
            password: formData.password
          }),
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Login failed');

        // Сохраняем данные после входа
        localStorage.setItem('access_token', result.access_token);
        localStorage.setItem('refresh_token', result.refresh_token);
        localStorage.setItem('user', JSON.stringify(result.user));
        setUser(result.user);
        navigate('/');
      } else {
        // Логика регистрации
        const registerResponse = await fetch('http://127.0.0.1:5000/users', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: formData.username,
            email: formData.email,
            password: formData.password
          }),
        });

        const registerResult = await registerResponse.json();
        if (!registerResponse.ok) throw new Error(registerResult.error || 'Registration failed');

        // Автоматический вход после регистрации
        const loginResponse = await fetch('http://127.0.0.1:5000/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: formData.email,
            password: formData.password
          }),
        });

        const loginResult = await loginResponse.json();
        if (!loginResponse.ok) throw new Error(loginResult.error || 'Auto-login failed');

        // Сохраняем данные после автоматического входа
        localStorage.setItem('access_token', loginResult.access_token);
        localStorage.setItem('refresh_token', loginResult.refresh_token);
        localStorage.setItem('user', JSON.stringify(loginResult.user));
        setUser(loginResult.user);
        navigate('/');
      }
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