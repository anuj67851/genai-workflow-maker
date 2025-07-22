import React from 'react';
import BaseNode from './BaseNode';
import { BoltIcon, ExclamationTriangleIcon, InformationCircleIcon, ArrowDownOnSquareIcon } from '@heroicons/react/24/outline';

const DirectToolCallNode = ({ data, selected }) => {
    const toolName = data.target_tool_name || "None Selected";

    return (
        <BaseNode data={data} selected={selected}>
            <div className="space-y-2">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <BoltIcon className="h-4 w-4 text-yellow-600" />
                    <span className="font-semibold">Executes Tool:</span>
                </div>

                {data.target_tool_name ? (
                    <p className="text-sm font-semibold text-yellow-800 p-2 bg-yellow-50 rounded-md break-words">
                        {toolName}
                    </p>
                ) : (
                    <div className="flex items-center gap-2 p-2 bg-red-50 border border-red-200 rounded-md">
                        <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
                        <p className="text-xs font-bold text-red-700">Select a tool in the inspector.</p>
                    </div>
                )}

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

export const DirectToolCallNodeInspector = ({ nodeData, handleChange, tools }) => {

    // Find the full schema for the selected tool to display its details
    const targetToolSchema = tools.find(tool => tool.name === nodeData.target_tool_name);
    const toolParameters = targetToolSchema?.parameters?.properties ?? {};
    const requiredParams = targetToolSchema?.parameters?.required ?? [];

    return (
        <div className="space-y-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h4 className="font-bold text-yellow-800">Direct Tool Call Settings</h4>

            {/* --- Tool Selection Dropdown --- */}
            <div>
                <label htmlFor="target_tool_name">Tool to Execute</label>
                <select id="target_tool_name" name="target_tool_name" value={nodeData.target_tool_name ?? ''} onChange={handleChange} >
                    <option value="">-- Select a Tool --</option>
                    {tools.map(tool => (
                        <option key={tool.name} value={tool.name}>{tool.name}</option>
                    ))}
                </select>
                <p className="text-xs text-gray-400 mt-1">Directly runs a specific tool without LLM intervention.</p>
            </div>

            {/* --- Dynamic Tool Information Display (if a tool is selected) --- */}
            {targetToolSchema && (
                <div className="space-y-3 p-3 border border-yellow-200 rounded-lg bg-white">
                    <div>
                        <h5 className="text-sm font-bold text-gray-700 flex items-center gap-2"><InformationCircleIcon className="h-5 w-5 text-gray-500"/>Description</h5>
                        <p className="text-xs text-gray-600 mt-1">{targetToolSchema.description}</p>
                    </div>
                    <div>
                        <h5 className="text-sm font-bold text-gray-700 flex items-center gap-2"><ArrowDownOnSquareIcon className="h-5 w-5 text-gray-500"/>Arguments</h5>
                        {Object.keys(toolParameters).length > 0 ? (
                            <ul className="space-y-1 mt-1 text-xs list-disc list-inside">
                                {Object.entries(toolParameters).map(([name, schema]) => (
                                    <li key={name}>
                                        <span className="font-mono text-yellow-900">{name}</span>
                                        <span className="text-gray-500"> ({schema.type})</span>
                                        {requiredParams.includes(name) && <span className="ml-1 text-red-600 font-bold">*required</span>}
                                        <p className="pl-4 text-gray-600 italic">{schema.description}</p>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p className="text-xs text-gray-500 mt-1">This tool takes no arguments.</p>
                        )}

                    </div>
                    <div>
                        <h5 className="text-sm font-bold text-gray-700">Returns</h5>
                        <p className="text-xs text-gray-600 mt-1">{targetToolSchema.returns?.description || 'No return description provided.'}</p>
                    </div>
                </div>
            )}

            {/* --- Arguments Mapping Input --- */}
            <div>
                <label htmlFor="data_template">Tool Arguments (JSON format)</label>
                <textarea
                    id="data_template"
                    name="data_template"
                    rows={6}
                    value={nodeData.data_template || ''}
                    onChange={handleChange}
                    className="font-mono text-sm"
                    placeholder={'{\n  "argument_name": "{input.variable_name}",\n  "another_arg": "static value"\n}'}
                />
                <p className="text-xs text-gray-400 mt-1">
                    Map tool arguments to workflow variables. Keys must match the argument names above.
                </p>
            </div>
        </div>
    );
};

export default DirectToolCallNode;