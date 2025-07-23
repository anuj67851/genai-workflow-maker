import React, { useEffect, useState } from 'react';
import useWorkflowStore from '../../stores/workflowStore';
import { TrashIcon } from '@heroicons/react/24/solid';
import axios from 'axios';

// Import all the new inspector components
import { ToolNodeInspector } from '../nodes/ToolNode';
import { WorkflowNodeInspector } from '../nodes/WorkflowNode';
import { IngestionNodeInspector } from '../nodes/IngestionNode';
import { FileStorageNodeInspector } from '../nodes/FileStorageNode';
import { VectorDBIngestionNodeInspector } from '../nodes/VectorDBIngestionNode';
import { VectorDBQueryNodeInspector } from '../nodes/VectorDBQueryNode';
import { CrossEncoderRerankNodeInspector } from '../nodes/CrossEncoderRerankNode';
import { HttpRequestNodeInspector } from '../nodes/HttpRequestNode';
import { IntelligentRouterNodeInspector } from '../nodes/IntelligentRouterNode';
import { DatabaseQueryNodeInspector } from '../nodes/DatabaseQueryNode';
import { DatabaseSaveNodeInspector } from '../nodes/DatabaseSaveNode';
import { DirectToolCallNodeInspector } from "../nodes/DirectToolCallNode";
import { StartLoopNodeInspector } from '../nodes/StartLoopNode';
import { EndLoopNodeInspector } from '../nodes/EndLoopNode';

// Map node types to their specific inspector components
const nodeInspectorMap = {
    agentic_tool_use: ToolNodeInspector,
    workflow_call: WorkflowNodeInspector,
    file_ingestion: IngestionNodeInspector,
    file_storage: FileStorageNodeInspector,
    vector_db_ingestion: VectorDBIngestionNodeInspector,
    vector_db_query: VectorDBQueryNodeInspector,
    cross_encoder_rerank: CrossEncoderRerankNodeInspector,
    http_request: HttpRequestNodeInspector,
    intelligent_router: IntelligentRouterNodeInspector,
    database_query: DatabaseQueryNodeInspector,
    database_save: DatabaseSaveNodeInspector,
    direct_tool_call: DirectToolCallNodeInspector,
    start_loop: StartLoopNodeInspector,
    end_loop: EndLoopNodeInspector,
};

// --- Helper constants for conditional rendering ---
const NODES_WITH_PROMPT_TEMPLATE = [
    'agentic_tool_use', 'condition_check', 'human_input', 'llm_response',
    'file_ingestion', 'file_storage', 'vector_db_query', 'intelligent_router',
    'display_message',
];
const NODES_WITH_DATA_SOURCE = ['vector_db_ingestion', 'cross_encoder_rerank'];
const NODES_WITH_OUTPUT_KEY = [
    'human_input', 'agentic_tool_use', 'llm_response', 'workflow_call', 'file_ingestion',
    'file_storage', 'http_request', 'vector_db_ingestion', 'vector_db_query', 'cross_encoder_rerank',
    'database_query', 'database_save', 'direct_tool_call', 'start_loop', 'display_message',
];

