// API base URL configuration:
// - Empty string "" = same-origin (when backend uvicorn serves the frontend locally)
// - For Vercel deployment: Set to your live Render backend URL, e.g. "https://scholarswarm-backend.onrender.com"
// - You can also override dynamically at runtime via localStorage.setItem("ss_api_base", "https://your-backend.onrender.com")
window.API_BASE = window.API_BASE || localStorage.getItem("ss_api_base") || "";

