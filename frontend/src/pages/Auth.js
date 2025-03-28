import React, { useState } from 'react';
import AuthForm from '../components/AuthForm';
import '../styles/main.css';

function Auth({ setUser, setPage }) {
  const [isLogin, setIsLogin] = useState(true); // Флаг для переключения между входом и регистрацией

  const handleLogin = (email, password) => {
    // Заглушка для входа
    console.log('Вход с данными:', { email, password });
    setUser({ email });
    setPage('home');
  };

  const handleRegister = (username, email, password) => {
    // Заглушка для регистрации
    console.log('Регистрация с данными:', {
      username,
      email,
      password,
      // Позже здесь будет хеширование пароля
      // hashedPassword: hashPassword(password)
    });

    // После "регистрации" автоматически входим
    setUser({ email, username });
    setPage('home');
  };

  return (
    <div className="auth-page">
      <h1>{isLogin ? 'Вход' : 'Регистрация'}</h1>

      {isLogin ? (
        <>
          <AuthForm
            isLogin={true}
            onSubmit={({email, password}) => handleLogin(email, password)}
          />
          <button
            className="auth-toggle"
            onClick={() => setIsLogin(false)}
          >
            Нет аккаунта? Зарегистрироваться
          </button>
        </>
      ) : (
        <>
          <AuthForm
            isLogin={false}
            onSubmit={({username, email, password}) => handleRegister(username, email, password)}
          />
          <button
            className="auth-toggle"
            onClick={() => setIsLogin(true)}
          >
            Уже есть аккаунт? Войти
          </button>
        </>
      )}
    </div>
  );
}

export default Auth;