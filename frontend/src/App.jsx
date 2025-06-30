import React from 'react';
import { Routes, Route, NavLink } from 'react-router-dom';
import { PlayCircleIcon, PlusCircleIcon, Cog8ToothIcon } from '@heroicons/react/24/outline';

import WorkflowBuilder from './views/WorkflowBuilder';
import WorkflowExecutor from './views/WorkflowExecutor';

function App() {
    const activeLinkClass = "bg-indigo-700 text-white";
    const inactiveLinkClass = "text-indigo-100 hover:bg-indigo-700 hover:text-white";

    return (
        <div className="flex flex-col h-screen bg-white">
            <header className="bg-indigo-600 text-white shadow-md z-20">
                <nav className="container mx-auto px-6 py-3">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center">
                            <Cog8ToothIcon className="h-8 w-8 mr-2" />
                            <h1 className="text-xl font-bold">GenAI Visual Workflows</h1>
                        </div>
                        <div className="flex items-center space-x-2">
                            <NavLink to="/" end className={({ isActive }) => `${isActive ? activeLinkClass : inactiveLinkClass} px-3 py-2 rounded-md text-sm font-medium flex items-center`}>
                                <PlusCircleIcon className="h-5 w-5 mr-2" />
                                Builder
                            </NavLink>
                            <NavLink to="/run" className={({ isActive }) => `${isActive ? activeLinkClass : inactiveLinkClass} px-3 py-2 rounded-md text-sm font-medium flex items-center`}>
                                <PlayCircleIcon className="h-5 w-5 mr-2" />
                                Run Workflows
                            </NavLink>
                        </div>
                    </div>
                </nav>
            </header>
            <main className="flex-grow overflow-hidden">
                <Routes>
                    {/* Updated Routes */}
                    <Route path="/" element={<WorkflowBuilder />} />
                    <Route path="/builder/:workflowId" element={<WorkflowBuilder />} />
                    <Route path="/run" element={<WorkflowExecutor />} />
                </Routes>
            </main>
        </div>
    );
}

export default App;