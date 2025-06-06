import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authFetch, clearAuth } from '../api/http';
import '../styles/main.css';

function Profile({ user, setUser }) {
  const [serverTime, setServerTime] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [updateError, setUpdateError] = useState(null);
  const [updateSuccess, setUpdateSuccess] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchServerTime();
    }
  }, [user]);

  const fetchServerTime = async () => {
    try {
      const response = await authFetch('/server/time');
      const data = await response.json();
      setServerTime(data.time);
    } catch (error) {
      console.error('Failed to get server time:', error);
    }
  };

  const handleUpdateHourlyWeather = async (cityId) => {
    try {
      setUpdateError(null);
      setUpdateSuccess(null);
      setLoadingStatus('Обновление данных о погоде...');

      const response = await authFetch(`/weather/update_hourly/${cityId}`, {
        method: 'POST'
      });

      const result = await response.json();

      if (response.ok) {
        setUpdateSuccess(
          `Данные о погоде для города ${result.city_name} (ID: ${result.city_id}) успешно обновлены. ` +
          `Добавлено ${result.total_added} записей за период с ${new Date(result.time_range.start).toLocaleString()} ` +
          `по ${new Date(result.time_range.end).toLocaleString()}`
        );
      } else {
        throw new Error(result.error || 'Не удалось обновить данные о погоде');
      }
    } catch (error) {
      console.error('Weather update error:', error);
      setUpdateError(error.message);
    } finally {
      setLoadingStatus(null);
      setTimeout(() => {
        setUpdateSuccess(null);
        setUpdateError(null);
      }, 5000);
    }
  };

  const handleCleanupWeather = async () => {
    try {
      setUpdateError(null);
      setUpdateSuccess(null);
      setLoadingStatus('Идет очистка старых данных...');

      const response = await authFetch('/weather/cleanup', {
        method: 'DELETE'
      });

      const result = await response.json();

      if (response.ok) {
        setUpdateSuccess(
          `Очистка данных завершена. Удалено ${result.details.records_deleted} записей ` +
          `для ${result.details.cities_processed} городов. ` +
          `Удалены данные старше ${new Date(result.details.cutoff_date).toLocaleString()}`
        );
      } else {
        throw new Error(result.error || 'Не удалось выполнить очистку данных');
      }
    } catch (error) {
      console.error('Cleanup error:', error);
      setUpdateError(error.message);
    } finally {
      setLoadingStatus(null);
      setTimeout(() => {
        setUpdateSuccess(null);
        setUpdateError(null);
      }, 5000);
    }
  };

  const handleUpdateAccount = async (updateData) => {
    try {
      setUpdateError(null);
      setUpdateSuccess(null);
      setLoadingStatus('Обновление данных...');

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
      } else {
        throw new Error(result.error || 'Не удалось обновить данные');
      }
    } catch (error) {
      console.error('Update failed:', error);
      setUpdateError(error.message);
    } finally {
      setLoadingStatus(null);
      setTimeout(() => {
        setUpdateSuccess(null);
        setUpdateError(null);
      }, 3000);
    }
  };

  const handleSearchUsers = async () => {
    try {
      setLoadingStatus('Поиск пользователей...');
      const response = await authFetch(`/users/search?query=${searchTerm}`);
      const results = await response.json();
      setSearchResults(results);
    } catch (error) {
      console.error('Search failed:', error);
      setUpdateError('Ошибка при поиске пользователей');
    } finally {
      setLoadingStatus(null);
      setTimeout(() => setUpdateError(null), 3000);
    }
  };

  const handleAddCity = async () => {
    const cityName = prompt('Введите название города:');
    if (cityName) {
      try {
        setLoadingStatus('Добавление города...');
        const response = await authFetch('/cities', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ name: cityName })
        });
        const result = await response.json();
        setUpdateSuccess(`Город добавлен: ${result.city.name}`);
      } catch (error) {
        setUpdateError('Не удалось добавить город');
      } finally {
        setLoadingStatus(null);
        setTimeout(() => {
          setUpdateSuccess(null);
          setUpdateError(null);
        }, 3000);
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
      {loadingStatus && <div className="loading-message">{loadingStatus}</div>}

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
          {serverTime && (
            <div className="info-row">
              <span className="info-label">Время сервера:</span>
              <span className="info-value">{serverTime}</span>
            </div>
          )}
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
              disabled={!!loadingStatus}
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
              disabled={!!loadingStatus}
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
              disabled={!!loadingStatus}
            >
              Изменить пароль
            </button>
            <button
              className="settings-button logout-button"
              onClick={handleLogout}
              disabled={!!loadingStatus}
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
              disabled={!!loadingStatus}
            />
            <button
              className="search-button"
              onClick={handleSearchUsers}
              disabled={!!loadingStatus}
            >
              Поиск
            </button>

            {searchResults.length > 0 && (
              <div className="search-results">
                <h4>Результаты поиска:</h4>
                <ul>
                  {searchResults.map(user => (
                    <li key={user.id}>
                      {user.username} ({user.email}) - {user.role}
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
              disabled={!!loadingStatus}
            >
              {loadingStatus === 'Добавление города...' ? 'Добавление...' : 'Добавить город'}
            </button>
            <button
              className="admin-button"
              onClick={() => {
                const cityId = prompt('Введите ID города для обновления погоды:');
                if (cityId) {
                  handleUpdateHourlyWeather(cityId);
                }
              }}
              disabled={!!loadingStatus}
            >
              {loadingStatus === 'Обновление данных о погоде...' ? 'Обновление...' : 'Обновить погоду для города'}
            </button>
            <button
              className="admin-button"
              onClick={handleCleanupWeather}
              disabled={!!loadingStatus}
            >
              {loadingStatus === 'Идет очистка старых данных...' ? 'Очистка...' : 'Очистить старые данные'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Profile;