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
import { toast } from 'react-hot-toast';
import { Panel, PanelGroup, PanelResizeHandle } from "react-resizable-panels";

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
import VectorDBIngestionNode from '../components/nodes/VectorDBIngestionNode';
import VectorDBQueryNode from '../components/nodes/VectorDBQueryNode';
import CrossEncoderRerankNode from '../components/nodes/CrossEncoderRerankNode';
import FileStorageNode from '../components/nodes/FileStorageNode';
import HttpRequestNode from '../components/nodes/HttpRequestNode';
import IntelligentRouterNode from '../components/nodes/IntelligentRouterNode';
import DatabaseQueryNode from '../components/nodes/DatabaseQueryNode';
import DatabaseSaveNode from '../components/nodes/DatabaseSaveNode';
import DirectToolCallNode from "../components/nodes/DirectToolCallNode.jsx";
import StartLoopNode from "../components/nodes/StartLoopNode.jsx";
import EndLoopNode from "../components/nodes/EndLoopNode.jsx";

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
    file_storageNode: FileStorageNode,
    vector_db_ingestionNode: VectorDBIngestionNode,
    vector_db_queryNode: VectorDBQueryNode,
    cross_encoder_rerankNode: CrossEncoderRerankNode,
    http_requestNode: HttpRequestNode,
    intelligent_routerNode: IntelligentRouterNode,
    database_queryNode: DatabaseQueryNode,
    database_saveNode: DatabaseSaveNode,
    direct_tool_callNode: DirectToolCallNode,
    start_loopNode: StartLoopNode,
    end_loopNode: EndLoopNode,
};

const initialNodes = [
    { id: 'start', type: 'startNode', position: { x: 250, y: 50 }, data: {} },
    { id: 'end', type: 'endNode', position: { x: 250, y: 500 }, data: {} },
];

// --- Centralized factory for creating new node data ---
const nodeDefaultsFactory = (type) => {
    const baseData = {
        action_type: type,
        label: `New ${type.replace(/_/g, ' ')}`,
        description: `A new step to ${type.replace(/_/g, ' ')}.`,
        prompt_template: '',
        output_key: '' // Default to empty so user must set it
    };

    const specificData = {
        'file_ingestion': { max_files: 1, allowed_file_types: [] },
        'file_storage': { max_files: 1, allowed_file_types: [], storage_path: 'general' },
        'workflow_call': { prompt_template: null, input_mappings: '{\n  "key_for_child": "{input.key_from_parent}"\n}' },
        'vector_db_ingestion': { prompt_template: '{input.documents}', collection_name: 'my_collection', chunk_size: 1000, chunk_overlap: 200, embedding_model: 'text-embedding-3-small' },
        'vector_db_query': { prompt_template: '{query}', collection_name: 'my_collection', top_k: 5 },
        'cross_encoder_rerank': { prompt_template: '{input.query_results}', rerank_top_n: 3 },
        'http_request': { http_method: 'GET', url_template: 'https://api.example.com/data', headers_template: '{\n  "Accept": "application/json"\n}', body_template: '', prompt_template: null },
        'intelligent_router': { prompt_template: 'Based on the user query, which category does it fall into?', routes: { "option_1": "END", "option_2": "END" }, output_key: null },
        'human_input': { output_key: 'user_response' },
        'agentic_tool_use': { output_key: 'tool_output' },
        'database_save': { table_name: 'my_table', primary_key_columns: ['id'], data_template: '{\n  "id": "{input.some_id}",\n  "content": "{input.some_content}"\n}', output_key: 'db_save_result' },
        'database_query': { query_template: "SELECT * FROM my_table WHERE id = '{input.some_id}';", output_key: 'db_results' },
        'direct_tool_call': { target_tool_name: '', data_template: '{\n  "arg_name": "{input.variable}"\n}', output_key: 'direct_tool_output' },
        'start_loop': { input_collection_variable: '{input.my_list}', current_item_output_key: 'currentItem', output_key: 'loop_results' },
        'end_loop': { output_key: null, prompt_template: null }, // End loop has no config
    };

    return { ...baseData, ...(specificData[type] || {}) };
};


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
                setFlow({ id, name, description, nodes, edges }); // Pass ID to store
                setTimeout(() => fitView({ padding: 0.4, duration: 200 }), 100);
            } catch (error) {
                console.error("Failed to load workflow:", error);
                toast.error("Could not load the specified workflow. Starting a new one.");
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

    // --- REFACTOR: Simplified onDrop callback ---
    const onDrop = useCallback((event) => {
        event.preventDefault();
        const type = event.dataTransfer.getData('application/reactflow');
        if (typeof type === 'undefined' || !type) return;

        const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
        const position = project({ x: event.clientX - reactFlowBounds.left, y: event.clientY - reactFlowBounds.top });

        // Use the factory to get the default data for the new node
        const defaultData = nodeDefaultsFactory(type);

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
        <PanelGroup direction="horizontal" className="h-full w-full">
            <Panel defaultSize={15} minSize={15} collapsible={true}>
                <Sidebar />
            </Panel>

            <PanelResizeHandle className="resize-handle">
                <div className="resize-handle-line" />
            </PanelResizeHandle>

            <Panel defaultSize={55} minSize={30}>
                <div className="flex-grow h-full" ref={reactFlowWrapper}>
                    <ReactFlow
                        nodes={nodes.map(n => ({ ...n, key: `${n.id}-${n.data._version || 0}` }))}
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
            </Panel>

            <PanelResizeHandle className="resize-handle">
                <div className="resize-handle-line" />
            </PanelResizeHandle>

            <Panel defaultSize={20} minSize={20} collapsible={true}>
                <InspectorPanel key={selection?.nodes[0]?.id || 'no-selection'} selection={selection} currentWorkflowId={workflowId} />
            </Panel>

        </PanelGroup>
    );
};

const WorkflowBuilder = () => (
    <ReactFlowProvider>
        <BuilderComponent />
    </ReactFlowProvider>
);

export default WorkflowBuilder;