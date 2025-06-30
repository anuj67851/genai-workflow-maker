import React, { useEffect, useState } from 'react';
import useWorkflowStore from '../../stores/workflowStore';
import { useReactFlow } from 'reactflow';

// This is the panel that appears on the right side to edit the selected node's properties.
const InspectorPanel = ({ selectedNode }) => {
    // Get the state and actions from our Zustand store
    const { tools, updateNodeData } = useWorkflowStore();

    // Local state to manage the form inputs to avoid re-rendering the whole canvas on every keystroke
    const [formData, setFormData] = useState({});

    useEffect(() => {
        // When a new node is selected, update the form data to reflect that node's data
        if (selectedNode) {
            setFormData(selectedNode.data);
        }
    }, [selectedNode]);

    const handleInputChange = (event) => {
        const { name, value } = event.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleBlur = () => {
        // When the user clicks away from an input, update the global state
        // This is more performant than updating on every keystroke.
        if (selectedNode) {
            updateNodeData(selectedNode.id, formData);
        }
    };

    // Render nothing if no node is selected
    if (!selectedNode || ['startNode', 'endNode'].includes(selectedNode.type)) {
        return (
            <aside className="w-96 bg-gray-50 p-6 border-l border-gray-200 inspector-panel">
                <h3 className="text-xl font-bold text-gray-800">Properties</h3>
                <p className="mt-2 text-sm text-gray-500">Select a node on the canvas to view and edit its properties.</p>
            </aside>
        );
    }

    // --- Render different forms based on the selected node's type ---

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
        <aside className="w-96 bg-gray-50 p-6 border-l border-gray-200 inspector-panel">
            <h3 className="text-xl font-bold text-gray-800 mb-4 capitalize">
                Edit: {selectedNode.type.replace('Node', ' Node')}
            </h3>
            <div className="space-y-4">
                {renderCommonFields()}
                {selectedNode.type === 'human_inputNode' && renderHumanInputFields()}
                {/* We can add specific fields for other node types here in the future */}
            </div>
        </aside>
    );
};

export default InspectorPanel;