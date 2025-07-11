import React from 'react';
import BaseNode from './BaseNode';
import { DocumentArrowUpIcon } from '@heroicons/react/24/outline';

const IngestionNode = ({ data, selected }) => {
    const fileTypes = Array.isArray(data.allowed_file_types)
        ? data.allowed_file_types.join(', ') || 'Any'
        : data.allowed_file_types || 'Any';

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

export const IngestionNodeInspector = ({ nodeData, handleChange, handleBlur }) => {
    const displayValue = (Array.isArray(nodeData.allowed_file_types)
        ? nodeData.allowed_file_types.join(', ')
        : nodeData.allowed_file_types) || '';

    return (
        <div className="space-y-4 p-4 bg-orange-50 border border-orange-200 rounded-lg">
            <h4 className="font-bold text-orange-800">File Ingestion Settings</h4>
            <div>
                <label htmlFor="max_files">Maximum Number of Files</label>
                <input id="max_files" name="max_files" type="number" min="1" value={nodeData.max_files ?? 1} onChange={handleChange} onBlur={handleBlur} />
            </div>
            <div>
                <label htmlFor="allowed_file_types">Allowed File Types (comma-separated)</label>
                <input id="allowed_file_types" name="allowed_file_types" value={displayValue} onChange={handleChange} onBlur={handleBlur} placeholder=".pdf, .txt, .csv" />
                <p className="text-xs text-gray-400 mt-1">Leave blank to allow any file type.</p>
            </div>
        </div>
    );
};

export default IngestionNode;