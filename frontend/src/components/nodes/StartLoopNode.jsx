import React from 'react';
import BaseNode from './BaseNode';
import { Handle, Position } from 'reactflow';
import {ArrowPathIcon, ExclamationTriangleIcon} from '@heroicons/react/24/outline';

const StartLoopNode = ({ data, selected }) => {
    return (
        <BaseNode data={data} selected={selected}>
            <div className="space-y-2">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <ArrowPathIcon className="h-4 w-4 text-rose-600" />
                    <span className="font-semibold">Loop Over Collection</span>
                </div>
                <div className="text-xs text-gray-500">
                    <span className="font-semibold">Looping Over:</span>
                    <span className="font-mono bg-gray-100 px-1 rounded ml-1">
                        {data.input_collection_variable || 'Not Set'}
                    </span>
                </div>
                {data.current_item_output_key ? (
                    <div className="text-xs text-gray-500 pt-1 border-t border-gray-200">
                        <span className="font-semibold">Item Key:</span>
                        <span className="font-mono bg-green-100 text-green-800 px-1 rounded ml-1">
                        {data.current_item_output_key}
                    </span>
                    </div>
                ) : (
                    <div className="flex items-center gap-1 text-xs text-amber-600 pt-1 border-t border-gray-200">
                        <ExclamationTriangleIcon className="h-4 w-4" />
                        <span>Item key not set.</span>
                    </div>
                )}
                {data.output_key ? (
                    <div className="text-xs text-gray-500 pt-1 border-t border-gray-200">
                        <span className="font-semibold">Aggregated Results To:</span>
                        <span className="font-mono bg-green-100 text-green-800 px-1 rounded ml-1">
                            {data.output_key}
                        </span>
                    </div>
                ) : (
                    <div className="flex items-center gap-1 text-xs text-amber-600 pt-1 border-t border-gray-200">
                        <ExclamationTriangleIcon className="h-4 w-4" />
                        <span>Aggregated output key not set.</span>
                    </div>
                )}
                <div className="flex justify-between mt-2 px-1 text-xs font-bold text-center">
                    <span className="text-rose-600">Loop Body</span>
                    <span className="text-gray-600">On Complete</span>
                    <span className="text-red-600">On Failure</span>
                </div>
            </div>

            {/* Custom Handles for the three distinct output paths */}
            <Handle
                type="source"
                position={Position.Bottom}
                id="loopBody" // Output for the loop body
                style={{ left: '25%' }}
                className="!w-4 !h-4 !bg-rose-500"
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="onSuccess" // Output for when loop completes
                style={{ left: '50%' }}
                className="!w-4 !h-4 !bg-gray-500"
            />
            <Handle
                type="source"
                position={Position.Bottom}
                id="onFailure" // Output for catastrophic loop failure
                style={{ left: '75%' }}
                className="!w-4 !h-4 !bg-red-500"
            />
        </BaseNode>
    );
};

export const StartLoopNodeInspector = ({ nodeData, handleChange }) => {
    return (
        <div className="space-y-4 p-4 bg-rose-50 border border-rose-200 rounded-lg">
            <h4 className="font-bold text-rose-800">Start Loop Settings</h4>
            <div>
                <label htmlFor="input_collection_variable">Input Collection Variable</label>
                <input
                    id="input_collection_variable"
                    name="input_collection_variable"
                    value={nodeData.input_collection_variable || ''}
                    onChange={handleChange}
                    placeholder="{input.list_variable_name}"
                />
                <p className="text-xs text-gray-400 mt-1">The variable holding the list/array to iterate over.</p>
            </div>
            <div>
                <label htmlFor="current_item_output_key">Output Key for Current Item</label>
                <input
                    id="current_item_output_key"
                    name="current_item_output_key"
                    value={nodeData.current_item_output_key || ''}
                    onChange={handleChange}
                    placeholder="e.g., current_doc, item"
                />
                <p className="text-xs text-gray-400 mt-1">The name for the variable holding the item in each iteration.</p>
            </div>
        </div>
    );
};

export default StartLoopNode;