const InspectorPanel = ({ selection, currentWorkflowId }) => {
    // --- Subscribe directly to the `nodes` state ---
    const { nodes, onNodesChange, onEdgesChange, updateNodeData, tools, fetchTools } = useWorkflowStore(state => ({
        nodes: state.nodes,
        onNodesChange: state.onNodesChange,
        onEdgesChange: state.onEdgesChange,
        updateNodeData: state.updateNodeData,
        tools: state.tools,
        fetchTools: state.fetchTools,
    }));

    const [availableWorkflows, setAvailableWorkflows] = useState([]);

    // --- Derive the selected node's data from the live store state ---
    const selectedNodeId = selection?.nodes[0]?.id;
    const selectedNode = nodes.find(n => n.id === selectedNodeId);

    // Effect for fetching external data.
    useEffect(() => {
        if (tools.length === 0) fetchTools();
        const fetchWorkflows = async () => {
            try {
                const response = await axios.get('/api/workflows');
                setAvailableWorkflows(response.data || []);
            } catch (error) {
                console.error("Failed to fetch workflows for inspector:", error);
            }
        }
        fetchWorkflows();
    }, [fetchTools, tools.length]);

    // Universal change handler for all controlled inputs.
    const handleChange = (event) => {
        if (!selectedNode) return;
        const { name, value, type, checked } = event.target;
        let finalValue;

        if (name === 'tool_names_checkbox') {
            const currentTools = selectedNode.data.tool_names || [];
            finalValue = checked ? [...currentTools, value] : currentTools.filter(tool => tool !== value);
            updateNodeData(selectedNode.id, { ...selectedNode.data, tool_names: finalValue });
            return;
        }

        finalValue = type === 'checkbox' ? checked : type === 'number' ? (value === '' ? '' : parseInt(value, 10)) : value;
        updateNodeData(selectedNode.id, { ...selectedNode.data, [name]: finalValue });
    };

    // Handler to format/finalize data when an input loses focus.
    const handleBlur = (event) => {
        if (!selectedNode) return;
        const { name, value, type } = event.target;

        if (name === 'allowed_file_types' || name === 'primary_key_columns') {
            const finalValue = value.split(',').map(item => item.trim()).filter(Boolean);
            updateNodeData(selectedNode.id, { ...selectedNode.data, [name]: finalValue });
        } else if (type === 'number' && value === '') {
            const defaultValues = { max_files: 1, rerank_top_n: 3, top_k: 5, chunk_size: 1000, chunk_overlap: 200 };
            updateNodeData(selectedNode.id, { ...selectedNode.data, [name]: defaultValues[name] || 0 });
        }
    };

    // Handler to delete the selected node.
    const handleDelete = () => {
        if (!selection || (selection.nodes.length === 0 && selection.edges.length === 0)) return;
        if (window.confirm(`Are you sure you want to delete the selected element(s)?`)) {
            if (selection.nodes.length > 0) onNodesChange(selection.nodes.map(n => ({ id: n.id, type: 'remove' })));
            if (selection.edges.length > 0) onEdgesChange(selection.edges.map(e => ({ id: e.id, type: 'remove' })));
        }
    };

    if (!selectedNode) {
        return (
            <aside className="h-full w-full bg-gray-50 p-6 border-l border-gray-200 inspector-panel">
                <h3 className="text-xl font-bold text-gray-800">Properties</h3>
                <p className="mt-2 text-sm text-gray-500">Select a node on the canvas to view and edit its properties.</p>
            </aside>
        );
    }

    const nodeData = selectedNode.data || {};
    const nodeActionType = nodeData.action_type;
    const nodeDisplayName = selectedNode.type ? selectedNode.type.replace(/Node$/, '').replace(/_/g, ' ') : 'Node';

    const isDeletable = selectedNode && !['start', 'end'].includes(selectedNode.id);
    const NodeSpecificInspector = nodeInspectorMap[nodeActionType];

    // --- RENDER FUNCTIONS FOR COMMON FIELDS ---
    const renderBaseFields = () => (
        <>
            <div>
                <label htmlFor="label">Node Label (Optional)</label>
                <input id="label" name="label" value={nodeData.label || ''} onChange={handleChange} placeholder="e.g., Check User Warranty"/>
            </div>
            <div>
                <label htmlFor="description">Description</label>
                <input id="description" name="description" value={nodeData.description || ''} onChange={handleChange} placeholder="A brief summary of this step"/>
            </div>
        </>
    );

    const renderPromptTemplateField = () => (
        <div>
            <label htmlFor="prompt_template">Prompt / Instruction</label>
            <textarea id="prompt_template" name="prompt_template" rows={5} value={nodeData.prompt_template || ''} onChange={handleChange} placeholder="The detailed instruction for the LLM or user."/>
            <p className="text-xs text-gray-400 mt-1">You can use variables like {`{query}`} or {`{input.variable_name}`}.</p>
        </div>
    );

    const renderDataSourceField = () => (
        <div>
            <label htmlFor="prompt_template">Input Variable / Data Source</label>
            <input id="prompt_template" name="prompt_template" value={nodeData.prompt_template || ''} onChange={handleChange} placeholder="{input.variable_name}" />
            <p className="text-xs text-gray-400 mt-1">Specify the variable holding the data for this step (e.g., from a file upload or previous step).</p>
        </div>
    );

    const renderOutputKeyField = () => (
        <div>
            <label htmlFor="output_key">Output Variable Name</label>
            <input id="output_key" name="output_key" value={nodeData.output_key || ''} onChange={handleChange} placeholder="e.g., user_email, ticket_id" />
            <p className="text-xs text-gray-400 mt-1">Saves the step's result to this variable for later use.</p>
        </div>
    );

    // --- Main component return ---
    return (
        <aside className="h-full w-full bg-gray-50 p-6 border-l border-gray-200 inspector-panel flex flex-col">
            <div className="flex-grow overflow-y-auto pr-2">
                <div>
                    <h3 className="text-xl font-bold text-gray-800">
                        {nodeData.label || `Edit: ${nodeDisplayName}`}
                    </h3>
                    <h4 className="text-sm font-mono text-indigo-600 bg-indigo-50 px-2 py-1 rounded-md mt-2 inline-block">
                        Type: {nodeDisplayName}
                    </h4>
                </div>

                <div className="space-y-4 mt-4">
                    {/* Common fields rendered for all nodes */}
                    {renderBaseFields()}
                    {NODES_WITH_PROMPT_TEMPLATE.includes(nodeActionType) && renderPromptTemplateField()}
                    {NODES_WITH_DATA_SOURCE.includes(nodeActionType) && renderDataSourceField()}

                    {/* Dynamically render the node-specific inspector */}
                    {NodeSpecificInspector && (
                        <NodeSpecificInspector
                            nodeId={selectedNode.id}
                            nodeData={nodeData}
                            handleChange={handleChange}
                            handleBlur={handleBlur}
                            tools={tools}
                            availableWorkflows={availableWorkflows}
                            currentWorkflowId={currentWorkflowId}
                        />
                    )}

                    {/* Common output key field */}
                    {NODES_WITH_OUTPUT_KEY.includes(nodeActionType) && renderOutputKeyField()}
                </div>
            </div>

            {/* Common delete button */}
            <div className="mt-6 pt-6 border-t border-gray-200">
                <button onClick={handleDelete} disabled={!isDeletable} className="w-full flex items-center justify-center gap-2 bg-red-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-red-700 disabled:bg-red-300 disabled:cursor-not-allowed transition-colors" >
                    <TrashIcon className="h-5 w-5"/>
                    Delete Node
                </button>
                {!isDeletable && ( <p className="text-xs text-center text-gray-500 mt-2"> The START and END nodes cannot be deleted. </p> )}
            </div>
        </aside>
    );
};

export default InspectorPanel;