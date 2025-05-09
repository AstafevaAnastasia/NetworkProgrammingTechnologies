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
  }
};