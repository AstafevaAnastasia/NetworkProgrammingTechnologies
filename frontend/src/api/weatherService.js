/**
 * Сервис для работы с погодой через ваш бэкенд
 * Все методы возвращают Promise с заглушками
 */

export default {
  /**
   * Получить погоду для одного города
   * @param {string} city - Название города
   * @returns {Promise} - Заглушка данных
   */
  getCityWeather(city) {
    return Promise.resolve({
      city,
      temp: 20 + Math.round(Math.random() * 10), // Рандомная температура
      description: 'Ясно',
      humidity: 65,
      icon: '01d'
    });
  },

  /**
   * Получить погоду для нескольких городов
   * @param {string[]} cities - Массив городов
   * @returns {Promise} - Заглушка данных
   */
  getMultipleCities(cities) {
    return Promise.all(cities.map(city => this.getCityWeather(city)));
  }
};