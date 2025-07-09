import React, { useEffect } from 'react';
import { Handle, Position, useUpdateNodeInternals } from 'reactflow';
import BaseNode from './BaseNode';
import { ShareIcon } from '@heroicons/react/24/outline';

const IntelligentRouterNode = ({ id, data, selected }) => { // Destructure 'id' from props
    console.log(`Rendering IntelligentRouterNode ${id} with version ${data._version || 0}`);
    const routes = data.routes ? Object.keys(data.routes) : [];
    console.log(`Routes for node ${id}:`, routes);
    const handleStep = routes.length > 1 ? 1 / (routes.length + 1) : 0.5;

    // Get the updateNodeInternals function from ReactFlow
    const updateNodeInternals = useUpdateNodeInternals();

    // Use useEffect to update node internals when routes or version changes
    useEffect(() => {
        console.log(`Updating node internals for ${id} with version ${data._version || 0}`);
        // This tells ReactFlow to recalculate the node's internals, including handles
        updateNodeInternals(id);
    }, [id, routes, data._version, updateNodeInternals]);

    return (
        <BaseNode data={data} selected={selected}>
            <div className="space-y-2">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <ShareIcon className="h-4 w-4 text-fuchsia-600" />
                    <span className="font-semibold">Routing based on context...</span>
                </div>
                <div className="text-xs text-gray-500 pt-1 border-t border-gray-200">
                    <span className="font-semibold">Outputs:</span>
                    <span className="font-mono bg-gray-100 px-1 rounded ml-1">
                        {routes.length > 0 ? routes.join(', ') : 'None configured'}
                    </span>
                </div>
            </div>

            {/* Dynamically create a handle for each route name */}
            {routes.map((routeName, index) => (
                <Handle
                    // *** THE KEY FIX: Make the key stable and unique, including version for re-rendering ***
                    key={`${id}-${routeName}-${data._version || 0}`}
                    type="source"
                    position={Position.Bottom}
                    id={routeName} // The ID MUST match the route name for connections
                    style={{ left: `${(index + 1) * handleStep * 100}%` }}
                    className="!w-4 !h-4 !bg-fuchsia-500"
                />
            ))}
        </BaseNode>
    );
};

export default IntelligentRouterNode;
