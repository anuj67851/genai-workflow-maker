import React, { useEffect, useState } from 'react';
import useWorkflowStore from '../../stores/workflowStore';
import { TrashIcon, InformationCircleIcon } from '@heroicons/react/24/solid';
import axios from 'axios';

const NODES_WITH_PROMPT_TEMPLATE = [
    'agentic_tool_use',
    'condition_check',
    'human_input',
    'llm_response',
    'file_ingestion',
    'file_storage',
    'vector_db_query',
    'intelligent_router',
];

const NODES_WITH_DATA_SOURCE = [
    'vector_db_ingestion',
    'cross_encoder_rerank',
];

const NODES_WITH_OUTPUT_KEY = [
    'human_input',
    'agentic_tool_use',
    'llm_response',
    'workflow_call',
    'file_ingestion',
    'file_storage',
    'http_request',
    'vector_db_ingestion',
    'vector_db_query',
    'cross_encoder_rerank',
];

const InspectorPanel = ({ selection, currentWorkflowId }) => {
    const { onNodesChange, onEdgesChange, updateNodeData, tools, fetchTools } = useWorkflowStore(state => ({
        onNodesChange: state.onNodesChange,
        onEdgesChange: state.onEdgesChange,
        updateNodeData: state.updateNodeData,
        tools: state.tools,
        fetchTools: state.fetchTools,
    }));

    const [formData, setFormData] = useState({});
    const [availableWorkflows, setAvailableWorkflows] = useState([]);
    const selectedNode = selection?.nodes[0];
    const nodeType = selectedNode?.type.replace('Node', '');

    // Fetch tools and workflows on component mount
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

    // Update form data when a new node is selected
    useEffect(() => {
        if (selectedNode) {
            setFormData({
                // Common fields
                label: '',
                description: '',
                prompt_template: '',
                output_key: '',
                // Tool fields
                tool_selection: 'auto',
                tool_names: [],
                // Workflow Call fields
                target_workflow_id: null,
                // File Ingestion fields
                allowed_file_types: [],
                max_files: 1,
                storage_path: '',
                // RAG Fields
                collection_name: '',
                embedding_model: '',
                chunk_size: 1000,
                chunk_overlap: 200,
                top_k: 5,
                rerank_top_n: 3,
                // HTTP Request Fields
                http_method: 'GET',
                url_template: '',
                headers_template: '',
                body_template: '',
                // For Intelligent Router
                routes: {},
                // Spread existing data over defaults
                ...selectedNode.data,
            });
        }
    }, [selectedNode]);

    const handleInputChange = (event) => {
        const { name, value, type } = event.target;
        const finalValue = type === 'number' ? parseInt(value, 10) || 0 : value;
        setFormData(prev => ({ ...prev, [name]: finalValue }));
    };

    const handleArrayInputChange = (event) => {
        const { name, value } = event.target;
        const arrayValue = value.split(',').map(item => item.trim()).filter(Boolean);
        setFormData(prev => ({...prev, [name]: arrayValue}));
    }

    const handleToolSelectionChange = (event) => {
        const { name, checked } = event.target;
        setFormData(prev => {
            const currentTools = prev.tool_names || [];
            if (checked) {
                return { ...prev, tool_names: [...currentTools, name] };
            } else {
                return { ...prev, tool_names: currentTools.filter(tool => tool !== name) };
            }
        });
    };

    const handleBlur = () => {
        if (selectedNode) {
            updateNodeData(selectedNode.id, formData);
        }
    };

    const handleDelete = () => {
        if (!selection || (selection.nodes.length === 0 && selection.edges.length === 0)) return;
        if (window.confirm(`Are you sure you want to delete the selected element(s)?`)) {
            if (selection.nodes.length > 0) onNodesChange(selection.nodes.map(n => ({ id: n.id, type: 'remove' })));
            if (selection.edges.length > 0) onEdgesChange(selection.edges.map(e => ({ id: e.id, type: 'remove' })));
        }
    };

    const isDeletable = selectedNode && !['start', 'end'].includes(selectedNode.id);

    if (!selectedNode) {
        return (
            <aside className="w-96 bg-gray-50 p-6 border-l border-gray-200 inspector-panel">
                <h3 className="text-xl font-bold text-gray-800">Properties</h3>
                <p className="mt-2 text-sm text-gray-500">Select a node on the canvas to view and edit its properties.</p>
            </aside>
        );
    }

    const renderBaseFields = () => (
        <>
            <div>
                <label htmlFor="label">Node Label (Optional)</label>
                <input id="label" name="label" value={formData.label || ''} onChange={handleInputChange} onBlur={handleBlur} placeholder="e.g., Check User Warranty"/>
                <p className="text-xs text-gray-400 mt-1">A custom title for this node in the graph.</p>
            </div>
            <div>
                <label htmlFor="description">Description</label>
                <input id="description" name="description" value={formData.description || ''} onChange={handleInputChange} onBlur={handleBlur} placeholder="A brief summary of this step"/>
            </div>
        </>
    );

    const renderPromptTemplateField = () => (
        <div>
            <label htmlFor="prompt_template">Prompt / Instruction</label>
            <textarea id="prompt_template" name="prompt_template" rows={5} value={formData.prompt_template || ''} onChange={handleInputChange} onBlur={handleBlur} placeholder="The detailed instruction for the LLM or user."/>
            <p className="text-xs text-gray-400 mt-1">You can use variables like {`{query}`} or {`{input.variable_name}`}.</p>
        </div>
    );

    const renderDataSourceField = () => (
        <div>
            <label htmlFor="prompt_template">Input Variable / Data Source</label>
            <input id="prompt_template" name="prompt_template" value={formData.prompt_template || ''} onChange={handleInputChange} onBlur={handleBlur} placeholder="{input.variable_name}" />
            <p className="text-xs text-gray-400 mt-1">Specify the variable holding the data for this step (e.g., from a file upload or previous step).</p>
        </div>
    );

    const renderOutputKeyField = () => (
        <div>
            <label htmlFor="output_key">Output Variable Name</label>
            <input id="output_key" name="output_key" value={formData.output_key || ''} onChange={handleInputChange} onBlur={handleBlur} placeholder="e.g., user_email, ticket_id" />
            <p className="text-xs text-gray-400 mt-1">Saves the step's result to this variable for later use.</p>
        </div>
    );

    const renderToolSelection = () => {
        const selectedToolSchemas = tools.filter(tool => formData.tool_names?.includes(tool.function.name));
        return (
            <div>
                <label>Tool Usage</label>
                <div className="space-y-3 rounded-md border border-gray-200 p-3 bg-white">
                    <div className="grid grid-cols-[auto_1fr] items-center gap-x-3">
                        <input type="radio" id="tool_auto" name="tool_selection" value="auto" checked={formData.tool_selection === 'auto'} onChange={handleInputChange} onBlur={handleBlur} className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300" />
                        <label htmlFor="tool_auto" className="text-sm font-medium text-gray-700">Let agent decide from all available tools</label>
                    </div>
                    <div className="grid grid-cols-[auto_1fr] items-center gap-x-3">
                        <input type="radio" id="tool_manual" name="tool_selection" value="manual" checked={formData.tool_selection === 'manual'} onChange={handleInputChange} onBlur={handleBlur} className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300" />
                        <label htmlFor="tool_manual" className="text-sm font-medium text-gray-700">Select specific tools for the agent</label>
                    </div>
                    <div className="grid grid-cols-[auto_1fr] items-center gap-x-3">
                        <input type="radio" id="tool_none" name="tool_selection" value="none" checked={formData.tool_selection === 'none'} onChange={handleInputChange} onBlur={handleBlur} className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300" />
                        <label htmlFor="tool_none" className="text-sm font-medium text-gray-700">Do not use any tools (direct LLM response)</label>
                    </div>
                </div>

                {formData.tool_selection === 'manual' && (
                    <div className="mt-2 p-3 border border-gray-200 rounded-md bg-gray-50 max-h-48 overflow-y-auto space-y-2">
                        <p className="text-xs text-gray-500 mb-2">Select one or more tools for the agent to use:</p>
                        {tools.map(tool => (
                            <div key={tool.function.name} className="grid grid-cols-[auto_1fr] items-center gap-x-3">
                                <input type="checkbox" id={`tool-chk-${tool.function.name}`} name={tool.function.name} checked={formData.tool_names?.includes(tool.function.name) || false} onChange={handleToolSelectionChange} onBlur={handleBlur} className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
                                <label htmlFor={`tool-chk-${tool.function.name}`} className="text-sm text-gray-900 font-mono">{tool.function.name}</label>
                            </div>
                        ))}
                    </div>
                )}

                {formData.tool_selection === 'manual' && selectedToolSchemas.length > 0 && (
                    <div className="mt-3 p-3 border border-blue-200 rounded-lg bg-blue-50 space-y-2">
                        <div className="flex items-center gap-2 text-blue-800"><InformationCircleIcon className="h-5 w-5"/><h4 className="text-sm font-bold">Tool Return Information</h4></div>
                        {selectedToolSchemas.map(tool => (
                            <div key={`info-${tool.function.name}`} className="text-xs">
                                <p className="font-bold font-mono text-blue-900">{tool.function.name}:</p>
                                <p className="text-blue-700 pl-2">{tool.function.returns?.description || "No return description provided."}</p>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    const renderWorkflowCallFields = () => (
        <div>
            <label htmlFor="target_workflow_id">Workflow to Execute</label>
            <select id="target_workflow_id" name="target_workflow_id" value={formData.target_workflow_id || ''} onChange={handleInputChange} onBlur={handleBlur} >
                <option value="">-- Select a Workflow --</option>
                {availableWorkflows.filter(wf => wf.id.toString() !== (currentWorkflowId || '').toString()).map(wf => (
                    <option key={wf.id} value={wf.id}>{wf.name}</option>
                ))}
            </select>
            <p className="text-xs text-gray-400 mt-1">Runs another workflow as a sub-step. The current workflow is excluded to prevent loops.</p>
        </div>
    );

    const renderFileIngestionFields = () => (
        <div className="space-y-4">
            <div>
                <label htmlFor="max_files">Maximum Number of Files</label>
                <input id="max_files" name="max_files" type="number" min="1" value={formData.max_files || 1} onChange={handleInputChange} onBlur={handleBlur} />
            </div>
            <div>
                <label htmlFor="allowed_file_types">Allowed File Types (comma-separated)</label>
                <input id="allowed_file_types" name="allowed_file_types" value={(formData.allowed_file_types || []).join(', ')} onChange={handleArrayInputChange} onBlur={handleBlur} placeholder=".pdf, .txt, .csv" />
                <p className="text-xs text-gray-400 mt-1">Leave blank to allow any file type.</p>
            </div>
        </div>
    );

    const renderFileStorageFields = () => (
        <div className="space-y-4">
            <div>
                <label htmlFor="storage_path">Storage Subdirectory (Optional)</label>
                <input id="storage_path" name="storage_path" value={formData.storage_path || ''} onChange={handleInputChange} onBlur={handleBlur} placeholder="e.g., ticket_attachments" />
                <p className="text-xs text-gray-400 mt-1">A subdirectory within the main attachments folder to save this file to.</p>
            </div>
            <div>
                <label htmlFor="max_files">Maximum Number of Files</label>
                <input id="max_files" name="max_files" type="number" min="1" value={formData.max_files || 1} onChange={handleInputChange} onBlur={handleBlur} />
            </div>
            <div>
                <label htmlFor="allowed_file_types">Allowed File Types (comma-separated)</label>
                <input id="allowed_file_types" name="allowed_file_types" value={(formData.allowed_file_types || []).join(', ')} onChange={handleArrayInputChange} onBlur={handleBlur} placeholder=".png, .jpg, .pdf" />
                <p className="text-xs text-gray-400 mt-1">Leave blank to allow any file type.</p>
            </div>
        </div>
    );

    const renderVectorDbIngestionFields = () => (
        <div className="space-y-4 p-3 bg-teal-50 border border-teal-200 rounded-lg">
            <h4 className="font-bold text-teal-800">Vector Ingestion Settings</h4>
            <div>
                <label htmlFor="collection_name">Collection Name</label>
                <input id="collection_name" name="collection_name" value={formData.collection_name || ''} onChange={handleInputChange} onBlur={handleBlur} placeholder="e.g., project_docs_v1"/>
            </div>
            <div>
                <label htmlFor="embedding_model">Embedding Model</label>
                <input id="embedding_model" name="embedding_model" value={formData.embedding_model || ''} onChange={handleInputChange} onBlur={handleBlur} placeholder="text-embedding-3-small"/>
            </div>
            <div>
                <label htmlFor="chunk_size">Chunk Size</label>
                <input id="chunk_size" name="chunk_size" type="number" min="1" value={formData.chunk_size || 1000} onChange={handleInputChange} onBlur={handleBlur} />
            </div>
            <div>
                <label htmlFor="chunk_overlap">Chunk Overlap</label>
                <input id="chunk_overlap" name="chunk_overlap" type="number" min="0" value={formData.chunk_overlap || 200} onChange={handleInputChange} onBlur={handleBlur} />
            </div>
        </div>
    );

    const renderVectorDbQueryFields = () => (
        <div className="space-y-4 p-3 bg-teal-50 border border-teal-200 rounded-lg">
            <h4 className="font-bold text-teal-800">Vector Query Settings</h4>
            <div>
                <label htmlFor="collection_name">Collection Name</label>
                <input id="collection_name" name="collection_name" value={formData.collection_name || ''} onChange={handleInputChange} onBlur={handleBlur} placeholder="e.g., project_docs_v1"/>
            </div>
            <div>
                <label htmlFor="top_k">Top-K</label>
                <input id="top_k" name="top_k" type="number" min="1" value={formData.top_k || 5} onChange={handleInputChange} onBlur={handleBlur} />
                <p className="text-xs text-gray-400 mt-1">The number of initial documents to retrieve.</p>
            </div>
        </div>
    );

    const renderCrossEncoderRerankFields = () => (
        <div className="space-y-4 p-3 bg-teal-50 border border-teal-200 rounded-lg">
            <h4 className="font-bold text-teal-800">Re-Ranker Settings</h4>
            <div>
                <label htmlFor="rerank_top_n">Return Top-N</label>
                <input id="rerank_top_n" name="rerank_top_n" type="number" min="1" value={formData.rerank_top_n || 3} onChange={handleInputChange} onBlur={handleBlur} />
                <p className="text-xs text-gray-400 mt-1">The final number of documents to return after re-ranking.</p>
            </div>
        </div>
    );

    const renderHttpRequestFields = () => (
        <div className="space-y-4 p-3 bg-slate-50 border border-slate-300 rounded-lg">
            <h4 className="font-bold text-slate-800">API Request Configuration</h4>
            <div>
                <label htmlFor="http_method">HTTP Method</label>
                <select id="http_method" name="http_method" value={formData.http_method || 'GET'} onChange={handleInputChange} onBlur={handleBlur}>
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="PATCH">PATCH</option>
                    <option value="DELETE">DELETE</option>
                </select>
            </div>
            <div>
                <label htmlFor="url_template">Request URL</label>
                <input id="url_template" name="url_template" value={formData.url_template || ''} onChange={handleInputChange} onBlur={handleBlur} placeholder="https://api.example.com/items/{input.item_id}" />
                <p className="text-xs text-gray-400 mt-1">You can use variables like {`{input.var_name}`}.</p>
            </div>
            <div>
                <label htmlFor="headers_template">Headers (JSON format)</label>
                <textarea id="headers_template" name="headers_template" rows={4} value={formData.headers_template || ''} onChange={handleInputChange} onBlur={handleBlur} placeholder={`{\n  "Authorization": "Bearer {context.api_key}"\n}`} />
            </div>
            {['POST', 'PUT', 'PATCH'].includes(formData.http_method?.toUpperCase()) && (
                <div>
                    <label htmlFor="body_template">Body (JSON format)</label>
                    <textarea id="body_template" name="body_template" rows={5} value={formData.body_template || ''} onChange={handleInputChange} onBlur={handleBlur} placeholder={`{\n  "name": "{input.user_name}",\n  "value": 123\n}`} />
                </div>
            )}
        </div>
    );

    const renderIntelligentRouterFields = () => {
        const currentRoutes = formData.routes || {};

        const handleRouteNameChange = (oldName, newName) => {
            if (newName && newName !== oldName) {
                const updatedRoutes = { ...currentRoutes };
                updatedRoutes[newName] = updatedRoutes[oldName];
                delete updatedRoutes[oldName];
                setFormData(prev => ({ ...prev, routes: updatedRoutes }));
            }
        };

        const addRoute = () => {
            const newRouteName = `new_route_${Object.keys(currentRoutes).length + 1}`;
            if (currentRoutes[newRouteName]) return; // Avoid collision
            const updatedRoutes = { ...currentRoutes, [newRouteName]: 'END' };
            setFormData(prev => ({ ...prev, routes: updatedRoutes, _version: (prev._version || 0) + 1 }));
        };

        const removeRoute = (routeName) => {
            const updatedRoutes = { ...currentRoutes };
            delete updatedRoutes[routeName];
            setFormData(prev => ({ ...prev, routes: updatedRoutes, _version: (prev._version || 0) + 1 }));
        };

        return (
            <div className="space-y-4 p-3 bg-fuchsia-50 border border-fuchsia-300 rounded-lg">
                <h4 className="font-bold text-fuchsia-800">Routing Options</h4>
                <p className="text-xs text-gray-500 -mt-2">Define the possible output paths. The LLM will be forced to choose one of these names. The edge connections on the node will be based on these names.</p>
                <div className="space-y-2">
                    {Object.keys(currentRoutes).map(routeName => (
                        <div key={routeName} className="flex items-center gap-2">
                            <input
                                type="text"
                                defaultValue={routeName}
                                onBlur={(e) => handleRouteNameChange(routeName, e.target.value.trim())}
                                placeholder="Route Name"
                                className="flex-grow p-1 border border-gray-300 rounded-md"
                            />
                            <button onClick={() => removeRoute(routeName)} className="p-1 text-red-500 hover:text-red-700">
                                <TrashIcon className="h-5 w-5" />
                            </button>
                        </div>
                    ))}
                </div>
                <button onClick={addRoute} className="w-full text-sm bg-fuchsia-200 text-fuchsia-800 font-semibold py-1 px-3 rounded-md hover:bg-fuchsia-300 transition-colors">
                    + Add Route
                </button>
            </div>
        );
    };

    return (
        <aside className="w-96 bg-gray-50 p-6 border-l border-gray-200 inspector-panel flex flex-col">
            <div className="flex-grow overflow-y-auto pr-2">
                <h3 className="text-xl font-bold text-gray-800 mb-4 capitalize">
                    Edit: {selectedNode.data.label || `${nodeType.replace(/_/g, ' ')} Node`}
                </h3>

                <div className="space-y-4">
                    {renderBaseFields()}

                    {NODES_WITH_PROMPT_TEMPLATE.includes(nodeType) && renderPromptTemplateField()}

                    {NODES_WITH_DATA_SOURCE.includes(nodeType) && renderDataSourceField()}

                    {/* Render fields specific to each node type */}
                    {nodeType === 'agentic_tool_use' && renderToolSelection()}
                    {nodeType === 'workflow_call' && renderWorkflowCallFields()}
                    {nodeType === 'file_ingestion' && renderFileIngestionFields()}
                    {nodeType === 'file_storage' && renderFileStorageFields()}
                    {nodeType === 'http_request' && renderHttpRequestFields()}
                    {nodeType === 'vector_db_ingestion' && renderVectorDbIngestionFields()}
                    {nodeType === 'vector_db_query' && renderVectorDbQueryFields()}
                    {nodeType === 'cross_encoder_rerank' && renderCrossEncoderRerankFields()}
                    {nodeType === 'intelligent_router' && renderIntelligentRouterFields()}

                    {NODES_WITH_OUTPUT_KEY.includes(nodeType) && renderOutputKeyField()}
                </div>
            </div>
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