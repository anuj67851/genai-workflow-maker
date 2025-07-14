export const createMetaSlice = (set, get) => ({
    workflowId: null,
    workflowName: 'Untitled Workflow',
    workflowDescription: '',

    setWorkflowName: (name) => set({ workflowName: name }),
    setWorkflowDescription: (description) => set({ workflowDescription: description }),

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
            if (node.data._version !== undefined) {
                delete node.data._version;
            }

            if (node.data.action_type === 'condition_check') {
                const successEdge = outgoingEdges.find(e => e.sourceHandle === 'onSuccess');
                const failureEdge = outgoingEdges.find(e => e.sourceHandle === 'onFailure');
                node.data.on_success = successEdge ? successEdge.target : 'END';
                node.data.on_failure = failureEdge ? failureEdge.target : 'END';
            } else if (node.data.action_type === 'intelligent_router') {
                const updatedRoutes = { ...(node.data.routes || {}) };
                for (const edge of outgoingEdges) {
                    if (edge.sourceHandle && updatedRoutes.hasOwnProperty(edge.sourceHandle)) {
                        updatedRoutes[edge.sourceHandle] = edge.target;
                    }
                }
                node.data.routes = updatedRoutes;
            } else {
                const successEdge = outgoingEdges.find(e => !e.sourceHandle || e.sourceHandle === 'default');
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
});