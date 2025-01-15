// frontend/src/axios.ts
import axios from 'axios';

// Base URL for FastAPI backend
const api = axios.create({
    baseURL: 'http://127.0.0.1:8000', // Your FastAPI backend URL
    headers: {
        'Content-Type': 'application/json',
    },
});

export default api;
