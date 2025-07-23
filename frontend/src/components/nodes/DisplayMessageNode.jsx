import React from 'react';
import BaseNode from './BaseNode';
import { ChatBubbleBottomCenterTextIcon } from '@heroicons/react/24/outline';

const DisplayMessageNode = ({ data, selected }) => {
    return (
        <BaseNode data={data} selected={selected}>
            <div className="space-y-2">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <ChatBubbleBottomCenterTextIcon className="h-4 w-4 text-indigo-600" />
                    <span className="font-semibold">Displaying a message...</span>
                </div>
                {/* The BaseNode will automatically render the prompt_template preview */}
                {data.output_key && (
                    <div className="text-xs text-gray-500 pt-1 border-t border-gray-200">
                        <span className="font-semibold">Saves Message To:</span>
                        <span className="font-mono bg-green-100 text-green-800 px-1 rounded ml-1">
                            {data.output_key}
                        </span>
                    </div>
                )}
            </div>
        </BaseNode>
    );
};

export default DisplayMessageNode;