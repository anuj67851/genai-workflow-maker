import React from 'react';
import BaseNode from './BaseNode';
import { DocumentArrowUpIcon } from '@heroicons/react/24/outline';

const IngestionNode = ({ data, selected }) => {
    const fileTypes = data.allowed_file_types?.length > 0
        ? data.allowed_file_types.join(', ')
        : 'Any';

    return (
        <BaseNode data={data} selected={selected}>
            <div className="space-y-2">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <DocumentArrowUpIcon className="h-4 w-4 text-orange-600" />
                    <span className="font-semibold">Requesting File Upload</span>
                </div>

                <div className="text-xs text-gray-500">
                    <span className="font-semibold">Max Files:</span>
                    <span className="font-mono bg-gray-100 px-1 rounded ml-1">{data.max_files || 1}</span>
                </div>

                <div className="text-xs text-gray-500">
                    <span className="font-semibold">Allowed Types:</span>
                    <span className="font-mono bg-gray-100 px-1 rounded ml-1">{fileTypes}</span>
                </div>

                {data.output_key ? (
                    <div className="text-xs text-gray-500 mt-1">
                        <span className="font-semibold">Saves to:</span>
                        <span className="font-mono bg-green-100 text-green-800 px-1 rounded ml-1">{data.output_key}</span>
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

export default IngestionNode;