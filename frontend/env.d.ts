/// <reference types="vite/client" />
/// <reference types="@types/google.maps" />
export {}

interface Window {
  google: typeof google
}

VUE_APP_API_BASE_URL=http://localhost:8000