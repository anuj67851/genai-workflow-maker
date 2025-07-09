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

        // We work on a deep copy to avoid mutating the live state.
        const processedNodes = JSON.parse(JSON.stringify(nodes));

        // Create a map of all edges for efficient lookup.
        const edgesBySource = edges.reduce((acc, edge) => {
            if (!acc[edge.source]) {
                acc[edge.source] = [];
            }
            acc[edge.source].push(edge);
            return acc;
        }, {});

        // Iterate over the processed nodes to update their connection data.
        for (const node of processedNodes) {
            // Skip Start and End nodes as they have no incoming logic.
            if (node.type === 'startNode' || node.type === 'endNode') {
                continue;
            }

            const outgoingEdges = edgesBySource[node.id] || [];

            // Clear any pre-existing connection data to ensure a clean slate.
            node.data.on_success = null;
            node.data.on_failure = null;

            if (node.data.action_type === 'condition_check') {
                // Find edges originating from this condition node's specific handles.
                const successEdge = outgoingEdges.find(e => e.sourceHandle === 'onSuccess');
                const failureEdge = outgoingEdges.find(e => e.sourceHandle === 'onFailure');

                // Update the node's data with the correct next step IDs.
                node.data.on_success = successEdge ? successEdge.target : 'END';
                node.data.on_failure = failureEdge ? failureEdge.target : 'END';

            } else if (node.data.action_type === 'intelligent_router') {
                // For the router, we rebuild the `routes` dictionary based on visual connections.
                const newRoutes = {};
                for (const edge of outgoingEdges) {
                    // sourceHandle is the route name, e.g., "billing_inquiry"
                    if (edge.sourceHandle) {
                        newRoutes[edge.sourceHandle] = edge.target;
                    }
                }
                node.data.routes = newRoutes;
                // Routers don't use on_success/on_failure, they are cleared above.

            } else {
                // For all other standard nodes (Tool, LLM, Human Input, etc.).
                // These nodes have one primary success path and potentially a failure path.

                // The main success path comes from the default handle (null or undefined).
                const successEdge = outgoingEdges.find(e => e.sourceHandle === null || e.sourceHandle === undefined);
                node.data.on_success = successEdge ? successEdge.target : 'END';

                // Some standard nodes might have a failure path (e.g., http_request).
                // This is a generic way to handle it if you add more complex nodes.
                // For now, it's good future-proofing.
                const failureEdge = outgoingEdges.find(e => e.sourceHandle === 'onFailure');
                if (failureEdge) {
                    node.data.on_failure = failureEdge.target;
                }
            }
        }

        return {
            name: workflowName,
            description: workflowDescription,
            // Return the processed nodes with updated routing data.
            nodes: processedNodes,
            // The visual edges are still useful for re-loading the flow into the UI.
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