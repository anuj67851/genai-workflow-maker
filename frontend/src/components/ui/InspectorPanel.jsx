import React, { useEffect, useState } from 'react';
import useWorkflowStore from '../../stores/workflowStore';
import { TrashIcon } from '@heroicons/react/24/solid';

const InspectorPanel = ({ selection }) => {
    const { onNodesChange, onEdgesChange } = useWorkflowStore();
    const { updateNodeData } = useWorkflowStore.getState();
    const [formData, setFormData] = useState({});

    const selectedNode = selection?.nodes[0];

    useEffect(() => {
        if (selectedNode) {
            setFormData(selectedNode.data);
        }
    }, [selectedNode]);

    const handleInputChange = (event) => {
        const { name, value } = event.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleBlur = () => {
        if (selectedNode) {
            updateNodeData(selectedNode.id, formData);
        }
    };

    const handleDelete = () => {
        if (!selection || (selection.nodes.length === 0 && selection.edges.length === 0)) return;

        if (window.confirm(`Are you sure you want to delete the selected element(s)?`)) {
            // Trigger the standard onNodesChange/onEdgesChange events with 'remove' actions.
            // The store's handlers will now correctly process these.
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

    // Fully defined render functions to avoid ambiguity
    const renderCommonFields = () => (
        <>
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

    const renderHumanInputFields = () => (
        <div>
            <label htmlFor="output_key">Output Variable Name</label>
            <input
                type="text"
                id="output_key"
                name="output_key"
                value={formData.output_key || ''}
                onChange={handleInputChange}
                onBlur={handleBlur}
                placeholder="e.g., user_email, ticket_id"
            />
            <p className="text-xs text-gray-400 mt-1">The name used to store the user's answer for later steps.</p>
        </div>
    );

    return (
        <aside className="w-96 bg-gray-50 p-6 border-l border-gray-200 inspector-panel flex flex-col">
            <div className="flex-grow">
                <h3 className="text-xl font-bold text-gray-800 mb-4 capitalize">
                    Edit: {selectedNode.type.replace('Node', ' Node')}
                </h3>
                <div className="space-y-4">
                    {renderCommonFields()}
                    {selectedNode.type === 'human_inputNode' && renderHumanInputFields()}
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