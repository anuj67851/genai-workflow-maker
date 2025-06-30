import { create } from 'zustand';
import {
    addEdge,
    applyNodeChanges,
    applyEdgeChanges,
} from 'reactflow';

// Zustand is a small, fast and scaleable bearbones state-management solution.
// It creates a "store" that can be accessed by any component.
// This store will hold the state of our workflow builder canvas.

const useWorkflowStore = create((set, get) => ({
    // --- STATE ---
    nodes: [],
    edges: [],
    workflowName: 'Untitled Workflow',
    workflowDescription: '',
    tools: [], // To be populated from the API

    // --- ACTIONS ---

    // Called by React Flow when nodes or edges are moved or selected
    onNodesChange: (changes) => {
        set({
            nodes: applyNodeChanges(changes, get().nodes),
        });
    },
    onEdgesChange: (changes) => {
        set({
            edges: applyEdgeChanges(changes, get().edges),
        });
    },
    // Called when a new connection is made between two nodes
    onConnect: (connection) => {
        set({
            edges: addEdge(connection, get().edges),
        });
    },

    // Action to add a new node to the canvas (e.g., from the sidebar)
    addNode: (newNode) => {
        set({ nodes: [...get().nodes, newNode] });
    },

    // Action to update the data of a specific node
    updateNodeData: (nodeId, newData) => {
        set({
            nodes: get().nodes.map((node) => {
                if (node.id === nodeId) {
                    // Merge the new data with existing data
                    return { ...node, data: { ...node.data, ...newData } };
                }
                return node;
            }),
        });
    },

    // Action to set the entire state, used when loading a workflow
    setFlow: (flow) => {
        set({
            nodes: flow.nodes || [],
            edges: flow.edges || [],
            workflowName: flow.name || 'Untitled Workflow',
            workflowDescription: flow.description || ''
        });
    },

    // Action to fetch available tools from the backend API
    fetchTools: async () => {
        try {
            // The vite.config.js proxy will redirect this to http://localhost:8000/api/tools
            const response = await fetch('/api/tools');
            if (!response.ok) {
                throw new Error('Failed to fetch tools');
            }
            const tools = await response.json();
            set({ tools: tools });
        } catch (error) {
            console.error("Error fetching tools:", error);
            set({ tools: [] });
        }
    },

    // Action to set workflow metadata
    setWorkflowName: (name) => set({ workflowName: name }),
    setWorkflowDescription: (description) => set({ workflowDescription: description }),

}));

export default useWorkflowStore;