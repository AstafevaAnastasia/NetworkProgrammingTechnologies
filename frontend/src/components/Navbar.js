import React from 'react';
import { useNavigate } from 'react-router-dom';
import { authFetch } from '../api/http';
import '../styles/main.css';

function Navbar({ user, setUser }) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      // Отправляем запрос на выход
      const response = await authFetch('http://127.0.0.1:5000/auth/logout', {
        method: 'POST'
      });

      if (response.ok) {
        // Полностью очищаем данные аутентификации
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        setUser(null); // Сбрасываем состояние пользователя
        navigate('/auth'); // Перенаправляем на страницу входа
      } else {
        console.error('Logout failed:', await response.json());
      }
    } catch (error) {
      console.error('Logout error:', error);
      // В любом случае очищаем данные и перенаправляем
      localStorage.clear();
      setUser(null);
      navigate('/auth');
    }
  };

  return (
    <nav>
      <button onClick={() => navigate('/')}>Главная</button>
      {user ? (
        <>
          <button onClick={() => navigate('/profile')}>Профиль</button>
          <button onClick={handleLogout}>Выйти</button>
        </>
      ) : (
        <button onClick={() => navigate('/auth')}>Войти</button>
      )}
    </nav>
  );
}

export default Navbar;