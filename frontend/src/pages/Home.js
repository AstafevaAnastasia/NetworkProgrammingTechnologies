import React, { useEffect, useState } from 'react';
import WeatherCard from '../components/WeatherCard';
import weatherService from '../api/weatherService';
import { authFetch } from '../api/http';
import '../styles/main.css';

const DEFAULT_CITY_IDS = [1, 2]; // Только 1 и 2 как просили

function Home({ user }) {
  const [favoriteWeather, setFavoriteWeather] = useState([]);
  const [popularWeather, setPopularWeather] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Всегда загружаем популярные города
        const popularData = await weatherService.getMultipleCities(DEFAULT_CITY_IDS);
        setPopularWeather(popularData);

        // Загружаем избранные если пользователь авторизован
        if (user) {
          await fetchFavorites();
        }
      } catch (err) {
        console.error('Ошибка при загрузке данных:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user]);

  const fetchFavorites = async () => {
    try {
      const response = await authFetch(`/users/${user.id}/favorites/weather`);
      if (!response.ok) throw new Error('Failed to fetch favorites');

      const data = await response.json();
      const formattedData = (data.favorite_cities_weather || []).map(item => ({
        id: item.city.id,
        city_id: item.city.id,
        city: item.city.name,
        temp: Math.round(item.weather.temperature),
        description: item.weather.description,
        humidity: item.weather.humidity,
        wind_speed: item.weather.wind_speed,
        timestamp: item.weather.timestamp
      }));

      setFavoriteWeather(formattedData);
    } catch (err) {
      console.error('Ошибка при загрузке избранных:', err);
      throw err;
    }
  };

  const toggleFavorite = async (cityId) => {
    try {
      const isFavorite = favoriteWeather.some(city => city.id === cityId);

      if (isFavorite) {
        await authFetch(`/users/${user.id}/favorites/${cityId}`, {
          method: 'DELETE'
        });
      } else {
        await authFetch(`/users/${user.id}/favorites`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ city_id: cityId })
        });
      }

      // Обновляем список избранных
      await fetchFavorites();
    } catch (err) {
      console.error('Ошибка при обновлении избранных:', err);
      setError(err.message);
    }
  };

  if (loading) return <div className="loading">Загрузка данных...</div>;
  if (error) return <div className="error-message">Ошибка: {error}</div>;

  return (
    <div className="home">
      {user && favoriteWeather.length > 0 && (
        <>
          <h2>Ваши избранные города</h2>
          <div className="weather-grid">
            {favoriteWeather.map((data) => (
              <WeatherCard
                key={`fav-${data.id}`}
                data={data}
                onToggleFavorite={toggleFavorite}
                isFavorite={true}
              />
            ))}
          </div>
        </>
      )}

      <h2>Популярные города</h2>
      <div className="weather-grid">
        {popularWeather.map((data) => {
          const isFavorite = user && favoriteWeather.some(city => city.id === data.id);
          return (
            <WeatherCard
              key={`pop-${data.id}`}
              data={data}
              onToggleFavorite={user ? toggleFavorite : null}
              isFavorite={isFavorite}
            />
          );
        })}
      </div>
    </div>
  );
}

export default Home;