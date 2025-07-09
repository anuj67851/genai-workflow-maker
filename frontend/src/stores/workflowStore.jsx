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
    workflowId: null, // Keep track of the current workflow's ID
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
        // When connecting from a router, the handleId is the route name.
        // We need to ensure this is passed to the edge object.
        const newEdge = {
            ...connection,
            id: `edge-${connection.source}-${connection.target}-${connection.sourceHandle || 'default'}`,
            type: 'smoothstep', // A nicer edge type
        };
        set({
            edges: addEdge(newEdge, get().edges),
        });
    },
    addNode: (newNode) => {
        set({ nodes: [...get().nodes, newNode] });
    },
    updateNodeData: (nodeId, newData) => {
        set({
            nodes: get().nodes.map((node) => {
                if (node.id === nodeId) {
                    const updatedData = { ...node.data, ...newData };
                    return { ...node, data: updatedData };
                }
                return node;
            }),
        });
    },
    setFlow: (flow) => {
        set({
            workflowId: flow.id || null,
            nodes: flow.nodes || [],
            edges: flow.edges || [],
            workflowName: flow.name || 'Untitled Workflow',
            workflowDescription: flow.description || ''
        });
    },

    // This function gathers the current state into the format the backend API expects.
    getFlowAsJson: () => {
        const { nodes, edges, workflowName, workflowDescription } = get();

        // Create a mutable copy of nodes to update their data
        const processedNodes = JSON.parse(JSON.stringify(nodes));

        // Iterate over a copy of nodes to avoid mutation issues during loop
        for (const node of processedNodes) {
            if (node.data.action_type === 'condition_check') {
                // Find edges originating from this condition node's specific handles
                const successEdge = edges.find(e => e.source === node.id && e.sourceHandle === 'onSuccess');
                const failureEdge = edges.find(e => e.source === node.id && e.sourceHandle === 'onFailure');

                // Update the node's data with the correct next step IDs
                node.data.on_success = successEdge ? successEdge.target : 'END';
                node.data.on_failure = failureEdge ? failureEdge.target : 'END';
            } else if (node.data.action_type === 'intelligent_router') {
                // For the router, we rebuild the `routes` dictionary based on visual connections
                const newRoutes = {};
                const outgoingEdges = edges.filter(e => e.source === node.id);

                for (const edge of outgoingEdges) {
                    if (edge.sourceHandle) { // sourceHandle is the route name
                        newRoutes[edge.sourceHandle] = edge.target;
                    }
                }
                node.data.routes = newRoutes;

                // Routers don't use on_success/on_failure in the backend, but we clear them for consistency
                node.data.on_success = null;
                node.data.on_failure = null;
            } else if (node.type !== 'startNode' && node.type !== 'endNode') {
                // For all other standard nodes
                const successEdge = edges.find(e => e.source === node.id && (e.sourceHandle === null || e.sourceHandle === undefined));
                node.data.on_success = successEdge ? successEdge.target : 'END';

                // Standard nodes might have a failure path (e.g., http_request)
                const failureEdge = edges.find(e => e.source === node.id && e.sourceHandle === 'onFailure');
                if (failureEdge) {
                    node.data.on_failure = failureEdge.target;
                }
            }
        }

        return {
            name: workflowName,
            description: workflowDescription,
            // Return the processed nodes with updated routing data
            nodes: processedNodes,
            // The visual edges are still useful for re-loading the flow
            edges: edges,
        };
    },

    fetchTools: async () => {
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