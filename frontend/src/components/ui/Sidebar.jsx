import React, { useState } from 'react';
import useWorkflowStore from '../../stores/workflowStore';
import { toast } from 'react-hot-toast';
import {
    Cog8ToothIcon,
    WrenchScrewdriverIcon,
    QuestionMarkCircleIcon,
    ChatBubbleLeftRightIcon,
    UserIcon,
    BeakerIcon,
    DocumentArrowUpIcon,
    CircleStackIcon,
    MagnifyingGlassIcon,
    ArrowsUpDownIcon,
    ArchiveBoxIcon,
    ServerStackIcon,
    ShareIcon,
    ArrowDownOnSquareStackIcon,
    BoltIcon,
    VariableIcon,
    ArrowPathIcon,
    ArrowUturnLeftIcon,
    ChatBubbleBottomCenterTextIcon,
} from '@heroicons/react/24/outline';
import AccordionItem from './AccordionItem';
import VariableExplorer from './VariableExplorer';
import axios from "axios";

const Sidebar = () => {
    const { workflowName, setWorkflowName, workflowDescription, setWorkflowDescription } = useWorkflowStore();
    const [openSection, setOpenSection] = useState('settings'); // 'settings' section is open by default

    const onDragStart = (event, nodeType) => {
        event.dataTransfer.setData('application/reactflow', nodeType);
        event.dataTransfer.effectAllowed = 'move';
    };

    // Handler to control which accordion section is open
    const handleToggle = (id) => {
        setOpenSection(prevOpenSection => (prevOpenSection === id ? null : id));
    };

    const nodeTypes = [
        { type: 'agentic_tool_use', label: 'Tool / Agent', icon: <WrenchScrewdriverIcon className="h-6 w-6 text-blue-700" /> },
        { type: 'direct_tool_call', label: 'Direct Tool Call', icon: <BoltIcon className="h-6 w-6 text-yellow-700" /> },
        { type: 'condition_check', label: 'Condition', icon: <QuestionMarkCircleIcon className="h-6 w-6 text-amber-700" /> },
        { type: 'human_input', label: 'Human Input', icon: <UserIcon className="h-6 w-6 text-green-700" /> },
        { type: 'llm_response', label: 'LLM Response', icon: <ChatBubbleLeftRightIcon className="h-6 w-6 text-cyan-700" /> },
        { type: 'workflow_call', label: 'Run Workflow', icon: <BeakerIcon className="h-6 w-6 text-purple-700" /> },
        { type: 'file_ingestion', label: 'File Ingestion', icon: <DocumentArrowUpIcon className="h-6 w-6 text-orange-700" /> },
        { type: 'file_storage', label: 'File Storage', icon: <ArchiveBoxIcon className="h-6 w-6 text-orange-700" /> },
        { type: 'vector_db_ingestion', label: 'Vector Ingestion', icon: <CircleStackIcon className="h-6 w-6 text-teal-700" /> },
        { type: 'vector_db_query', label: 'Vector Query', icon: <MagnifyingGlassIcon className="h-6 w-6 text-teal-700" /> },
        { type: 'database_save', label: 'Database Save', icon: <ArrowDownOnSquareStackIcon className="h-6 w-6 text-sky-700" /> },
        { type: 'database_query', label: 'Database Query', icon: <CircleStackIcon className="h-6 w-6 text-sky-700" /> },
        { type: 'cross_encoder_rerank', label: 'Rerank Results', icon: <ArrowsUpDownIcon className="h-6 w-6 text-teal-700" /> },
        { type: 'http_request', label: 'API Request', icon: <ServerStackIcon className="h-6 w-6 text-slate-700" /> },
        { type: 'intelligent_router', label: 'Intelligent Router', icon: <ShareIcon className="h-6 w-6 text-fuchsia-700" /> },
        { type: 'start_loop', label: 'Start Loop', icon: <ArrowPathIcon className="h-6 w-6 text-rose-700" /> },
        { type: 'end_loop', label: 'End Loop', icon: <ArrowUturnLeftIcon className="h-6 w-6 text-rose-700" /> },
        { type: 'display_message', label: 'Display Message', icon: <ChatBubbleBottomCenterTextIcon className="h-6 w-6 text-indigo-700" /> },
    ];

    const handleSaveWorkflow = async () => {
        const currentStoreState = useWorkflowStore.getState();
        if (!currentStoreState.workflowName) {
            toast.error("Please enter a name for the workflow.");
            return;
        }
        const workflowData = currentStoreState.getFlowAsJson();
        const toastId = toast.loading('Saving workflow...');

        try {
            const response = await axios.post('/api/workflows', workflowData);
            toast.success(`Workflow "${response.data.name}" saved successfully!`, { id: toastId });
        } catch (error) {
            const errorMsg = error.response?.data?.detail || error.message;
            toast.error(`Error saving: ${errorMsg}`, { id: toastId });
        }
    };

    return (
        <aside className="h-full w-full bg-gray-50 p-4 border-r border-gray-200 flex flex-col shadow-lg z-10">
            <div className="flex-grow overflow-y-auto -mx-3">
                <AccordionItem
                    id="settings"
                    title="Settings"
                    icon={<Cog8ToothIcon className="h-6 w-6 text-gray-700" />}
                    isOpen={openSection === 'settings'}
                    onToggle={handleToggle}
                >
                    <div className="space-y-3">
                        <input type="text" value={workflowName} onChange={(e) => setWorkflowName(e.target.value)} placeholder="Workflow Name" className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" />
                        <textarea value={workflowDescription} onChange={(e) => setWorkflowDescription(e.target.value)} placeholder="Workflow Description..." rows={3} className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500" />
                    </div>
                </AccordionItem>

                <AccordionItem
                    id="nodes"
                    title="Nodes"
                    icon={<WrenchScrewdriverIcon className="h-6 w-6 text-gray-700" />}
                    isOpen={openSection === 'nodes'}
                    onToggle={handleToggle}
                >
                    <p className="text-xs text-gray-500 mb-3">Drag nodes to the canvas to build your workflow.</p>
                    <div className="space-y-2">
                        {nodeTypes.map((node) => (
                            <div key={node.type} onDragStart={(event) => onDragStart(event, node.type)} draggable className="p-3 border-2 border-dashed border-gray-300 rounded-lg cursor-grab flex items-center gap-3 hover:bg-indigo-50 hover:border-indigo-400 transition-colors" >
                                {node.icon}
                                <span className="font-semibold text-gray-700">{node.label}</span>
                            </div>
                        ))}
                    </div>
                </AccordionItem>

                <AccordionItem
                    id="variables"
                    title="Variables"
                    icon={<VariableIcon className="h-6 w-6 text-gray-700" />}
                    isOpen={openSection === 'variables'}
                    onToggle={handleToggle}
                >
                    <VariableExplorer />
                </AccordionItem>
            </div>

            <div className="pt-4 border-t border-gray-200">
                <button onClick={handleSaveWorkflow} className="w-full bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors">
                    Save Workflow
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;