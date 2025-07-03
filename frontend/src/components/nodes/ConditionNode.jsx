import React from 'react';
import BaseNode from './BaseNode';
import { QuestionMarkCircleIcon } from '@heroicons/react/24/outline';

const ConditionNode = ({ data, selected }) => {
    return (
        <BaseNode data={data} selected={selected}>
            <div className="space-y-2">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <QuestionMarkCircleIcon className="h-4 w-4 text-yellow-600" />
                    <span className="font-semibold">Evaluating Condition</span>
                </div>
                <div className="flex justify-between mt-2 px-4">
                    <span className="text-xs font-bold text-green-600">TRUE</span>
                    <span className="text-xs font-bold text-red-600">FALSE</span>
                </div>
            </div>
        </BaseNode>
    );
};

export default ConditionNode;