import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import weatherService from '../api/weatherService';
import { authFetch, clearAuth } from '../api/http';
import '../styles/main.css';

function Profile({ user, setUser }) {
  const [serverTime, setServerTime] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [updateError, setUpdateError] = useState(null);
  const [updateSuccess, setUpdateSuccess] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchServerTime();
    }
  }, [user]);

  const fetchServerTime = async () => {
    try {
      const time = await weatherService.getServerTime();
      setServerTime(time);
    } catch (error) {
      console.error('Failed to get server time:', error);
    }
  };

  const handleUpdateAccount = async (updateData) => {
    try {
      setUpdateError(null);
      setUpdateSuccess(null);

      const response = await authFetch('/update-account', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      });

      const result = await response.json();

      if (response.ok) {
        localStorage.setItem('user', JSON.stringify(result.user));
        if (setUser && typeof setUser === 'function') {
          setUser(result.user);
        }
        setUpdateSuccess('Данные успешно обновлены');
        setTimeout(() => setUpdateSuccess(null), 3000);
      } else {
        throw new Error(result.error || 'Не удалось обновить данные');
      }
    } catch (error) {
      console.error('Update failed:', error);
      setUpdateError(error.message);
      setTimeout(() => setUpdateError(null), 3000);
    }
  };

  const handleSearchUsers = async () => {
    try {
      const results = await weatherService.searchUsers(searchTerm, '');
      setSearchResults(results);
    } catch (error) {
      console.error('Search failed:', error);
      setUpdateError('Ошибка при поиске пользователей');
      setTimeout(() => setUpdateError(null), 3000);
    }
  };

  const handleCleanupWeather = async () => {
    try {
      const result = await weatherService.cleanupOldWeatherData();
      setUpdateSuccess(`Очистка данных выполнена: ${result.message}`);
      setTimeout(() => setUpdateSuccess(null), 3000);
    } catch (error) {
      setUpdateError('Ошибка при очистке данных');
      setTimeout(() => setUpdateError(null), 3000);
    }
  };

  const handleAddCity = async () => {
    const cityName = prompt('Введите название города:');
    if (cityName) {
      try {
        const result = await weatherService.addCity(cityName);
        setUpdateSuccess(`Город добавлен: ${result.city.name}`);
        setTimeout(() => setUpdateSuccess(null), 3000);
      } catch (error) {
        setUpdateError('Не удалось добавить город');
        setTimeout(() => setUpdateError(null), 3000);
      }
    }
  };

  const handleLogout = async () => {
    try {
      await authFetch('/logout', { method: 'POST' });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearAuth();
      if (setUser && typeof setUser === 'function') {
        setUser(null);
      }
      navigate('/auth');
    }
  };

  return (
    <div className="profile">
      <div className="profile-header">
        <h1>Мой профиль</h1>
        <div className="user-avatar">
          {user?.username?.charAt(0).toUpperCase() || 'U'}
        </div>
        {user?.role === 'admin' && <span className="admin-badge">ADMIN</span>}
      </div>

      {updateError && <div className="error-message">{updateError}</div>}
      {updateSuccess && <div className="success-message">{updateSuccess}</div>}

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
          <div className="info-row">
            <span className="info-label">Роль:</span>
            <span className="info-value">{user?.role || 'user'}</span>
          </div>
        </div>

        <div className="settings-card">
          <h3>Настройки профиля</h3>
          <div className="settings-buttons">
            <button
              className="settings-button"
              onClick={() => {
                const newUsername = prompt('Новое имя пользователя:', user?.username);
                if (newUsername && newUsername !== user?.username) {
                  handleUpdateAccount({ username: newUsername });
                }
              }}
            >
              Изменить имя пользователя
            </button>
            <button
              className="settings-button"
              onClick={() => {
                const newEmail = prompt('Новый email:', user?.email);
                if (newEmail && newEmail !== user?.email) {
                  handleUpdateAccount({ email: newEmail });
                }
              }}
            >
              Изменить email
            </button>
            <button
              className="settings-button"
              onClick={() => {
                const oldPass = prompt('Текущий пароль:');
                const newPass = prompt('Новый пароль:');
                if (oldPass && newPass) {
                  handleUpdateAccount({
                    old_password: oldPass,
                    new_password: newPass
                  });
                }
              }}
            >
              Изменить пароль
            </button>
            <button
              className="settings-button logout-button"
              onClick={handleLogout}
            >
              Выйти из аккаунта
            </button>
          </div>
        </div>
      </div>

      {user?.role === 'admin' && (
        <div className="admin-panel">
          <h2>Административные функции</h2>

          <div className="search-users">
            <input
              type="text"
              placeholder="Поиск пользователей..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
            <button
              className="search-button"
              onClick={handleSearchUsers}
            >
              Поиск
            </button>

            {searchResults.length > 0 && (
              <div className="search-results">
                <h4>Результаты поиска:</h4>
                <ul>
                  {searchResults.map(user => (
                    <li key={user.id}>
                      {user.username} ({user.email})
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="admin-actions">
            <button
              className="admin-button"
              onClick={handleAddCity}
            >
              Добавить город
            </button>
            <button
              className="admin-button"
              onClick={handleCleanupWeather}
            >
              Очистить старые данные
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Profile;