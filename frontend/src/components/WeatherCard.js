import React from 'react';
import { FaStar, FaRegStar } from 'react-icons/fa';
import '../styles/WeatherCard.css';

function WeatherCard({ data, onToggleFavorite, isFavorite }) {
  const formatDate = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  return (
    <div className="weather-card">
      <div className="card-header">
        <h3>{data.city}</h3>
        {onToggleFavorite && (
          <button
            className="favorite-btn"
            onClick={(e) => {
              e.stopPropagation();
              onToggleFavorite(data.id);
            }}
            aria-label={isFavorite ? "Удалить из избранного" : "Добавить в избранное"}
          >
            {isFavorite ? <FaStar color="gold" size={20} /> : <FaRegStar size={20} />}
          </button>
        )}
      </div>
      <div className="weather-main">
        <span className="temp">{data.temp}°C</span>
        <span className="description">{data.description}</span>
      </div>
      <div className="weather-details">
        <p>Влажность: {data.humidity}%</p>
        <p>Ветер: {data.wind_speed} м/с</p>
        {data.timestamp && <p className="timestamp">{formatDate(data.timestamp)}</p>}
      </div>
    </div>
  );
}

export default WeatherCard;