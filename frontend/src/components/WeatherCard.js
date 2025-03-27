import React from 'react';
import '../styles/WeatherCard.css';

function WeatherCard({ data }) {
  if (!data) return <div className="weather-card loading">Нет данных</div>;

  return (
    <div className="weather-card">
      <h3>{data.city}</h3>
      <p>{data.temp}°C</p>
      <p>{data.description}</p>
      <p>Влажность: {data.humidity}%</p>
    </div>
  );
}

export default WeatherCard;