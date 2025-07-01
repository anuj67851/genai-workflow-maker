import React, { useEffect, useState } from 'react';
import useWorkflowStore from '../../stores/workflowStore';
import { TrashIcon } from '@heroicons/react/24/solid';

const InspectorPanel = ({ selection }) => {
    const { onNodesChange, onEdgesChange, updateNodeData, tools, fetchTools } = useWorkflowStore(state => ({
        onNodesChange: state.onNodesChange,
        onEdgesChange: state.onEdgesChange,
        updateNodeData: state.updateNodeData,
        tools: state.tools,
        fetchTools: state.fetchTools,
    }));

    const [formData, setFormData] = useState({});
    const selectedNode = selection?.nodes[0];

    useEffect(() => {
        if (tools.length === 0) {
            fetchTools();
        }
    }, [fetchTools, tools.length]);

    useEffect(() => {
        if (selectedNode) {
            setFormData({
                label: '',
                description: '',
                prompt_template: '',
                output_key: '',
                tool_selection: 'auto', // Default value
                tool_names: [],
                ...selectedNode.data,
            });
        }
    }, [selectedNode]);

    const handleInputChange = (event) => {
        const { name, value } = event.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

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
            if (selection.nodes.length > 0) {
                onNodesChange(selection.nodes.map(n => ({ id: n.id, type: 'remove' })));
            }
            if (selection.edges.length > 0) {
                onEdgesChange(selection.edges.map(e => ({ id: e.id, type: 'remove' })));
            }
        }
    };

    const isDeletable = selectedNode && !['startNode', 'endNode'].includes(selectedNode.type);

    if (!selectedNode) {
        return (
            <aside className="w-96 bg-gray-50 p-6 border-l border-gray-200 inspector-panel">
                <h3 className="text-xl font-bold text-gray-800">Properties</h3>
                <p className="mt-2 text-sm text-gray-500">Select a node on the canvas to view and edit its properties.</p>
            </aside>
        );
    }

    const renderCommonFields = () => (
        <>
            <div>
                <label htmlFor="label">Node Label (Optional)</label>
                <input
                    type="text"
                    id="label"
                    name="label"
                    value={formData.label || ''}
                    onChange={handleInputChange}
                    onBlur={handleBlur}
                    placeholder="e.g., Check User Warranty"
                />
                <p className="text-xs text-gray-400 mt-1">A custom title for this node in the graph.</p>
            </div>
            <div>
                <label htmlFor="description">Description</label>
                <input
                    type="text"
                    id="description"
                    name="description"
                    value={formData.description || ''}
                    onChange={handleInputChange}
                    onBlur={handleBlur}
                    placeholder="A brief summary of this step"
                />
            </div>
            <div>
                <label htmlFor="prompt_template">Prompt / Instruction</label>
                <textarea
                    id="prompt_template"
                    name="prompt_template"
                    rows={5}
                    value={formData.prompt_template || ''}
                    onChange={handleInputChange}
                    onBlur={handleBlur}
                    placeholder="The detailed instruction for the LLM or user."
                />
                <p className="text-xs text-gray-400 mt-1">You can use variables like {`{query}`} or {`{input.variable_name}`}.</p>
            </div>
        </>
    );

    const renderOutputKeyField = () => (
        <div>
            <label htmlFor="output_key">Output Variable Name (Optional)</label>
            <input
                type="text"
                id="output_key"
                name="output_key"
                value={formData.output_key || ''}
                onChange={handleInputChange}
                onBlur={handleBlur}
                placeholder="e.g., user_email, ticket_id"
            />
            <p className="text-xs text-gray-400 mt-1">Saves the step's result to this variable for later use.</p>
        </div>
    );

    const renderToolSelection = () => (
        <div>
            <label>Tool Usage</label>
            <div className="space-y-3 rounded-md border border-gray-200 p-3 bg-white">
                {/* --- BUG FIX STARTS HERE: Replaced flex with a rigid 2-column grid for alignment --- */}
                {/* Option 1: Auto */}
                <div className="grid grid-cols-[auto_1fr] items-center gap-x-3">
                    <input type="radio" id="tool_auto" name="tool_selection" value="auto" checked={formData.tool_selection === 'auto'} onChange={handleInputChange} onBlur={handleBlur} className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300" />
                    <label htmlFor="tool_auto" className="text-sm font-medium text-gray-700">Let agent decide from all available tools</label>
                </div>
                {/* Option 2: Manual */}
                <div className="grid grid-cols-[auto_1fr] items-center gap-x-3">
                    <input type="radio" id="tool_manual" name="tool_selection" value="manual" checked={formData.tool_selection === 'manual'} onChange={handleInputChange} onBlur={handleBlur} className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300" />
                    <label htmlFor="tool_manual" className="text-sm font-medium text-gray-700">Select specific tools for the agent</label>
                </div>
                {/* Option 3: None */}
                <div className="grid grid-cols-[auto_1fr] items-center gap-x-3">
                    <input type="radio" id="tool_none" name="tool_selection" value="none" checked={formData.tool_selection === 'none'} onChange={handleInputChange} onBlur={handleBlur} className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300" />
                    <label htmlFor="tool_none" className="text-sm font-medium text-gray-700">Do not use any tools (direct LLM response)</label>
                </div>
                {/* --- BUG FIX ENDS HERE --- */}
            </div>

            {formData.tool_selection === 'manual' && (
                <div className="mt-2 p-3 border border-gray-200 rounded-md bg-gray-50 max-h-48 overflow-y-auto space-y-2">
                    <p className="text-xs text-gray-500 mb-2">Select one or more tools for the agent to use:</p>
                    {/* --- BUG FIX STARTS HERE: Applied the same grid layout to the checkboxes --- */}
                    {tools.map(tool => (
                        <div key={tool.function.name} className="grid grid-cols-[auto_1fr] items-center gap-x-3">
                            <input
                                type="checkbox"
                                id={`tool-chk-${tool.function.name}`}
                                name={tool.function.name}
                                checked={formData.tool_names?.includes(tool.function.name) || false}
                                onChange={handleToolSelectionChange}
                                onBlur={handleBlur}
                                className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                            />
                            <label htmlFor={`tool-chk-${tool.function.name}`} className="text-sm text-gray-900 font-mono">
                                {tool.function.name}
                            </label>
                        </div>
                    ))}
                    {/* --- BUG FIX ENDS HERE --- */}
                </div>
            )}
        </div>
    );

    const nodeType = selectedNode.type.replace('Node', '');

    return (
        <aside className="w-96 bg-gray-50 p-6 border-l border-gray-200 inspector-panel flex flex-col">
            <div className="flex-grow overflow-y-auto pr-2">
                <h3 className="text-xl font-bold text-gray-800 mb-4 capitalize">
                    Edit: {selectedNode.data.label || `${nodeType.replace(/_/g, ' ')} Node`}
                </h3>
                <div className="space-y-4">
                    {renderCommonFields()}
                    {['human_input', 'agentic_tool_use', 'llm_response'].includes(nodeType) && renderOutputKeyField()}
                    {nodeType === 'agentic_tool_use' && renderToolSelection()}
                </div>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-200">
                <button
                    onClick={handleDelete}
                    disabled={!isDeletable}
                    className="w-full flex items-center justify-center gap-2 bg-red-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-red-700 disabled:bg-red-300 disabled:cursor-not-allowed transition-colors"
                >
                    <TrashIcon className="h-5 w-5"/>
                    Delete Node
                </button>
                {!isDeletable && (
                    <p className="text-xs text-center text-gray-500 mt-2">
                        The START and END nodes cannot be deleted.
                    </p>
                )}
            </div>
        </aside>
    );
};

export default InspectorPanel;