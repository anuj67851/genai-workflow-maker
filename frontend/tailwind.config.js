/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Custom colors for nodes to match the backend visualization
                'node-tool': '#cde4ff',
                'node-condition': '#fff2cc',
                'node-human': '#d4edda',
                'node-response': '#d1ecf1',
                'node-start': '#f8f9fa',
            },
            borderColor: {
                'node-tool': '#6ab0ff',
                'node-condition': '#ffdf7a',
                'node-human': '#79d18b',
                'node-response': '#76c5d1',
                'node-start': '#ced4da',
            }
        },
    },
    plugins: [],
}