import React, { useState } from 'react';
import AuthForm from '../components/AuthForm';
import '../styles/main.css';

function Auth({ setUser, setPage }) {
  const [isLogin, setIsLogin] = useState(true);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleRegister = async (username, email, password) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://127.0.0.1:5000/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          email,
          password
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || 'Ошибка регистрации');
      }

      setUser({
        username: data.username,
        email: data.email,
      });

      setPage('home');

    } catch (err) {
      setError(err.message || 'Произошла ошибка при регистрации');
      console.error('Registration error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async (emailOrUsername, password) => {
    setIsLoading(true);
    setError(null);

    try {
      // Определяем параметр поиска (email или username)
      const isEmail = emailOrUsername.includes('@');
      const searchParam = isEmail ? 'email' : 'username';

      // Ищем пользователя по email или username
      const searchResponse = await fetch(
        `http://127.0.0.1:5000/users/search?${searchParam}=${encodeURIComponent(emailOrUsername)}`
      );

      const users = await searchResponse.json();

      if (!searchResponse.ok || !users.length) {
        throw new Error('Пользователь не найден');
      }

      const user = users[0];

      // Проверяем пароль (в реальном приложении это должно делаться на бэкенде)
      if (user.password !== password) {
        throw new Error('Неверный пароль');
      }

      // Авторизуем пользователя
      setUser({
        id: user.id,
        username: user.username,
        email: user.email,
      });

      setPage('home');

    } catch (err) {
      setError(err.message || 'Неверные учетные данные');
      console.error('Login error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <h1>{isLogin ? 'Вход' : 'Регистрация'}</h1>

      {error && <div className="error-message">{error}</div>}
      {isLoading && <div className="loading">Загрузка...</div>}

      {isLogin ? (
        <>
          <AuthForm
            isLogin={true}
            onSubmit={({emailOrUsername, password}) => handleLogin(emailOrUsername, password)}
            disabled={isLoading}
          />
          <button
            className="auth-toggle"
            onClick={() => setIsLogin(false)}
            disabled={isLoading}
          >
            Нет аккаунта? Зарегистрироваться
          </button>
        </>
      ) : (
        <>
          <AuthForm
            isLogin={false}
            onSubmit={({username, email, password}) => handleRegister(username, email, password)}
            disabled={isLoading}
          />
          <button
            className="auth-toggle"
            onClick={() => setIsLogin(true)}
            disabled={isLoading}
          >
            Уже есть аккаунт? Войти
          </button>
        </>
      )}
    </div>
  );
}

export default Auth;