import { authFetch } from './http';

export default {
  /**
   * Получить погоду для города по ID
   * @param {number} cityId - ID города
   * @returns {Promise} - Данные о погоде
   */
  async getCityWeather(cityId) {
    try {
      const response = await authFetch(`/weather/${cityId}`);
      if (!response.ok) throw new Error('Failed to fetch weather data');

      const data = await response.json();
      if (!data.weather_data || data.weather_data.length === 0) {
        throw new Error('No weather data available');
      }

      // Берем последнюю запись о погоде
      const latestWeather = data.weather_data[0];

      return {
        id: data.city.id,
        city_id: data.city.id,
        city: data.city.name,
        temp: Math.round(latestWeather.temperature),
        description: latestWeather.description,
        humidity: latestWeather.humidity,
        wind_speed: latestWeather.wind_speed,
        timestamp: latestWeather.timestamp
      };
    } catch (error) {
      console.error('Error fetching weather:', error);
      throw error;
    }
  },

  /**
   * Получить погоду для нескольких городов по их ID
   * @param {number[]} cityIds - Массив ID городов
   * @returns {Promise} - Массив данных о погоде
   */
  async getMultipleCities(cityIds) {
    try {
      const promises = cityIds.map(id => this.getCityWeather(id));
      return await Promise.all(promises);
    } catch (error) {
      console.error('Error fetching multiple cities weather:', error);
      throw error;
    }
  },

  /**
   * Добавить город в базу данных (админ)
   * @param {string} cityName - Название города
   * @returns {Promise} - Добавленный город
   */
  async addCity(cityName) {
    try {
      const response = await authFetch('/cities', {
        method: 'POST',
        body: JSON.stringify({ name: cityName })
      });
      if (!response.ok) throw new Error('Failed to add city');
      return await response.json();
    } catch (error) {
      console.error('Error adding city:', error);
      throw error;
    }
  },

  /**
   * Удалить город из базы (админ)
   * @param {number} cityId - ID города
   * @returns {Promise} - Результат удаления
   */
  async deleteCity(cityId) {
    try {
      const response = await authFetch(`/cities/${cityId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete city');
      return await response.json();
    } catch (error) {
      console.error('Error deleting city:', error);
      throw error;
    }
  },

  /**
   * Обновить почасовые данные о погоде (админ)
   * @param {number} cityId - ID города
   * @returns {Promise} - Результат обновления
   */
  async updateHourlyWeather(cityId) {
    try {
      const response = await authFetch(`/weather/update_hourly/${cityId}`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to update hourly weather');
      return await response.json();
    } catch (error) {
      console.error('Error updating hourly weather:', error);
      throw error;
    }
  },

  /**
   * Очистить старые данные о погоде (админ)
   * @returns {Promise} - Результат очистки
   */
  async cleanupOldWeatherData() {
    try {
      const response = await authFetch('/weather/cleanup', {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to cleanup weather data');
      return await response.json();
    } catch (error) {
      console.error('Error cleaning old weather data:', error);
      throw error;
    }
  },
  /**
 * Получить список всех городов
 * @returns {Promise} - Список городов
 */
  async getAllCities() {
    try {
      const response = await authFetch('/cities');
      if (!response.ok) throw new Error('Failed to fetch cities');
      return await response.json();
    } catch (error) {
      console.error('Error fetching cities:', error);
      throw error;
    }
  },

  /**
   * Поиск пользователей (админ)
   * @param {string} username - Имя пользователя
   * @param {string} email - Email
   * @returns {Promise} - Список пользователей
   */
  async searchUsers(username, email) {
    try {
      const params = new URLSearchParams();
      if (username) params.append('username', username);
      if (email) params.append('email', email);

      const response = await authFetch(`/users/search?${params.toString()}`);
      if (!response.ok) throw new Error('Failed to search users');
      return await response.json();
    } catch (error) {
      console.error('Error searching users:', error);
      throw error;
    }
  },

  /**
   * Получить серверное время
   * @returns {Promise} - Серверное время
   */
  async getServerTime() {
    try {
      const response = await authFetch('/server_time');
      if (!response.ok) throw new Error('Failed to get server time');
      return await response.json();
    } catch (error) {
      console.error('Error getting server time:', error);
      throw error;
    }
  },

  /**
   * Получить информацию о пользователе
   * @param {number} userId - ID пользователя
   * @returns {Promise} - Данные пользователя
   */
  async getUserInfo(userId) {
    try {
      const response = await authFetch(`/users/${userId}`);
      if (!response.ok) throw new Error('Failed to get user info');
      return await response.json();
    } catch (error) {
      console.error('Error getting user info:', error);
      throw error;
    }
  },

  /**
   * Удалить пользователя (админ)
   * @param {number} userId - ID пользователя
   * @returns {Promise} - Результат удаления
   */
  async deleteUser(userId) {
    try {
      const response = await authFetch(`/users/${userId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete user');
      return await response.json();
    } catch (error) {
      console.error('Error deleting user:', error);
      throw error;
    }
  },

  /**
   * Обновить погодные данные для избранных городов пользователя
   * @param {number} userId - ID пользователя
   * @returns {Promise} - Обновленные данные
   */
  async updateFavoriteCitiesWeather(userId) {
    try {
      const response = await authFetch(`/users/${userId}/favorites/weather`);
      if (!response.ok) throw new Error('Failed to update favorites weather');
      return await response.json();
    } catch (error) {
      console.error('Error updating favorites weather:', error);
      throw error;
    }
  }
};