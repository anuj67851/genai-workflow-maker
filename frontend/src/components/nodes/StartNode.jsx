import React from 'react';
import { Handle, Position } from 'reactflow';
import { PlayIcon } from '@heroicons/react/24/solid';

const StartNode = ({ selected }) => {
    const selectionClass = selected ? `ring-2 ring-indigo-500` : '';

    return (
        <div className={`w-32 h-16 bg-node-start border-2 border-node-start rounded-lg shadow-md flex items-center justify-center ${selectionClass}`}>
            <div className="flex items-center gap-2">
                <PlayIcon className="h-6 w-6 text-gray-600" />
                <span className="text-lg font-bold text-gray-700">START</span>
            </div>
            <Handle
                type="source"
                position={Position.Bottom}
                className="!w-4 !h-4 !bg-gray-500"
            />
        </div>
    );
};

export default StartNode;