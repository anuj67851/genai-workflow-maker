import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactFlow, {
    ReactFlowProvider,
    useReactFlow,
    Controls,
    Background,
    MiniMap,
} from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';

import Sidebar from '../components/ui/Sidebar';
import InspectorPanel from '../components/ui/InspectorPanel';

// Import all node components
import ToolNode from '../components/nodes/ToolNode';
import ConditionNode from '../components/nodes/ConditionNode';
import HumanInputNode from '../components/nodes/HumanInputNode';
import LLMResponseNode from '../components/nodes/LLMResponseNode';
import StartNode from '../components/nodes/StartNode';
import EndNode from '../components/nodes/EndNode';
import WorkflowNode from '../components/nodes/WorkflowNode';
import IngestionNode from '../components/nodes/IngestionNode';

import useWorkflowStore from '../stores/workflowStore';

// Map action_type to the corresponding component
const nodeTypes = {
    agentic_tool_useNode: ToolNode,
    condition_checkNode: ConditionNode,
    human_inputNode: HumanInputNode,
    llm_responseNode: LLMResponseNode,
    startNode: StartNode,
    endNode: EndNode,
    workflow_callNode: WorkflowNode,
    file_ingestionNode: IngestionNode,
};

const initialNodes = [
    { id: 'start', type: 'startNode', position: { x: 250, y: 50 }, data: {} },
    { id: 'end', type: 'endNode', position: { x: 250, y: 500 }, data: {} },
];

const BuilderComponent = () => {
    const { workflowId } = useParams();
    const navigate = useNavigate();
    const reactFlowWrapper = useRef(null);
    const {
        nodes, edges, onNodesChange, onEdgesChange, onConnect, addNode, setFlow,
    } = useWorkflowStore();
    const { project, fitView } = useReactFlow();
    const [selection, setSelection] = useState({ nodes: [], edges: [] });

    useEffect(() => {
        const loadWorkflow = async (id) => {
            try {
                const response = await axios.get(`/api/workflows/${id}`);
                const { name, description, nodes, edges } = response.data;
                setFlow({ name, description, nodes, edges });
                setTimeout(() => fitView({ padding: 0.4, duration: 200 }), 100);
            } catch (error) {
                console.error("Failed to load workflow:", error);
                alert("Could not load the specified workflow. Starting a new one.");
                setFlow({ nodes: initialNodes, edges: [], name: 'Untitled Workflow', description: '' });
                navigate('/');
            }
        };
        if (workflowId) {
            loadWorkflow(workflowId);
        } else {
            setFlow({ nodes: initialNodes, edges: [], name: 'Untitled Workflow', description: '' });
        }
    }, [workflowId, setFlow, navigate, fitView]);

    const onDragOver = useCallback((event) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }, []);

    const onDrop = useCallback((event) => {
        event.preventDefault();
        const type = event.dataTransfer.getData('application/reactflow');
        if (typeof type === 'undefined' || !type) return;
        const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
        const position = project({ x: event.clientX - reactFlowBounds.left, y: event.clientY - reactFlowBounds.top });

        // Default data for new nodes
        const defaultData = {
            action_type: type,
            label: `New ${type.replace(/_/g, ' ')}`,
            description: `A new step to ${type.replace(/_/g, ' ')}.`,
            prompt_template: '',
            output_key: `output_${Math.floor(Math.random() * 1000)}` // Pre-fill with a random key
        };

        // Custom initial data for specific node types
        if(type === 'file_ingestion') {
            defaultData.max_files = 1;
            defaultData.allowed_file_types = [];
        }
        if(type === 'workflow_call') {
            defaultData.prompt_template = null; // Not needed for workflow_call
        }


        const newNode = {
            id: `${type.replace(/_/g, '-')}-${+new Date()}`,
            type: `${type}Node`,
            position,
            data: defaultData,
        };
        addNode(newNode);
    }, [project, addNode]);

    const onPaneClick = useCallback(() => {
        setSelection({ nodes: [], edges: [] });
    }, []);

    const onSelectionChange = useCallback(({ nodes, edges }) => {
        setSelection({ nodes, edges });
    }, []);

    return (
        <div className="flex h-full w-full">
            <Sidebar />
            <div className="flex-grow h-full" ref={reactFlowWrapper}>
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    onDrop={onDrop}
                    onDragOver={onDragOver}
                    onPaneClick={onPaneClick}
                    onSelectionChange={onSelectionChange}
                    deleteKeyCode={['Backspace', 'Delete']}
                    nodeTypes={nodeTypes}
                    fitView
                    fitViewOptions={{ padding: 0.2 }}
                >
                    <Controls />
                    <MiniMap />
                    <Background variant="dots" gap={12} size={1} />
                </ReactFlow>
            </div>
            <InspectorPanel selection={selection} />
        </div>
    );
};

const WorkflowBuilder = () => (
    <ReactFlowProvider>
        <BuilderComponent />
    </ReactFlowProvider>
);

export default WorkflowBuilder;