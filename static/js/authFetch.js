export async function authFetch(url, options = {}) {
  const token = localStorage.getItem('access_token');
  if (!token) {
    throw new Error('No access token found.');
  }
  console.log(token)

  const method = options.method || 'GET';

  const headers = {
    ...(options.headers || {}),
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(method !== 'GET' ? { 'Content-Type': 'application/json' } : {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    console.warn(`[authFetch] Unauthorized: ${url}`);
    throw new Error('Unauthorized');
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status} - ${errorText}`);
  }

  return response;
}
