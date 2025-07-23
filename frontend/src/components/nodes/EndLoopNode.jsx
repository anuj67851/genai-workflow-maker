import React from 'react';
import { Handle, Position } from 'reactflow';
import { ArrowUturnLeftIcon } from '@heroicons/react/24/solid';

const EndLoopNode = ({ selected }) => {
    const selectionClass = selected ? `ring-2 ring-indigo-500` : '';
    const nodeClass = 'bg-node-loop border-node-loop';

    return (
        <div className={`w-48 h-16 rounded-lg shadow-md flex items-center justify-center border-2 ${nodeClass} ${selectionClass}`}>
            <Handle
                type="target"
                position={Position.Top}
                className="!w-4 !h-4 !bg-gray-500"
            />
            <div className="flex items-center gap-2">
                <ArrowUturnLeftIcon className="h-6 w-6 text-rose-700" />
                <span className="text-lg font-bold text-rose-800">End Loop</span>
            </div>
        </div>
    );
};

export default EndLoopNode;