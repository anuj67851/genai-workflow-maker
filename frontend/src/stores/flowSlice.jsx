import {
    addEdge,
    applyNodeChanges,
    applyEdgeChanges,
} from 'reactflow';

export const createFlowSlice = (set, get) => ({
    nodes: [],
    edges: [],

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
            markerEnd: { type: 'arrowclosed', color: '#6b7280' },
            style: { strokeWidth: 2 },
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
        set((state) => ({
            nodes: state.nodes.map(node => {
                if (node.id === nodeId) {
                    const oldRoutes = node.data.routes || {};
                    const newRoutes = Object.keys(oldRoutes).reduce((acc, key) => {
                        if (key === oldName) {
                            acc[newName] = oldRoutes[key];
                        } else {
                            acc[key] = oldRoutes[key];
                        }
                        return acc;
                    }, {});
                    const currentVersion = node.data._version || 0;
                    return { ...node, data: { ...node.data, routes: newRoutes, _version: currentVersion + 1 } };
                }
                return node;
            }),
            edges: state.edges.filter(edge => !(edge.source === nodeId && edge.sourceHandle === oldName)),
        }));

        setTimeout(() => {
            set((state) => ({
                nodes: state.nodes.map(node => {
                    if (node.id === nodeId) {
                        const currentVersion = node.data._version || 0;
                        return { ...node, data: { ...node.data, _version: currentVersion + 1 } };
                    }
                    return node;
                })
            }));
        }, 50);
    },
});