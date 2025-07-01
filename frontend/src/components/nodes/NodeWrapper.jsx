import React from 'react';
import { Handle, Position } from 'reactflow';

const NodeWrapper = ({ data, children, selected }) => {
    const action_type = data?.action_type || 'default';
    const customLabel = data?.label;

    const typeStyles = {
        agentic_tool_use: { bg: 'bg-node-tool', border: 'border-node-tool', title: 'Tool / Agent' },
        condition_check: { bg: 'bg-node-condition', border: 'border-node-condition', title: 'Condition' },
        human_input: { bg: 'bg-node-human', border: 'border-node-human', title: 'Human Input' },
        llm_response: { bg: 'bg-node-response', border: 'border-node-response', title: 'LLM Response' },
        default: { bg: 'bg-gray-200', border: 'border-gray-400', title: 'Node' },
    };

    const styles = typeStyles[action_type] || typeStyles.default;
    const selectionClass = selected ? `shadow-lg ring-2 ring-indigo-500` : 'shadow-md';
    const displayTitle = customLabel || styles.title;

    return (
        <div className={`w-64 rounded-lg border-2 ${styles.border} ${selectionClass}`}>
            <Handle type="target" position={Position.Top} className="!w-4 !h-4 !bg-gray-500" />

            <div className={`px-3 py-1 text-sm font-bold text-gray-700 rounded-t-md ${styles.bg}`}>
                {displayTitle}
            </div>

            <div className="p-3 bg-white text-sm text-gray-700">
                {children}
            </div>

            {action_type === 'condition_check' ? (
                <>
                    <Handle type="source" position={Position.Bottom} id="onSuccess" style={{ left: '33%' }} className="!w-4 !h-4 !bg-green-500" />
                    <Handle type="source" position={Position.Bottom} id="onFailure" style={{ left: '66%' }} className="!w-4 !h-4 !bg-red-500" />
                </>
            ) : (
                <Handle type="source" position={Position.Bottom} className="!w-4 !h-4 !bg-gray-500" />
            )}
        </div>
    );
};

export default NodeWrapper;