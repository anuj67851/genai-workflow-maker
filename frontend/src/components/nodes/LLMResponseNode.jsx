import React from 'react';
import BaseNode from './BaseNode';
import { ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline';

const LLMResponseNode = ({ data, selected }) => {
    return (
        <BaseNode data={data} selected={selected}>
            <div className="space-y-2">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <ChatBubbleLeftRightIcon className="h-4 w-4 text-cyan-600" />
                    <span className="font-semibold">Generates Response</span>
                </div>
                {data.output_key && (
                    <div className="text-xs text-gray-500">
                        <span className="font-semibold">Saves to:</span>
                        <span className="font-mono bg-green-100 text-green-800 px-1 rounded ml-1">{data.output_key}</span>
                    </div>
                )}
            </div>
        </BaseNode>
    );
};

export default LLMResponseNode;