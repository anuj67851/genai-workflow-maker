import React from 'react';
import BaseNode from './BaseNode';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';

// Override typeStyles for this specific node type
const typeStyles = {
    vector_db_query: { bg: 'bg-node-vector', border: 'border-node-vector', title: 'Vector Query' },
};

const VectorDBQueryNode = ({ data, selected }) => {
    // Manually set action_type for BaseNode styling
    const styledData = { ...data, action_type: 'vector_db_query' };

    return (
        <BaseNode data={styledData} selected={selected} typeStyles={typeStyles}>
            <div className="space-y-2">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <MagnifyingGlassIcon className="h-4 w-4 text-teal-600" />
                    <span className="font-semibold">Querying Collection</span>
                </div>

                <div className="text-xs text-gray-500">
                    <span className="font-semibold">Collection:</span>
                    <span className="font-mono bg-gray-100 px-1 rounded ml-1">
                        {data.collection_name || 'Not Set'}
                    </span>
                </div>

                <div className="text-xs text-gray-500">
                    <span className="font-semibold">Retrieve Top-K:</span>
                    <span className="font-mono bg-gray-100 px-1 rounded ml-1">{data.top_k || 5}</span>
                </div>

                {data.output_key ? (
                    <div className="text-xs text-gray-500 pt-1 border-t border-gray-200">
                        <span className="font-semibold">Saves to:</span>
                        <span className="font-mono bg-green-100 text-green-800 px-1 rounded ml-1">
                            {data.output_key}
                        </span>
                    </div>
                ) : (
                    <div className="text-xs text-red-500 pt-1 border-t border-gray-200">
                        <span className="font-semibold">Warning:</span>
                        <span> Output key not set.</span>
                    </div>
                )}
            </div>
        </BaseNode>
    );
};

export default VectorDBQueryNode;