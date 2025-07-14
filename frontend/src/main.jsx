import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx'
import './index.css'

// We are rendering the app directly without StrictMode for now
// to ensure maximum stability with the React Flow library and prevent
// potential double-rendering issues during this debugging phase.
ReactDOM.createRoot(document.getElementById('root')).render(
    <BrowserRouter>
        <App />
        <Toaster
            position="top-center"
            reverseOrder={false}
            toastOptions={{
                success: {
                    duration: 3000,
                },
                error: {
                    duration: 5000,
                },
                style: {
                    fontSize: '16px',
                    maxWidth: '500px',
                    padding: '16px 24px',
                },
            }}
        />
    </BrowserRouter>
);