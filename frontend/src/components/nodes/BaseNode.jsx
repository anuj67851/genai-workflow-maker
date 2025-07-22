import React from 'react';
import { Handle, Position } from 'reactflow';

const typeStyles = {
    agentic_tool_use: { bg: 'bg-node-tool', border: 'border-node-tool', title: 'Tool / Agent' },
    condition_check: { bg: 'bg-node-condition', border: 'border-node-condition', title: 'Condition' },
    human_input: { bg: 'bg-node-human', border: 'border-node-human', title: 'Human Input' },
    llm_response: { bg: 'bg-node-response', border: 'border-node-response', title: 'LLM Response' },
    workflow_call: { bg: 'bg-node-workflow', border: 'border-node-workflow', title: 'Run Workflow' },
    file_ingestion: { bg: 'bg-node-file', border: 'border-node-file', title: 'File Ingestion' },
    file_storage: { bg: 'bg-node-file', border: 'border-node-file', title: 'File Storage' },
    vector_db_ingestion: { bg: 'bg-node-vector', border: 'border-node-vector', title: 'Vector Ingestion' },
    vector_db_query: { bg: 'bg-node-vector', border: 'border-node-vector', title: 'Vector Query' },
    cross_encoder_rerank: { bg: 'bg-node-vector', border: 'border-node-vector', title: 'Re-Rank Results' },
    http_request: { bg: 'bg-node-api', border: 'border-node-api', title: 'API Request' },
    intelligent_router: { bg: 'bg-node-router', border: 'border-node-router', title: 'Intelligent Router' },
    database_query: { bg: 'bg-node-database', border: 'border-node-database', title: 'Database Query' },
    database_save: { bg: 'bg-node-database', border: 'border-node-database', title: 'Database Save' },
    direct_tool_call: { bg: 'bg-node-direct-tool-call', border: 'border-node-direct-tool-call', title: 'Direct Tool Call' },
    default: { bg: 'bg-gray-200', border: 'border-gray-400', title: 'Node' },
};

const BaseNode = ({ data, selected, children }) => {
    const action_type = data?.action_type || 'default';
    const styles = typeStyles[action_type] || typeStyles.default;
    const selectionClass = selected ? 'shadow-lg ring-2 ring-indigo-500' : 'shadow-md';
    const displayTitle = data?.label || styles.title;

    // Truncate long prompts for display on the node
    const truncate = (text, length = 60) => {
        if (!text) return '';
        if (text.length <= length) return text;
        return text.substring(0, length) + '...';
    };

    return (
        <div className={`w-64 rounded-lg border-2 ${styles.border} ${selectionClass}`}>
            <Handle type="target" position={Position.Top} className="!w-4 !h-4 !bg-gray-500" />

            <div className={`px-3 py-1 text-sm font-bold text-gray-700 rounded-t-md ${styles.bg}`}>
                {displayTitle}
            </div>

            <div className="p-3 bg-white text-sm text-gray-700 space-y-2">
                {/* Render children passed to the BaseNode */}
                {children}

                {/* Requirement 4: Common display for prompt_template */}
                {data.prompt_template && data.action_type !== 'condition_check' && (
                    <div className="mt-2 p-2 bg-gray-50 border-t border-gray-200">
                        <p className="text-xs text-gray-400 italic break-words">
                            "{truncate(data.prompt_template)}"
                        </p>
                    </div>
                )}
            </div>

            {/* Conditional rendering for handles based on node type */}
            {action_type === 'condition_check' ? (
                <>
                    <Handle type="source" position={Position.Bottom} id="onSuccess" style={{ left: '33%' }} className="!w-4 !h-4 !bg-green-500" />
                    <Handle type="source" position={Position.Bottom} id="onFailure" style={{ left: '66%' }} className="!w-4 !h-4 !bg-red-500" />
                </>
            ) : action_type === 'intelligent_router' ? null : (
                <Handle type="source" position={Position.Bottom} className="!w-4 !h-4 !bg-gray-500" />
            )}
        </div>
    );
};

export default BaseNode;