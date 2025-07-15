import React from 'react';
import BaseNode from './BaseNode';
import { ArrowDownOnSquareStackIcon } from '@heroicons/react/24/outline';

const DatabaseSaveNode = ({ data, selected }) => {
    const pk_string = Array.isArray(data.primary_key_columns)
        ? data.primary_key_columns.join(', ')
        : data.primary_key_columns || 'Not Set';

    return (
        <BaseNode data={data} selected={selected}>
            <div className="space-y-2">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <ArrowDownOnSquareStackIcon className="h-4 w-4 text-sky-600" />
                    <span className="font-semibold">Saving to Database</span>
                </div>

                <div className="text-xs text-gray-500">
                    <span className="font-semibold">Table:</span>
                    <span className="font-mono bg-gray-100 px-1 rounded ml-1">
                        {data.table_name || 'Not Set'}
                    </span>
                </div>

                <div className="text-xs text-gray-500">
                    <span className="font-semibold">PKs:</span>
                    <span className="font-mono bg-gray-100 px-1 rounded ml-1">
                        {pk_string}
                    </span>
                </div>

                {data.output_key ? (
                    <div className="text-xs text-gray-500 pt-2 border-t border-gray-200">
                        <span className="font-semibold">Saves to:</span>
                        <span className="font-mono bg-green-100 text-green-800 px-1 rounded ml-1">
                            {data.output_key}
                        </span>
                    </div>
                ) : (
                    <div className="text-xs text-red-500 pt-2 border-t border-gray-200">
                        <span className="font-semibold">Warning:</span>
                        <span> Output key not set.</span>
                    </div>
                )}
            </div>
        </BaseNode>
    );
};

export const DatabaseSaveNodeInspector = ({ nodeData, handleChange, handleBlur }) => {
    // It now correctly handles an array, a string, or a null/undefined value for display.
    const displayValue = (Array.isArray(nodeData.primary_key_columns)
        ? nodeData.primary_key_columns.join(', ')
        : nodeData.primary_key_columns) || '';

    return (
        <div className="space-y-4 p-4 bg-sky-50 border border-sky-200 rounded-lg">
            <h4 className="font-bold text-sky-800">Database Save Settings</h4>
            <div>
                <label htmlFor="table_name">Table Name</label>
                <input
                    id="table_name"
                    name="table_name"
                    value={nodeData.table_name || ''}
                    onChange={handleChange}
                    placeholder="e.g., users, tickets"
                />
            </div>
            <div>
                <label htmlFor="primary_key_columns">Primary Key Columns (comma-separated)</label>
                <input
                    id="primary_key_columns"
                    name="primary_key_columns"
                    value={displayValue}
                    onChange={handleChange}
                    onBlur={handleBlur} // Use onBlur to format to array
                    placeholder="e.g., id, user_email"
                />
                <p className="text-xs text-gray-400 mt-1">Columns that uniquely identify a row for updating.</p>
            </div>
            <div>
                <label htmlFor="data_template">Data to Save (JSON format)</label>
                <textarea
                    id="data_template"
                    name="data_template"
                    rows={6}
                    value={nodeData.data_template || ''}
                    onChange={handleChange}
                    className="font-mono text-sm"
                    placeholder={'{\n  "email": "{input.user_email}",\n  "status": "processed"\n}'}
                />
                <p className="text-xs text-gray-400 mt-1">
                    Map columns to workflow variables.
                </p>
            </div>
        </div>
    );
};


export default DatabaseSaveNode;