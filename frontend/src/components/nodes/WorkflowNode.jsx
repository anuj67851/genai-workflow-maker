import React, { useState, useEffect } from 'react';
import axios from 'axios';
import BaseNode from './BaseNode';
import { BeakerIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const WorkflowNode = ({ data, selected }) => {
    const [workflows, setWorkflows] = useState([]);

    useEffect(() => {
        const fetchWorkflows = async () => {
            try {
                const response = await axios.get('/api/workflows');
                setWorkflows(response.data || []);
            } catch (error) {
                console.error("Failed to fetch workflows for node:", error);
            }
        };
        fetchWorkflows();
    }, []);

    // We now use parseInt() to ensure we are comparing numbers with numbers.
    const targetWorkflow = data.target_workflow_id
        ? workflows.find(wf => wf.id === parseInt(data.target_workflow_id, 10))
        : null;

    const workflowName = targetWorkflow ? targetWorkflow.name : "None Selected";

    return (
        <BaseNode data={data} selected={selected}>
            <div className="space-y-2">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <BeakerIcon className="h-4 w-4 text-purple-600" />
                    <span className="font-semibold">Executes Workflow:</span>
                </div>

                {data.target_workflow_id ? (
                    <p className="text-sm font-semibold text-purple-800 p-2 bg-purple-50 rounded-md break-words">
                        {workflowName}
                    </p>
                ) : (
                    <div className="flex items-center gap-2 p-2 bg-red-50 border border-red-200 rounded-md">
                        <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
                        <p className="text-xs font-bold text-red-700">Select a workflow in the inspector.</p>
                    </div>
                )}

                {data.output_key && (
                    <div className="text-xs text-gray-500 mt-1">
                        <span className="font-semibold">Saves to:</span>
                        <span className="font-mono bg-green-100 text-green-800 px-1 rounded ml-1">{data.output_key}</span>
                    </div>
                )}
            </div>
        </BaseNode>
    );
};

export const WorkflowNodeInspector = ({ nodeData, handleChange, availableWorkflows, currentWorkflowId }) => {
    return (
        <div className="space-y-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
            <h4 className="font-bold text-purple-800">Sub-Workflow Settings</h4>
            <div>
                <label htmlFor="target_workflow_id">Workflow to Execute</label>
                <select id="target_workflow_id" name="target_workflow_id" value={nodeData.target_workflow_id ?? ''} onChange={handleChange} >
                    <option value="">-- Select a Workflow --</option>
                    {availableWorkflows.filter(wf => wf.id.toString() !== (currentWorkflowId || '').toString()).map(wf => (
                        <option key={wf.id} value={wf.id}>{wf.name}</option>
                    ))}
                </select>
                <p className="text-xs text-gray-400 mt-1">Runs another workflow as a sub-step. The current workflow is excluded to prevent loops.</p>
            </div>
            <div>
                <label htmlFor="input_mappings">Input Context Mapping (JSON)</label>
                <textarea
                    id="input_mappings"
                    name="input_mappings"
                    rows={5}
                    value={nodeData.input_mappings || ''}
                    onChange={handleChange}
                    className="font-mono text-sm"
                    placeholder='{\n  "key_for_child": "{input.key_from_parent}",\n  "static_value": "hello"\n}'
                />
                <p className="text-xs text-gray-400 mt-1">
                    Map data from this workflow's state to the sub-workflow's context.
                    Use variables like <strong>{`{input.var_name}`}</strong> or <strong>{`{query}`}</strong>.
                </p>
            </div>
        </div>
    );
};


export default WorkflowNode;