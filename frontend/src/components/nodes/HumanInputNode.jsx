import React from 'react';
import BaseNode from './BaseNode';
import { UserIcon } from '@heroicons/react/24/outline';

const HumanInputNode = ({ data, selected }) => {
    return (
        <BaseNode data={data} selected={selected}>
            <div className="space-y-2">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <UserIcon className="h-4 w-4 text-green-600" />
                    <span className="font-semibold">Awaiting User Input</span>
                </div>
                {data.output_key ? (
                    <div className="text-xs text-gray-500">
                        <span className="font-semibold">Saves to:</span>
                        <span className="font-mono bg-green-100 text-green-800 px-1 rounded ml-1">
                            {data.output_key}
                        </span>
                    </div>
                ) : (
                    <div className="text-xs text-red-500">
                        <span className="font-semibold">Warning:</span>
                        <span> Output key not set.</span>
                    </div>
                )}
            </div>
        </BaseNode>
    );
};

export default HumanInputNode;