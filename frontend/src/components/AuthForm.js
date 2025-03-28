import React, { useState } from 'react';
import '../styles/AuthForm.css';

function AuthForm({ isLogin, onSubmit }) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isLogin) {
      onSubmit({ email: formData.email, password: formData.password });
    } else {
      onSubmit({ ...formData });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      {!isLogin && (
        <input
          type="text"
          name="username"
          placeholder="Имя пользователя"
          value={formData.username}
          onChange={handleChange}
          required
        />
      )}
      <input
        type="email"
        name="email"
        placeholder="Email"
        value={formData.email}
        onChange={handleChange}
        required
      />
      <input
        type="password"
        name="password"
        placeholder="Пароль"
        value={formData.password}
        onChange={handleChange}
        required
        minLength="6"
      />
      <button type="submit">
        {isLogin ? 'Войти' : 'Зарегистрироваться'}
      </button>
    </form>
  );
}

export default AuthForm;