const API_KEY = 'ваш_api_ключ'; // Получите на openweathermap.org

export async function fetchWeather(city) {
  const response = await fetch(
    `https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${API_KEY}&units=metric&lang=ru`
  );
  return response.json();
}