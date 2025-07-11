import React from 'react';
import BaseNode from './BaseNode';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';

const VectorDBQueryNode = ({ data, selected }) => {

    return (
        <BaseNode data={data} selected={selected}>
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

export const VectorDBQueryNodeInspector = ({ nodeData, handleChange, handleBlur }) => {
    return (
        <div className="space-y-4 p-4 bg-teal-50 border border-teal-200 rounded-lg">
            <h4 className="font-bold text-teal-800">Vector Query Settings</h4>
            <div>
                <label htmlFor="collection_name">Collection Name</label>
                <input id="collection_name" name="collection_name" value={nodeData.collection_name || ''} onChange={handleChange} placeholder="e.g., project_docs_v1"/>
            </div>
            <div>
                <label htmlFor="top_k">Top-K</label>
                <input id="top_k" name="top_k" type="number" min="1" value={nodeData.top_k ?? 5} onChange={handleChange} onBlur={handleBlur} />
                <p className="text-xs text-gray-400 mt-1">The number of initial documents to retrieve.</p>
            </div>
        </div>
    );
};

export default VectorDBQueryNode;