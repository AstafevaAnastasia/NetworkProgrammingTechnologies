import React from 'react';
import '../styles/main.css';

function Navbar({ user, setPage }) {
  return (
    <nav>
      <button onClick={() => setPage('home')}>Главная</button>
      {user ? (
        <button onClick={() => setPage('profile')}>Профиль</button>
      ) : (
        <button onClick={() => setPage('auth')}>Войти</button>
      )}
    </nav>
  );
}

export default Navbar;