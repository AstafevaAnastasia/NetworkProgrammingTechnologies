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

      // Сохраняем данные пользователя после успешной регистрации
      setUser({
        username: data.username,
        email: data.email,
        // Другие данные, которые может вернуть сервер
      });

      // Перенаправляем на главную страницу
      setPage('home');

    } catch (err) {
      setError(err.message || 'Произошла ошибка при регистрации');
      console.error('Registration error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = (email, password) => {
    // Заглушка для входа (реализуйте аналогично регистрации)
    console.log('Login attempt:', { email, password });
    setUser({ email });
    setPage('home');
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
            onSubmit={({email, password}) => handleLogin(email, password)}
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