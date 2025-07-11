import React, { useEffect } from 'react';
import { Handle, Position, useUpdateNodeInternals } from 'reactflow';
import BaseNode from './BaseNode';
import { ShareIcon, TrashIcon } from '@heroicons/react/24/outline';
import useWorkflowStore from '../../stores/workflowStore';

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

export const IntelligentRouterNodeInspector = ({ nodeId, nodeData }) => {
    const { updateNodeData, updateRouteName } = useWorkflowStore.getState();
    const currentRoutes = nodeData.routes || {};

    const handleRouteNameChange = (oldName, newName) => {
        const trimmedNewName = newName.trim();
        if (trimmedNewName && trimmedNewName !== oldName && !currentRoutes[trimmedNewName]) {
            updateRouteName(nodeId, oldName, trimmedNewName);
        }
    };

    const addRoute = () => {
        let i = 1;
        let newRouteName = `new_route_${i}`;
        while (currentRoutes[newRouteName]) { i++; newRouteName = `new_route_${i}`; }
        const updatedRoutes = { ...currentRoutes, [newRouteName]: 'END' };
        const currentVersion = nodeData._version || 0;
        updateNodeData(nodeId, { ...nodeData, routes: updatedRoutes, _version: currentVersion + 1 });
    };

    const removeRoute = (routeName) => {
        const updatedRoutes = { ...currentRoutes };
        delete updatedRoutes[routeName];
        const currentVersion = nodeData._version || 0;
        updateNodeData(nodeId, { ...nodeData, routes: updatedRoutes, _version: currentVersion + 1 });
    };

    return (
        <div className="space-y-4 p-4 bg-fuchsia-50 border border-fuchsia-300 rounded-lg">
            <h4 className="font-bold text-fuchsia-800">Routing Options</h4>
            <p className="text-xs text-gray-500 -mt-2">Define output paths. The LLM will choose one. The handle ID on the node must match the route name.</p>
            <div className="space-y-2">
                {Object.keys(currentRoutes).map(routeName => (
                    <div key={routeName} className="flex items-center gap-2">
                        <input type="text" defaultValue={routeName} onBlur={(e) => handleRouteNameChange(routeName, e.target.value)} placeholder="Route Name" className="flex-grow p-1 border border-gray-300 rounded-md" />
                        <button onClick={() => removeRoute(routeName)} className="p-1 text-red-500 hover:text-red-700"> <TrashIcon className="h-5 w-5" /> </button>
                    </div>
                ))}
            </div>
            <button onClick={addRoute} className="w-full text-sm bg-fuchsia-200 text-fuchsia-800 font-semibold py-1 px-3 rounded-md hover:bg-fuchsia-300 transition-colors">
                + Add Route
            </button>
        </div>
    );
}


export default IntelligentRouterNode;