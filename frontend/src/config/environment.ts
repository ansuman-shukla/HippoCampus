// Environment configuration for the application
export const config = {
  BACKEND_URL: import.meta.env.VITE_BACKEND_URL,
  API_URL: import.meta.env.VITE_API_URL,
  SUPABASE_URL: import.meta.env.VITE_SUPABASE_URL,
  SUPABASE_ANON_KEY: import.meta.env.VITE_SUPABASE_ANON_KEY,
};

// For use in public scripts (background.js, content.js)
// This will be injected during build process
export const getEnvironmentConfig = () => {
  return {
    BACKEND_URL: '__VITE_BACKEND_URL__',
    API_URL: '__VITE_API_URL__'
  };
};
