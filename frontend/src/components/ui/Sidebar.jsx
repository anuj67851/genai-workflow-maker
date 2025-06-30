import React from 'react';
import axios from 'axios';
import { WrenchScrewdriverIcon, QuestionMarkCircleIcon, ChatBubbleLeftRightIcon, UserIcon } from '@heroicons/react/24/outline';
import useWorkflowStore from '../../stores/workflowStore'; // Import the store

const Sidebar = () => {
    const {
        workflowName, setWorkflowName, workflowDescription, setWorkflowDescription,
    } = useWorkflowStore();

    const onDragStart = (event, nodeType) => {
        event.dataTransfer.setData('application/reactflow', nodeType);
        event.dataTransfer.effectAllowed = 'move';
    };

    const nodeTypes = [
        { type: 'agentic_tool_use', label: 'Tool / Agent', icon: <WrenchScrewdriverIcon className="h-6 w-6" /> },
        { type: 'condition_check', label: 'Condition', icon: <QuestionMarkCircleIcon className="h-6 w-6" /> },
        { type: 'human_input', label: 'Human Input', icon: <UserIcon className="h-6 w-6" /> },
        { type: 'llm_response', label: 'LLM Response', icon: <ChatBubbleLeftRightIcon className="h-6 w-6" /> },
    ];

    const handleSaveWorkflow = async () => {
        const currentStoreState = useWorkflowStore.getState();
        if (!currentStoreState.workflowName) {
            alert("Please enter a name for the workflow.");
            return;
        }

        const workflowData = {
            name: currentStoreState.workflowName,
            description: currentStoreState.workflowDescription,
            nodes: currentStoreState.nodes,
            edges: currentStoreState.edges,
        };

        try {
            const response = await axios.post('/api/workflows', workflowData);
            alert(`Workflow "${response.data.name}" saved successfully with ID: ${response.data.id}`);
        } catch (error) {
            console.error("Failed to save workflow:", error);
            alert(`Error: ${error.response?.data?.detail || error.message}`);
        }
    };

    return (
        <aside className="w-80 bg-gray-50 p-4 border-r border-gray-200 flex flex-col shadow-lg z-10">
            {/* Section for Workflow Metadata */}
            <div className="pb-4 border-b border-gray-200">
                <h2 className="text-lg font-bold text-gray-800 mb-2">Workflow Settings</h2>
                <div className="space-y-3">
                    <input
                        type="text"
                        value={workflowName}
                        onChange={(e) => setWorkflowName(e.target.value)}
                        placeholder="Workflow Name"
                        className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    <textarea
                        value={workflowDescription}
                        onChange={(e) => setWorkflowDescription(e.target.value)}
                        placeholder="Workflow Description..."
                        rows={3}
                        className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
                    />
                </div>
            </div>

            {/* Section for Draggable Nodes */}
            <div className="py-4 flex-grow">
                <h2 className="text-lg font-bold text-gray-800 mb-2">Nodes</h2>
                <p className="text-xs text-gray-500 mb-3">Drag nodes to the canvas to build your workflow.</p>
                <div className="space-y-2">
                    {nodeTypes.map((node) => (
                        <div
                            key={node.type}
                            onDragStart={(event) => onDragStart(event, node.type)}
                            draggable
                            className="p-3 border-2 border-dashed border-gray-300 rounded-lg cursor-grab flex items-center gap-3 hover:bg-indigo-50 hover:border-indigo-400 transition-colors"
                        >
                            {node.icon}
                            <span className="font-semibold text-gray-700">{node.label}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Section for Save Button */}
            <div className="pt-4 border-t border-gray-200">
                <button
                    onClick={handleSaveWorkflow}
                    className="w-full bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors"
                >
                    Save Workflow
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;