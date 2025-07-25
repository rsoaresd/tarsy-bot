import '@testing-library/jest-dom';

// Mock environment variables for tests
(import.meta as any).env = {
  VITE_API_BASE_URL: 'http://localhost:8000',
  VITE_WS_BASE_URL: 'ws://localhost:8000'
}; 