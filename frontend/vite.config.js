import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173, // The port the frontend dev server will run on
        proxy: {
            // Proxy API requests to the backend server
            '/api': {
                target: 'http://localhost:8000', // The address of our FastAPI backend
                changeOrigin: true, // Needed for virtual hosted sites
                secure: false,      // If you are running your backend on https, set this to true
            },
        },
    },
})