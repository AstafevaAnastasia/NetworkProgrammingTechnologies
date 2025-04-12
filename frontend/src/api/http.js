const API_BASE_URL = 'http://127.0.0.1:5000';

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
      credentials: 'include',
    });

    if (response.status === 401 && refreshToken) {
      try {
        const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${refreshToken}`,
            'Content-Type': 'application/json',
          },
          credentials: 'include',
        });

        if (refreshResponse.ok) {
          const { access_token } = await refreshResponse.json();
          localStorage.setItem('access_token', access_token);
          headers['Authorization'] = `Bearer ${access_token}`;
          response = await fetch(`${API_BASE_URL}${url}`, {
            ...options,
            headers,
            credentials: 'include',
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

export const logout = async () => {
  try {
    const response = await authFetch('/auth/logout', { method: 'POST' });
    clearAuth();
    return response;
  } catch (error) {
    console.error('Logout failed:', error);
    throw error;
  }
};

export const clearAuth = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
  document.cookie = 'access_token_cookie=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
  document.cookie = 'refresh_token_cookie=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
};

export const isAuthenticated = () => !!localStorage.getItem('access_token');

export const getCurrentUser = () => {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
};

export const authGet = (url, options = {}) => authFetch(url, { ...options, method: 'GET' });

export const authPost = (url, body, options = {}) => (
  authFetch(url, {
    ...options,
    method: 'POST',
    body: JSON.stringify(body),
  })
);

export const authPut = (url, body, options = {}) => (
  authFetch(url, {
    ...options,
    method: 'PUT',
    body: JSON.stringify(body),
  })
);

export const authDelete = (url, options = {}) => authFetch(url, { ...options, method: 'DELETE' });