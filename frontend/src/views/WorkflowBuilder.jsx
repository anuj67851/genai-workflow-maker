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

// Import UI components
import Sidebar from '../components/ui/Sidebar';
import InspectorPanel from '../components/ui/InspectorPanel';

// Import custom node components
import ToolNode from '../components/nodes/ToolNode';
import ConditionNode from '../components/nodes/ConditionNode';
import HumanInputNode from '../components/nodes/HumanInputNode';
import LLMResponseNode from '../components/nodes/LLMResponseNode';
import StartNode from '../components/nodes/StartNode';
import EndNode from '../components/nodes/EndNode';

// Import the state management store
import useWorkflowStore from '../stores/workflowStore';

// Define the custom node types that React Flow will be able to render
const nodeTypes = {
    agentic_tool_useNode: ToolNode,
    condition_checkNode: ConditionNode,
    human_inputNode: HumanInputNode,
    llm_responseNode: LLMResponseNode,
    startNode: StartNode,
    endNode: EndNode,
};

const initialNodes = [
    { id: 'start', type: 'startNode', position: { x: 250, y: 50 }, data: {} },
    { id: 'end', type: 'endNode', position: { x: 250, y: 500 }, data: {} },
];

// This is the core builder logic component.
const BuilderComponent = () => {
    const { workflowId } = useParams(); // Get ID from URL if it exists
    const navigate = useNavigate();
    const reactFlowWrapper = useRef(null);
    const {
        nodes, edges, onNodesChange, onEdgesChange, onConnect, addNode, setFlow
    } = useWorkflowStore();
    const [selectedNode, setSelectedNode] = useState(null);
    const { project, fitView } = useReactFlow();

    // This effect handles loading existing workflows or starting a new one.
    useEffect(() => {
        const loadWorkflow = async (id) => {
            try {
                const response = await axios.get(`/api/workflows/${id}`);
                // The backend needs to be able to return a workflow in this graph format.
                // Assuming your get_workflow_graph endpoint does this.
                const { name, description, nodes, edges } = response.data;
                setFlow({ name, description, nodes, edges });

                // Use a timeout to ensure nodes are rendered before fitting the view
                setTimeout(() => fitView({ padding: 0.2 }), 100);
            } catch (error) {
                console.error("Failed to load workflow:", error);
                alert("Could not load the specified workflow. Starting a new one.");
                navigate('/'); // Redirect to new builder on error
            }
        };

        if (workflowId) {
            loadWorkflow(workflowId);
        } else {
            // This is for a new workflow
            setFlow({ nodes: initialNodes, edges: [], name: 'Untitled Workflow', description: '' });
        }
    }, [workflowId, setFlow, navigate, fitView]);

    const onDragOver = useCallback((event) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }, []);

    const onDrop = useCallback(
        (event) => {
            event.preventDefault();
            const type = event.dataTransfer.getData('application/reactflow');
            if (typeof type === 'undefined' || !type) {
                return;
            }
            const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
            const position = project({
                x: event.clientX - reactFlowBounds.left,
                y: event.clientY - reactFlowBounds.top,
            });
            const newNode = {
                id: `${type.replace(/_/g, '-')}-${+new Date()}`,
                type: `${type}Node`,
                position,
                data: {
                    action_type: type,
                    description: `A new step to ${type.replace(/_/g, ' ')}.`,
                    prompt_template: '',
                },
            };
            addNode(newNode);
        },
        [project, addNode]
    );

    const onNodeClick = useCallback((event, node) => {
        setSelectedNode(node);
    }, []);

    const onPaneClick = useCallback(() => {
        setSelectedNode(null);
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
                    onNodeClick={onNodeClick}
                    onPaneClick={onPaneClick}
                    nodeTypes={nodeTypes}
                    fitView
                    fitViewOptions={{ padding: 0.2 }}
                >
                    <Controls />
                    <MiniMap />
                    <Background variant="dots" gap={12} size={1} />
                </ReactFlow>
            </div>
            <InspectorPanel selectedNode={selectedNode} />
        </div>
    );
};

// The provider wrapper is essential for the useReactFlow hook to work.
const WorkflowBuilder = () => (
    <ReactFlowProvider>
        <BuilderComponent />
    </ReactFlowProvider>
);

export default WorkflowBuilder;