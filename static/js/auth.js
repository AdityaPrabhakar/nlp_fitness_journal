// static/js/auth.js
const token = localStorage.getItem('access_token');
const protectedPaths = ['/', '/log', '/view-entries', '/log-entry'];

// Redirect to login if no token is found on protected pages
if (!token && protectedPaths.includes(window.location.pathname)) {
  window.location.href = '/auth/login';
}

// Show main content if token exists
if (token) {
  const mainContent = document.getElementById('main-content');
  if (mainContent) {
    mainContent.style.display = 'block';
  }
}
