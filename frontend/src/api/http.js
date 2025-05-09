const API_BASE_URL = 'http://127.0.0.1:5000';

export const basicFetch = async (url, options = {}) => {
  try {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || 'Request failed');
    }

    return response;
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};

export const authFetch = async (url, options = {}) => {
  const token = localStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token');

  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) headers['Authorization'] = `Bearer ${token}`;

  try {
    let response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers,
    });

    if (response.status === 401 && refreshToken) {
      try {
        const refreshResponse = await fetch(`${API_BASE_URL}/refresh`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${refreshToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (refreshResponse.ok) {
          const { access_token } = await refreshResponse.json();
          localStorage.setItem('access_token', access_token);
          headers['Authorization'] = `Bearer ${access_token}`;
          response = await fetch(`${API_BASE_URL}${url}`, {
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
    console.error('API request failed:', error);
    throw error;
  }
};

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