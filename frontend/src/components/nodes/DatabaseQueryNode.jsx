import React from 'react';
import BaseNode from './BaseNode';
import { CircleStackIcon } from '@heroicons/react/24/outline';

const DatabaseQueryNode = ({ data, selected }) => {
    const truncate = (text, length = 40) => {
        if (!text) return '';
        if (text.length <= length) return text;
        return text.substring(0, length) + '...';
    };

    return (
        <BaseNode data={data} selected={selected}>
            <div className="space-y-2">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <CircleStackIcon className="h-4 w-4 text-sky-600" />
                    <span className="font-semibold">Querying Database</span>
                </div>

                <div className="text-xs text-gray-700 font-mono bg-slate-50 p-2 rounded break-all border border-slate-200">
                    {truncate(data.query_template) || 'No query configured'}
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

export const DatabaseQueryNodeInspector = ({ nodeData, handleChange }) => {
    return (
        <div className="space-y-4 p-4 bg-sky-50 border border-sky-200 rounded-lg">
            <h4 className="font-bold text-sky-800">Database Query Settings</h4>
            <div>
                <label htmlFor="query_template">SQL Query Template</label>
                <textarea
                    id="query_template"
                    name="query_template"
                    rows={6}
                    value={nodeData.query_template || ''}
                    onChange={handleChange}
                    className="font-mono text-sm"
                    placeholder="SELECT * FROM users WHERE email = '{input.user_email}';"
                />
                <p className="text-xs text-gray-400 mt-1">
                    You can use variables like {`{input.var_name}`} or {`{query}`}.
                </p>
            </div>
        </div>
    );
};

export default DatabaseQueryNode;