# GenAI Visual Workflow Builder

This project provides a full-stack application for visually building, managing, and executing complex, AI-driven workflows. It features a React-based drag-and-drop interface and a powerful FastAPI backend that leverages the `genai_workflows` library.

## Features

-   **Visual Builder:** A drag-and-drop canvas using React Flow to design workflows.
-   **Node-Based Logic:** Create flows using distinct node types:
    -   **Tool Node:** Have an LLM agent select and use a specific tool.
    -   **Condition Node:** Branch your workflow based on dynamic, LLM-evaluated conditions.
    -   **Human Input Node:** Pause the workflow to ask the user for information.
    -   **LLM Response Node:** Generate a final, synthesized response to the user.
-   **Context-Aware Editing:** The UI helps you write prompts by showing available input variables from connected steps.
-   **Workflow Executor:** A chat interface to run your saved workflows and interact with them.
-   **FastAPI Backend:** A robust and scalable backend serving a REST API for all workflow operations.

## Project Structure

```
.
├── backend/            # FastAPI application
└── frontend/           # React application
```

---

## 1. Backend Setup

The backend is a Python FastAPI server that uses the `genai_workflows` library.

### Prerequisites

-   Python 3.9+
-   An OpenAI API Key

### Installation

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**
    Create a file named `.env` in the `backend` directory and add your OpenAI API key:
    ```
    OPENAI_API_KEY="sk-..."
    ```

### Running the Backend

From the `backend` directory, run the FastAPI server using Uvicorn:

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. You can see the auto-generated documentation at `http://localhost:8000/docs`.

---

## 2. Frontend Setup

The frontend is a React application built with Vite for a fast development experience.

### Prerequisites

-   Node.js 18+ and npm

### Installation

1.  **Navigate to the frontend directory:**
    ```bash
    cd frontend
    ```

2.  **Install the required npm packages:**
    ```bash
    npm install
    ```

### Running the Frontend

From the `frontend` directory, run the development server:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`. The frontend is pre-configured to proxy API requests to the backend server running on port 8000.

---

## How It Works

1.  **Build:** Use the visual builder on the homepage to drag nodes onto the canvas. Select a node to open the Inspector Panel, where you can define its properties (e.g., write a prompt for a Condition Node). Connect the nodes' handles to define the flow of execution.
2.  **Save:** Click the "Save Workflow" button. The frontend sends the structure of your graph (nodes and edges) to the backend API (`POST /api/workflows`). The backend translates this graph into a `Workflow` object that the `genai_workflows` engine can understand and saves it to the database.
3.  **Run:** Navigate to the "Run Workflows" page. Select a workflow and start a conversation. The UI communicates with the backend execution endpoints (`/api/executions/*`) to run the workflow logic, pausing and resuming as needed based on your design.