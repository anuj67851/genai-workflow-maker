import React from 'react';
import NodeWrapper from './NodeWrapper';
import { InformationCircleIcon } from '@heroicons/react/24/outline';

const HumanInputNode = ({ data, selected }) => {
    return (
        <NodeWrapper data={data} selected={selected}>
            <div className="flex flex-col gap-2">
                <div>
                    <label className="block text-xs font-semibold text-gray-500 mb-1">PROMPT FOR USER</label>
                    <p className="text-gray-800 p-2 bg-gray-50 rounded-md break-words">
                        {data.prompt_template || 'Please provide input...'}
                    </p>
                </div>
                <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded-md">
                    <div className="flex items-center gap-2">
                        <InformationCircleIcon className="h-5 w-5 text-green-600" />
                        <div>
                            <p className="text-xs font-bold text-green-700">Output Saved As:</p>
                            <p className="text-sm font-mono text-green-800">{data.output_key || 'not_set'}</p>
                        </div>
                    </div>
                </div>
            </div>
        </NodeWrapper>
    );
};

export default HumanInputNode;