import React from 'react';
import '../styles/main.css';

function Profile({ user }) {
  return (
    <div className="profile">
      <h1>Профиль</h1>
      <p>Email: {user?.email}</p>
      <div className="settings">
        <h3>Настройки</h3>
        <label>
          <input type="checkbox" /> Тёмная тема
        </label>
      </div>
    </div>
  );
}

export default Profile;