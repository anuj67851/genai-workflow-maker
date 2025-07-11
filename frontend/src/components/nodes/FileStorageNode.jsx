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

export const FileStorageNodeInspector = ({ nodeData, handleChange, handleBlur }) => {
    // It now correctly handles an array, a string, or a null/undefined value.
    const displayValue = (Array.isArray(nodeData.allowed_file_types)
        ? nodeData.allowed_file_types.join(', ')
        : nodeData.allowed_file_types) || '';

    return (
        <div className="space-y-4 p-4 bg-orange-50 border border-orange-200 rounded-lg">
            <h4 className="font-bold text-orange-800">File Storage Settings</h4>
            <div>
                <label htmlFor="storage_path">Storage Subdirectory (Optional)</label>
                <input id="storage_path" name="storage_path" value={nodeData.storage_path || ''} onChange={handleChange} placeholder="e.g., ticket_attachments" />
                <p className="text-xs text-gray-400 mt-1">A subdirectory within the main attachments folder to save this file to.</p>
            </div>
            <div>
                <label htmlFor="max_files">Maximum Number of Files</label>
                <input id="max_files" name="max_files" type="number" min="1" value={nodeData.max_files ?? 1} onChange={handleChange} onBlur={handleBlur} />
            </div>
            <div>
                <label htmlFor="allowed_file_types">Allowed File Types (comma-separated)</label>
                <input id="allowed_file_types" name="allowed_file_types" value={displayValue} onChange={handleChange} onBlur={handleBlur} placeholder=".png, .jpg, .pdf" />
                <p className="text-xs text-gray-400 mt-1">Leave blank to allow any file type.</p>
            </div>
        </div>
    );
}

export default FileStorageNode;