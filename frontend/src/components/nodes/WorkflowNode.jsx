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

    const targetWorkflow = workflows.find(wf => wf.id === data.target_workflow_id);
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

export default WorkflowNode;