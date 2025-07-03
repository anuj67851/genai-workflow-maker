import React from 'react';
import BaseNode from './BaseNode';
import { WrenchScrewdriverIcon, CheckBadgeIcon, CircleStackIcon } from '@heroicons/react/24/outline';

const ToolNode = ({ data, selected }) => {
    const renderToolInfo = () => {
        if (data.tool_selection === 'manual' && data.tool_names?.length > 0) {
            return (
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <CheckBadgeIcon className="h-4 w-4 text-blue-500" />
                    <span className="font-semibold">Manual:</span>
                    <span className="font-mono bg-gray-100 px-1 rounded">{data.tool_names.join(', ')}</span>
                </div>
            );
        }
        if (data.tool_selection === 'none') {
            return (
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <CircleStackIcon className="h-4 w-4 text-gray-400" />
                    <span className="font-semibold">Mode:</span>
                    <span>No Tools</span>
                </div>
            )
        }
        // Default to 'auto'
        return (
            <div className="flex items-center gap-1 text-xs text-gray-500">
                <WrenchScrewdriverIcon className="h-4 w-4 text-indigo-500" />
                <span className="font-semibold">Mode:</span>
                <span>Auto</span>
            </div>
        );
    };

    return (
        <BaseNode data={data} selected={selected}>
            <div className="space-y-2">
                {renderToolInfo()}
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

export default ToolNode;