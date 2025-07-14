export const createMetaSlice = (set, get) => ({
    workflowId: null,
    workflowName: 'Untitled Workflow',
    workflowDescription: '',

    setWorkflowName: (name) => set({ workflowName: name }),
    setWorkflowDescription: (description) => set({ workflowDescription: description }),

    getFlowAsJson: () => {
        const { nodes, edges, workflowName, workflowDescription } = get();

        return {
            name: workflowName,
            description: workflowDescription,
            nodes: nodes,
            edges: edges,
        };
    },
});