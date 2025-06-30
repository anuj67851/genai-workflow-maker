import React from 'react';
import NodeWrapper from './NodeWrapper';
import { ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline';

const LLMResponseNode = ({ data, selected }) => {
    return (
        <NodeWrapper data={data} selected={selected}>
            <div className="flex flex-col gap-2">
                <div className="flex items-center text-gray-500 gap-1">
                    <ChatBubbleLeftRightIcon className="h-4 w-4" />
                    <label className="block text-xs font-semibold">LLM INSTRUCTION</label>
                </div>
                <p className="text-gray-800 p-2 bg-gray-50 rounded-md break-words">
                    {data.prompt_template || 'Synthesize a response for the user...'}
                </p>
            </div>
        </NodeWrapper>
    );
};

export default LLMResponseNode;