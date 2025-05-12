import React, { useEffect, useState } from 'react';
import WeatherCard from '../components/WeatherCard';
import weatherService from '../api/weatherService';
import { authFetch } from '../api/http';
import '../styles/main.css';

function Home({ user }) {
  const [favoriteWeather, setFavoriteWeather] = useState([]);
  const [availableWeather, setAvailableWeather] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Дефолтные города, которые точно есть в базе
  const DEFAULT_CITY_IDS = [3, 5, 6, 7, 8];

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // 1. Загружаем погоду для дефолтных городов
        const defaultWeather = await weatherService.getMultipleCities(DEFAULT_CITY_IDS);

        // 2. Если пользователь авторизован, загружаем его избранные города
        let combinedWeather = [...defaultWeather];
        if (user) {
          try {
            const favResponse = await authFetch(`/users/${user.id}/favorites/weather`);
            if (favResponse.ok) {
              const favData = await favResponse.json();
              const favCities = favData.favorite_cities_weather || [];

              // Добавляем уникальные города из избранного
              favCities.forEach(fav => {
                const exists = combinedWeather.some(city => city.id === fav.city.id);
                if (!exists) {
                  combinedWeather.push({
                    id: fav.city.id,
                    city_id: fav.city.id,
                    city: fav.city.name,
                    temp: Math.round(fav.weather.temperature),
                    description: fav.weather.description,
                    humidity: fav.weather.humidity,
                    wind_speed: fav.weather.wind_speed,
                    timestamp: fav.weather.timestamp
                  });
                }
              });

              // Сохраняем отдельно избранные города для секции "Избранное"
              const formattedFavorites = favCities.map(item => ({
                id: item.city.id,
                city_id: item.city.id,
                city: item.city.name,
                temp: Math.round(item.weather.temperature),
                description: item.weather.description,
                humidity: item.weather.humidity,
                wind_speed: item.weather.wind_speed,
                timestamp: item.weather.timestamp
              }));
              setFavoriteWeather(formattedFavorites);
            }
          } catch (favError) {
            console.error('Ошибка загрузки избранных:', favError);
          }
        }

        setAvailableWeather(combinedWeather);
      } catch (err) {
        console.error('Ошибка при загрузке данных:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user]);

  const toggleFavorite = async (cityId) => {
    if (!user) return;

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
      const favResponse = await authFetch(`/users/${user.id}/favorites/weather`);
      if (favResponse.ok) {
        const favData = await favResponse.json();
        const formattedFavorites = (favData.favorite_cities_weather || []).map(item => ({
          id: item.city.id,
          city_id: item.city.id,
          city: item.city.name,
          temp: Math.round(item.weather.temperature),
          description: item.weather.description,
          humidity: item.weather.humidity,
          wind_speed: item.weather.wind_speed,
          timestamp: item.weather.timestamp
        }));
        setFavoriteWeather(formattedFavorites);
      }
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

      <h2>Доступные города</h2>
      <div className="weather-grid">
        {availableWeather.map((data) => {
          const isFavorite = user && favoriteWeather.some(city => city.id === data.id);
          return (
            <WeatherCard
              key={`city-${data.id}`}
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