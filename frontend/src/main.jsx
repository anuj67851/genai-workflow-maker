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
    </BrowserRouter>
);