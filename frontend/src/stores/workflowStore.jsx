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
    workflowId: null,
    workflowName: 'Untitled Workflow',
    workflowDescription: '',
    tools: [],

    // --- ACTIONS ---

    onNodesChange: (changes) => {
        const nonDeletableNodeIds = ['start', 'end'];
        const { nodes, edges } = get();

        const filteredChanges = changes.filter(change => {
            if (change.type === 'remove') {
                if (nonDeletableNodeIds.includes(change.id)) {
                    console.warn(`Attempted to delete protected node: ${change.id}. Ignoring.`);
                    return false;
                }
                const nodeToRemove = nodes.find(n => n.id === change.id);
                if (nodeToRemove?.type === 'intelligent_routerNode' && edges.some(e => e.source === change.id)) {
                    alert('Cannot delete a router node with active connections. Please disconnect its routes first.');
                    return false;
                }
            }
            return true;
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
        const newEdge = {
            ...connection,
            id: `edge-${connection.source}-${connection.target}-${connection.sourceHandle || 'default'}`,
            // type: 'smoothstep',
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
                    return { ...node, data: { ...node.data, ...newData } };
                }
                return node;
            }),
        });
    },

    updateRouteName: (nodeId, oldName, newName) => {
        console.log("Updating route name from", oldName, "to", newName, "for node", nodeId);

        // First, update the node data and remove any connected edges
        set((state) => ({
            // 1. Update the node's data to rename the route key.
            nodes: state.nodes.map(node => {
                if (node.id === nodeId) {
                    const oldRoutes = node.data.routes || {};
                    // Rebuild the routes object to preserve the order of other keys.
                    const newRoutes = Object.keys(oldRoutes).reduce((acc, key) => {
                        if (key === oldName) {
                            acc[newName] = oldRoutes[key]; // Rename the key.
                        } else {
                            acc[key] = oldRoutes[key];
                        }
                        return acc;
                    }, {});
                    // Increment the version to force a re-render of the node with new handles
                    const currentVersion = node.data._version || 0;
                    return { 
                        ...node, 
                        data: { 
                            ...node.data, 
                            routes: newRoutes,
                            _version: currentVersion + 1 
                        } 
                    };
                }
                return node;
            }),
            // 2. IMPORTANT: Delete any edge that was connected to the OLD handle.
            edges: state.edges.filter(edge =>
                !(edge.source === nodeId && edge.sourceHandle === oldName)
            ),
        }));

        // Then, after a small delay, increment the version again to ensure ReactFlow recognizes the new handles
        setTimeout(() => {
            set((state) => ({
                nodes: state.nodes.map(node => {
                    if (node.id === nodeId) {
                        const currentVersion = node.data._version || 0;
                        console.log(`Incrementing version for node ${nodeId} from ${currentVersion} to ${currentVersion + 1} after delay`);
                        return {
                            ...node,
                            data: {
                                ...node.data,
                                _version: currentVersion + 1
                            }
                        };
                    }
                    return node;
                })
            }));
        }, 50); // 50ms delay
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

    getFlowAsJson: () => {
        const { nodes, edges, workflowName, workflowDescription } = get();
        const processedNodes = JSON.parse(JSON.stringify(nodes));
        const edgesBySource = edges.reduce((acc, edge) => {
            if (!acc[edge.source]) acc[edge.source] = [];
            acc[edge.source].push(edge);
            return acc;
        }, {});

        for (const node of processedNodes) {
            if (node.type === 'startNode' || node.type === 'endNode') continue;

            const outgoingEdges = edgesBySource[node.id] || [];
            node.data.on_success = null;
            node.data.on_failure = null;

            // Remove _version parameter as it's only used in frontend
            if (node.data._version !== undefined) {
                delete node.data._version;
            }

            if (node.data.action_type === 'condition_check') {
                const successEdge = outgoingEdges.find(e => e.sourceHandle === 'onSuccess');
                const failureEdge = outgoingEdges.find(e => e.sourceHandle === 'onFailure');
                node.data.on_success = successEdge ? successEdge.target : 'END';
                node.data.on_failure = failureEdge ? failureEdge.target : 'END';

            } else if (node.data.action_type === 'intelligent_router') {
                // This logic is now correct: it preserves unconnected routes.
                const updatedRoutes = { ...(node.data.routes || {}) };
                for (const edge of outgoingEdges) {
                    if (edge.sourceHandle && updatedRoutes.hasOwnProperty(edge.sourceHandle)) {
                        updatedRoutes[edge.sourceHandle] = edge.target;
                    }
                }
                node.data.routes = updatedRoutes;

            } else {
                const successEdge = outgoingEdges.find(e => !e.sourceHandle);
                node.data.on_success = successEdge ? successEdge.target : 'END';
                const failureEdge = outgoingEdges.find(e => e.sourceHandle === 'onFailure');
                if (failureEdge) node.data.on_failure = failureEdge.target;
            }
        }

        return {
            name: workflowName,
            description: workflowDescription,
            nodes: processedNodes,
            edges: edges,
        };
    },

    fetchTools: async () => {
        if (get().tools.length > 0) return;
        try {
            const response = await axios.get('/api/tools');
            if (response.data) set({ tools: response.data });
        } catch (error) {
            console.error("Error fetching tools:", error);
            set({ tools: [] });
        }
    },
    setWorkflowName: (name) => set({ workflowName: name }),
    setWorkflowDescription: (description) => set({ workflowDescription: description }),
}));

export default useWorkflowStore;
