import React, { useState } from 'react';
import '../styles/AuthForm.css';

function AuthForm({ isLogin, onSubmit, disabled }) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    emailOrUsername: '',
    password: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isLogin) {
      onSubmit({
        emailOrUsername: formData.emailOrUsername,
        password: formData.password
      });
    } else {
      onSubmit(formData);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="auth-form" autoComplete="off">
      {!isLogin ? (
        <>
          <input
            type="text"
            name="username"
            placeholder="Имя пользователя"
            value={formData.username}
            onChange={handleChange}
            required
            minLength="3"
            disabled={disabled}
          />
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            required
            disabled={disabled}
          />
        </>
      ) : (
        <input
          type="text"
          name="emailOrUsername"
          placeholder="Email или логин"
          value={formData.emailOrUsername}
          onChange={handleChange}
          required
          disabled={disabled}
        />
      )}
      <input
        type="password"
        name="password"
        placeholder="Пароль"
        value={formData.password}
        onChange={handleChange}
        required
        minLength="6"
        disabled={disabled}
      />
      <button type="submit" disabled={disabled}>
        {isLogin ? 'Войти' : 'Зарегистрироваться'}
      </button>
    </form>
  );
}

export default AuthForm;