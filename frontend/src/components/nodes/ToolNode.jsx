import React from 'react';
import BaseNode from './BaseNode';
import { WrenchScrewdriverIcon, CheckBadgeIcon, CircleStackIcon, InformationCircleIcon } from '@heroicons/react/24/outline';

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

export const ToolNodeInspector = ({ nodeData, handleChange, tools }) => {
    const selectedToolSchemas = tools.filter(tool => nodeData.tool_names?.includes(tool.name));

    return (
        <div className="space-y-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-bold text-blue-800">Tool / Agent Settings</h4>
            <div>
                <label>Tool Usage</label>
                <div className="space-y-3 rounded-md border border-gray-200 p-3 bg-white">
                    <div className="grid grid-cols-[auto_1fr] items-center gap-x-3">
                        <input type="radio" id="tool_auto" name="tool_selection" value="auto" checked={nodeData.tool_selection === 'auto'} onChange={handleChange} className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300" />
                        <label htmlFor="tool_auto" className="text-sm font-medium text-gray-700">Let agent decide from all available tools</label>
                    </div>
                    <div className="grid grid-cols-[auto_1fr] items-center gap-x-3">
                        <input type="radio" id="tool_manual" name="tool_selection" value="manual" checked={nodeData.tool_selection === 'manual'} onChange={handleChange} className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300" />
                        <label htmlFor="tool_manual" className="text-sm font-medium text-gray-700">Select specific tools for the agent</label>
                    </div>
                    <div className="grid grid-cols-[auto_1fr] items-center gap-x-3">
                        <input type="radio" id="tool_none" name="tool_selection" value="none" checked={nodeData.tool_selection === 'none'} onChange={handleChange} className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300" />
                        <label htmlFor="tool_none" className="text-sm font-medium text-gray-700">Do not use any tools (direct LLM response)</label>
                    </div>
                </div>

                {nodeData.tool_selection === 'manual' && (
                    <div className="mt-2 p-3 border border-gray-200 rounded-md bg-gray-50 max-h-48 overflow-y-auto space-y-2">
                        <p className="text-xs text-gray-500 mb-2">Select one or more tools for the agent to use:</p>
                        {tools.map(tool => (
                            <div key={tool.name} className="grid grid-cols-[auto_1fr] items-center gap-x-3">
                                <input type="checkbox" id={`tool-chk-${tool.name}`} name="tool_names_checkbox" value={tool.name} checked={nodeData.tool_names?.includes(tool.name) || false} onChange={handleChange} className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
                                <label htmlFor={`tool-chk-${tool.name}`} className="text-sm text-gray-900 font-mono">{tool.name}</label>
                            </div>
                        ))}
                    </div>
                )}

                {nodeData.tool_selection === 'manual' && selectedToolSchemas.length > 0 && (
                    <div className="mt-3 p-3 border border-blue-200 rounded-lg bg-blue-50 space-y-2">
                        <div className="flex items-center gap-2 text-blue-800"><InformationCircleIcon className="h-5 w-5"/><h4 className="text-sm font-bold">Tool Return Information</h4></div>
                        {selectedToolSchemas.map(tool => (
                            <div key={`info-${tool.name}`} className="text-xs">
                                <p className="font-bold font-mono text-blue-900">{tool.name}:</p>
                                <p className="text-blue-700 pl-2">{tool.returns?.description || "No return description provided."}</p>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}

export default ToolNode;