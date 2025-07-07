import React from 'react';
import BaseNode from './BaseNode';
import { ArchiveBoxIcon } from '@heroicons/react/24/outline';

const FileStorageNode = ({ data, selected }) => {

    return (
        <BaseNode data={data} selected={selected}>
            <div className="space-y-2">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <ArchiveBoxIcon className="h-4 w-4 text-orange-600" />
                    <span className="font-semibold">Requesting File to Store</span>
                </div>

                <div className="text-xs text-gray-500">
                    <span className="font-semibold">Storage Path:</span>
                    <span className="font-mono bg-gray-100 px-1 rounded ml-1">
                        {data.storage_path || 'default'}
                    </span>
                </div>

                {data.output_key ? (
                    <div className="text-xs text-gray-500 mt-1">
                        <span className="font-semibold">Saves Paths to:</span>
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

export default FileStorageNode;