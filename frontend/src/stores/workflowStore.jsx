import { create } from 'zustand';
import {
    addEdge,
    applyNodeChanges,
    applyEdgeChanges,
} from 'reactflow';
import axios from 'axios';

const useWorkflowStore = create((set, get) => ({
    // --- STATE ---
    nodes: [],
    edges: [],
    workflowName: 'Untitled Workflow',
    workflowDescription: '',
    tools: [],

    // --- ACTIONS ---

    // We intercept changes here to prevent the deletion of protected nodes.
    onNodesChange: (changes) => {
        const nonDeletableNodeIds = ['start', 'end'];

        // Filter out any 'remove' change that targets a protected node
        const filteredChanges = changes.filter(change => {
            if (change.type === 'remove' && nonDeletableNodeIds.includes(change.id)) {
                console.warn(`Attempted to delete protected node: ${change.id}. Ignoring.`);
                return false; // Exclude this change
            }
            return true; // Keep all other changes
        });

        set({
            nodes: applyNodeChanges(filteredChanges, get().nodes),
        });
    },

    onEdgesChange: (changes) => {
        set({
            edges: applyEdgeChanges(changes, get().edges),
        });
    },
    onConnect: (connection) => {
        set({
            edges: addEdge(connection, get().edges),
        });
    },
    addNode: (newNode) => {
        set({ nodes: [...get().nodes, newNode] });
    },
    updateNodeData: (nodeId, newData) => {
        set({
            nodes: get().nodes.map((node) => {
                if (node.id === nodeId) {
                    // Make sure to merge deeply to avoid overwriting nested data
                    const updatedData = { ...node.data, ...newData };
                    return { ...node, data: updatedData };
                }
                return node;
            }),
        });
    },
    setFlow: (flow) => {
        set({
            nodes: flow.nodes || [],
            edges: flow.edges || [],
            workflowName: flow.name || 'Untitled Workflow',
            workflowDescription: flow.description || ''
        });
    },
    removeElements: ({ nodesToRemove, edgesToRemove }) => {
        const nodes = get().nodes.filter(n => !nodesToRemove.some(ntr => ntr.id === n.id));
        const edges = get().edges.filter(e => !edgesToRemove.some(etr => etr.id === e.id));
        set({ nodes, edges });
    },

    fetchTools: async () => {
        // Prevent re-fetching if tools are already loaded
        if (get().tools.length > 0) return;
        try {
            const response = await axios.get('/api/tools');
            if (response.data) {
                set({ tools: response.data });
            }
        } catch (error) {
            console.error("Error fetching tools:", error);
            set({ tools: [] });
        }
    },
    setWorkflowName: (name) => set({ workflowName: name }),
    setWorkflowDescription: (description) => set({ workflowDescription: description }),
}));

export default useWorkflowStore;