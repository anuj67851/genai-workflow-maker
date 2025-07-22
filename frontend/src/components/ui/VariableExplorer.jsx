import React, { useMemo } from 'react';
import useWorkflowStore from '../../stores/workflowStore';
import { ClipboardDocumentIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const VariableExplorer = () => {
    // Subscribe to the nodes from the Zustand store
    const nodes = useWorkflowStore(state => state.nodes);

    // useMemo will re-calculate the variables only when the nodes array changes.
    const availableVariables = useMemo(() => {
        const outputKeys = nodes
            .map(node => node.data?.output_key) // Get all output_key values
            .filter(Boolean);                   // Filter out null, undefined, or empty strings

        // Return a sorted list of unique keys
        return [...new Set(outputKeys)].sort();
    }, [nodes]);

    const handleCopyVariable = (variableName) => {
        const variableTemplate = `{input.${variableName}}`;
        navigator.clipboard.writeText(variableTemplate);
        toast.success(`Copied "${variableTemplate}" to clipboard!`);
    };

    return (
        <div>
            <p className="text-xs text-gray-500 mb-3">Click a variable to copy its template name for use in node settings.</p>
            <div className="space-y-1 pr-2">
                {availableVariables.length > 0 ? (
                    availableVariables.map(variable => (
                        <button
                            key={variable}
                            onClick={() => handleCopyVariable(variable)}
                            className="w-full flex items-center justify-between p-2 text-left bg-gray-100 rounded-md hover:bg-indigo-100 group"
                        >
                            <span className="font-mono text-sm text-indigo-800">{variable}</span>
                            <ClipboardDocumentIcon className="h-5 w-5 text-gray-400 group-hover:text-indigo-600" />
                        </button>
                    ))
                ) : (
                    <p className="text-sm text-gray-400 italic text-center py-4">No output variables defined in this workflow yet.</p>
                )}
            </div>
        </div>
    );
};

export default VariableExplorer;