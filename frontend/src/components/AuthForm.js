import React, { useState } from 'react';
import '../styles/AuthForm.css';

function AuthForm({ isLogin, onSubmit, disabled }) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    emailOrUsername: '',
    password: ''
  });

  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Очищаем ошибку при изменении поля
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (isLogin) {
      if (!formData.emailOrUsername) {
        newErrors.emailOrUsername = 'Введите email или имя пользователя';
      }
    } else {
      if (!formData.username) {
        newErrors.username = 'Введите имя пользователя';
      }
      if (!formData.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        newErrors.email = 'Введите корректный email';
      }
    }

    if (!formData.password || formData.password.length < 6) {
      newErrors.password = 'Пароль должен содержать минимум 6 символов';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    if (isLogin) {
      onSubmit({
        emailOrUsername: formData.emailOrUsername.trim(),
        password: formData.password
      });
    } else {
      onSubmit({
        username: formData.username.trim(),
        email: formData.email.trim(),
        password: formData.password
      });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="auth-form" autoComplete="off">
      {!isLogin ? (
        <>
          <div className="form-group">
            <input
              type="text"
              name="username"
              placeholder="Имя пользователя"
              value={formData.username}
              onChange={handleChange}
              disabled={disabled}
              className={errors.username ? 'error' : ''}
            />
            {errors.username && <span className="error-text">{errors.username}</span>}
          </div>
          <div className="form-group">
            <input
              type="email"
              name="email"
              placeholder="Email"
              value={formData.email}
              onChange={handleChange}
              disabled={disabled}
              className={errors.email ? 'error' : ''}
            />
            {errors.email && <span className="error-text">{errors.email}</span>}
          </div>
        </>
      ) : (
        <div className="form-group">
          <input
            type="text"
            name="emailOrUsername"
            placeholder="Email или имя пользователя"
            value={formData.emailOrUsername}
            onChange={handleChange}
            disabled={disabled}
            className={errors.emailOrUsername ? 'error' : ''}
          />
          {errors.emailOrUsername && <span className="error-text">{errors.emailOrUsername}</span>}
        </div>
      )}
      <div className="form-group">
        <input
          type="password"
          name="password"
          placeholder="Пароль"
          value={formData.password}
          onChange={handleChange}
          disabled={disabled}
          className={errors.password ? 'error' : ''}
        />
        {errors.password && <span className="error-text">{errors.password}</span>}
      </div>
      <button type="submit" disabled={disabled}>
        {isLogin ? 'Войти' : 'Зарегистрироваться'}
      </button>
    </form>
  );
}

export default AuthForm;