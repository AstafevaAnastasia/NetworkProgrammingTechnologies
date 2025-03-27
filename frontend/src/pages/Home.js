import React, { useEffect, useState } from 'react';
import WeatherCard from '../components/WeatherCard';
import weatherService from '../api/weatherService';
import '../styles/main.css';

function Home() {
  const [cities] = useState(['Moscow', 'London', 'New York', 'Tokyo']);
  const [weatherData, setWeatherData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    weatherService.getMultipleCities(cities)
      .then(data => {
        setWeatherData(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('Ошибка при загрузке данных:', error);
        setLoading(false);
      });
  }, [cities]);

  if (loading) return <div className="loading">Загрузка данных...</div>;

  return (
    <div className="home">
      <h1>Погода в крупных городах</h1>
      <div className="weather-grid">
        {weatherData.map((data, index) => (
          <WeatherCard key={index} data={data} />
        ))}
      </div>
    </div>
  );
}

export default Home;