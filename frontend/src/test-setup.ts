import '@testing-library/jest-dom'

// Mock chrome API for extension testing
global.chrome = {
  runtime: {
    sendMessage: () => {},
    onMessage: {
      addListener: () => {},
      removeListener: () => {}
    }
  },
  cookies: {
    get: () => {},
    getAll: () => {},
    set: () => {},
    remove: () => {},
    onChanged: {
      addListener: () => {},
      removeListener: () => {}
    }
  },
  tabs: {
    query: () => Promise.resolve([]),
    sendMessage: () => Promise.resolve({})
  },
  scripting: {
    executeScript: () => Promise.resolve([])
  }
} as any

// Mock environment variables
process.env.VITE_BACKEND_URL = 'http://localhost:8000'
process.env.VITE_API_URL = 'http://localhost:3000' 