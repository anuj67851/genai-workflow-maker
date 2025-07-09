import React from 'react';
import BaseNode from './BaseNode';
import { ServerStackIcon } from '@heroicons/react/24/outline';

const typeStyles = {
    http_request: { bg: 'bg-node-api', border: 'border-node-api', title: 'API Request' },
    default: { bg: 'bg-gray-200', border: 'border-gray-400', title: 'Node' },
};

const getMethodColor = (method) => {
    switch (method?.toUpperCase()) {
        case 'GET': return 'bg-green-200 text-green-800';
        case 'POST': return 'bg-blue-200 text-blue-800';
        case 'PUT':
        case 'PATCH': return 'bg-amber-200 text-amber-800';
        case 'DELETE': return 'bg-red-200 text-red-800';
        default: return 'bg-gray-200 text-gray-800';
    }
};

const HttpRequestNode = ({ data, selected }) => {
    const styledData = { ...data, action_type: 'http_request' };
    const method = data.http_method || 'GET';

    return (
        <BaseNode data={styledData} selected={selected} typeStyles={typeStyles}>
            <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                        <ServerStackIcon className="h-4 w-4 text-slate-600" />
                        <span className="font-semibold">Calling External API</span>
                    </div>
                    <span className={`px-2 py-0.5 rounded-full font-bold text-xs ${getMethodColor(method)}`}>
                        {method.toUpperCase()}
                    </span>
                </div>

                <div className="text-xs text-gray-700 font-mono bg-slate-50 p-2 rounded break-all border border-slate-200">
                    {data.url_template || 'No URL configured'}
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

export default HttpRequestNode;