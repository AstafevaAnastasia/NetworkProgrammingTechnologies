import React from 'react';
import '../styles/main.css';

function Profile({ user }) {
  return (
    <div className="profile">
      <div className="profile-header">
        <h1>Мой профиль</h1>
        <div className="user-avatar">
          {user?.username?.charAt(0).toUpperCase() || 'U'}
        </div>
      </div>

      <div className="profile-info">
        <div className="info-card">
          <h3>Основная информация</h3>
          <div className="info-row">
            <span className="info-label">Логин:</span>
            <span className="info-value">{user?.username || 'Не указан'}</span>
          </div>
          <div className="info-row">
            <span className="info-label">Email:</span>
            <span className="info-value">{user?.email || 'Не указан'}</span>
          </div>
        </div>

        <div className="settings-card">
          <h3>Настройки профиля</h3>
          <div className="setting-item">
            <label className="switch">
              <input type="checkbox" />
              <span className="slider round"></span>
            </label>
            <span>Тёмная тема</span>
          </div>
          <div className="setting-item">
            <label className="switch">
              <input type="checkbox" defaultChecked />
              <span className="slider round"></span>
            </label>
            <span>Уведомления по email</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Profile;