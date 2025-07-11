import React from 'react';
import BaseNode from './BaseNode';
import { ServerStackIcon } from '@heroicons/react/24/outline';

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
    const method = data.http_method || 'GET';

    return (
        <BaseNode data={data} selected={selected}>
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

export const HttpRequestNodeInspector = ({ nodeData, handleChange }) => {
    return (
        <div className="space-y-4 p-4 bg-slate-50 border border-slate-300 rounded-lg">
            <h4 className="font-bold text-slate-800">API Request Configuration</h4>
            <div>
                <label htmlFor="http_method">HTTP Method</label>
                <select id="http_method" name="http_method" value={nodeData.http_method || 'GET'} onChange={handleChange}>
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="PATCH">PATCH</option>
                    <option value="DELETE">DELETE</option>
                </select>
            </div>
            <div>
                <label htmlFor="url_template">Request URL</label>
                <input id="url_template" name="url_template" value={nodeData.url_template || ''} onChange={handleChange} placeholder="https://api.example.com/items/{input.item_id}" />
                <p className="text-xs text-gray-400 mt-1">You can use variables like {`{input.var_name}`}.</p>
            </div>
            <div>
                <label htmlFor="headers_template">Headers (JSON format)</label>
                <textarea id="headers_template" name="headers_template" rows={4} value={nodeData.headers_template || ''} onChange={handleChange} placeholder={`{\n  "Authorization": "Bearer {context.api_key}"\n}`} />
            </div>
            {['POST', 'PUT', 'PATCH'].includes(nodeData.http_method?.toUpperCase()) && (
                <div>
                    <label htmlFor="body_template">Body (JSON format)</label>
                    <textarea id="body_template" name="body_template" rows={5} value={nodeData.body_template || ''} onChange={handleChange} placeholder={`{\n  "name": "{input.user_name}",\n  "value": 123\n}`} />
                </div>
            )}
        </div>
    );
};


export default HttpRequestNode;