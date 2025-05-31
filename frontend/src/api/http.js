// Определяем базовый URL API в зависимости от среды
const API_BASE_URL = process.env.NODE_ENV === 'development'
  ? 'http://localhost:5000'
  : '/api';

// Универсальный fetch-запрос
export const basicFetch = async (url, options = {}) => {
  const fullUrl = API_BASE_URL.startsWith('http')
    ? `${API_BASE_URL}${url}`
    : `${window.location.origin}${API_BASE_URL}${url}`;

  try {
    const response = await fetch(fullUrl, {
      ...options,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Request failed with status ${response.status}`);
    }

    return response;
  } catch (error) {
    console.error('API request failed:', error.message, 'URL:', fullUrl);
    throw error;
  }
};

// Авторизованный fetch
export const authFetch = async (url, options = {}) => {
  const token = localStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token');

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) headers.Authorization = `Bearer ${token}`;

  try {
    let response = await basicFetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401 && refreshToken) {
      try {
        const refreshResponse = await basicFetch('/refresh', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${refreshToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (refreshResponse.ok) {
          const { access_token } = await refreshResponse.json();
          localStorage.setItem('access_token', access_token);
          headers.Authorization = `Bearer ${access_token}`;
          response = await basicFetch(url, {
            ...options,
            headers,
          });
        } else {
          clearAuth();
          throw new Error('Session expired');
        }
      } catch (refreshError) {
        clearAuth();
        throw refreshError;
      }
    }

    if (response.status === 401) {
      clearAuth();
      throw new Error('Authorization required');
    }

    return response;
  } catch (error) {
    console.error('Auth request failed:', error.message);
    throw error;
  }
};

// Остальные функции
export const clearAuth = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};

export const isAuthenticated = () => !!localStorage.getItem('access_token');

export const getCurrentUser = () => {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
};