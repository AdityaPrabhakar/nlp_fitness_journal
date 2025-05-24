// static/js/checkAuth.js
export function enforceAuth(protectedElementId, fallbackElementId = null) {
  document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem('access_token');
    const protectedContent = document.getElementById(protectedElementId);
    const fallbackContent = fallbackElementId ? document.getElementById(fallbackElementId) : null;

    if (token) {
      if (protectedContent) protectedContent.classList.remove("hidden");
      if (fallbackContent) fallbackContent.classList.add("hidden");
    } else {
      console.warn("No access token found. Hiding protected content.");
      if (protectedContent) protectedContent.classList.add("hidden");
      if (fallbackContent) fallbackContent.classList.remove("hidden");
    }
  });
}
