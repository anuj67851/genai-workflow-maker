import React from 'react';
import { Handle, Position } from 'reactflow';
import { StopCircleIcon } from '@heroicons/react/24/solid';

const EndNode = ({ selected }) => {
    const selectionClass = selected ? `ring-2 ring-indigo-500` : '';

    return (
        <div className={`w-32 h-16 bg-node-start border-2 border-node-start rounded-lg shadow-md flex items-center justify-center ${selectionClass}`}>
            <Handle
                type="target"
                position={Position.Top}
                className="!w-4 !h-4 !bg-gray-500"
            />
            <div className="flex items-center gap-2">
                <StopCircleIcon className="h-6 w-6 text-gray-600" />
                <span className="text-lg font-bold text-gray-700">END</span>
            </div>
        </div>
    );
};

export default EndNode;