import React from 'react';
import { Handle, Position } from 'reactflow';
import BaseNode from './BaseNode';
import { ShareIcon } from '@heroicons/react/24/outline';

const IntelligentRouterNode = ({ data, selected }) => {
    // The keys of the routes dictionary are the names of our output handles
    const routes = data.routes ? Object.keys(data.routes) : [];

    // This calculation ensures handles are evenly spaced, even for 1 handle
    const handleStep = routes.length > 1 ? 1 / (routes.length + 1) : 0.5;

    return (
        // We pass the raw data to BaseNode. BaseNode will handle the styling.
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
                    key={routeName}
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