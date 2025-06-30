import React from 'react';
import NodeWrapper from './NodeWrapper';
import { QuestionMarkCircleIcon } from '@heroicons/react/24/outline';

const ConditionNode = ({ data, selected }) => {
    return (
        <NodeWrapper data={data} selected={selected}>
            <div className="flex flex-col gap-2 text-center">
                <div className="flex items-center justify-center text-gray-500 gap-1">
                    <QuestionMarkCircleIcon className="h-4 w-4" />
                    <label className="block text-xs font-semibold">EVALUATION</label>
                </div>
                <p className="text-gray-800 p-2 bg-gray-50 rounded-md break-words">
                    {data.prompt_template || 'Is a condition true?'}
                </p>
                <div className="flex justify-between mt-2 px-4">
                    <span className="text-xs font-bold text-green-600">TRUE</span>
                    <span className="text-xs font-bold text-red-600">FALSE</span>
                </div>
            </div>
        </NodeWrapper>
    );
};

export default ConditionNode;