import React from 'react';
import { useNavigate } from 'react-router-dom';
import { authFetch, clearAuth } from '../api/http';
import '../styles/main.css';

function Navbar({ user, setUser }) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await authFetch('/logout', { method: 'POST' });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearAuth();
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