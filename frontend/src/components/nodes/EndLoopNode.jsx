import React from 'react';
import { Handle, Position } from 'reactflow';
import { ArrowUturnLeftIcon } from '@heroicons/react/24/solid';

const EndLoopNode = ({ data, selected }) => {
    const selectionClass = selected ? `ring-2 ring-indigo-500` : '';
    const nodeClass = 'bg-node-loop border-node-loop';

    return (
        <div className={`w-48 h-auto min-h-[4rem] rounded-lg shadow-md flex flex-col justify-center border-2 ${nodeClass} ${selectionClass}`}>
            <Handle
                type="target"
                position={Position.Top}
                className="!w-4 !h-4 !bg-gray-500"
            />
            <div className="flex items-center justify-center gap-2 py-2">
                <ArrowUturnLeftIcon className="h-6 w-6 text-rose-700" />
                <span className="text-lg font-bold text-rose-800">End Loop</span>
            </div>
            {/* ---Display the configured return value --- */}
            {data.value_to_return && (
                <div className="text-xs text-center text-gray-700 bg-gray-50 py-1 border-t border-rose-200">
                    <span className="font-semibold">Returns: </span>
                    <span className="font-mono bg-gray-200 px-1 rounded">{data.value_to_return}</span>
                </div>
            )}
        </div>
    );
};

export const EndLoopNodeInspector = ({ nodeData, handleChange }) => {
    return (
        <div className="space-y-4 p-4 bg-rose-50 border border-rose-200 rounded-lg">
            <h4 className="font-bold text-rose-800">End Loop Settings</h4>
            <div>
                <label htmlFor="value_to_return">Value to Return (Optional)</label>
                <input
                    id="value_to_return"
                    name="value_to_return"
                    value={nodeData.value_to_return || ''}
                    onChange={handleChange}
                    placeholder="{input.variable_to_aggregate}"
                />
                <p className="text-xs text-gray-400 mt-1">
                    Specify which variable's value from this iteration should be added to the loop's final results. If blank, it defaults to the output of the previous step.
                </p>
            </div>
        </div>
    );
};


export default EndLoopNode;