export async function authFetch(url, options = {}) {
  const token = localStorage.getItem('access_token');

  if (!token) {
    // Optional: direct redirect if no token is found at all
    localStorage.setItem('logout_message', 'You need to log in to continue.');
    window.location.href = "/auth/login";
    return;
  }

  const method = options.method || 'GET';

  const headers = {
    ...(options.headers || {}),
    Authorization: `Bearer ${token}`,
    ...(method !== 'GET' ? { 'Content-Type': 'application/json' } : {}),
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      console.warn(`[authFetch] 401 Unauthorized: ${url}`);
      localStorage.removeItem('access_token');
      localStorage.setItem('logout_message', 'Your session expired. Please log in again.');
      window.location.href = "/auth/login";
      return;
    }

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status} - ${errorText}`);
    }

    return response;
  } catch (error) {
    console.error('[authFetch] Fetch error:', error);
    throw error;
  }
}
