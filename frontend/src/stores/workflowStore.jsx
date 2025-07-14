import { create } from 'zustand';
import { createFlowSlice } from './flowSlice';
import { createMetaSlice } from './metaSlice';
import { createToolSlice } from './toolSlice';

const useWorkflowStore = create((set, get) => ({
    // Combine slices
    ...createFlowSlice(set, get),
    ...createMetaSlice(set, get),
    ...createToolSlice(set, get),

    // Actions that span across multiple slices
    setFlow: (flow) => {
        set({
            workflowId: flow.id || null,
            nodes: flow.nodes || [],
            edges: flow.edges || [],
            workflowName: flow.name || 'Untitled Workflow',
            workflowDescription: flow.description || ''
        });
    },
}));

export default useWorkflowStore;