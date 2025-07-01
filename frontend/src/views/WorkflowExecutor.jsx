import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { ArrowPathIcon, PencilSquareIcon, TrashIcon } from '@heroicons/react/24/solid';

const WorkflowExecutor = () => {
    const [workflows, setWorkflows] = useState([]);
    const [selectedWorkflow, setSelectedWorkflow] = useState(null);
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [executionId, setExecutionId] = useState(null);
    const chatEndRef = useRef(null);
    const navigate = useNavigate();

    const fetchWorkflows = async () => {
        try {
            const response = await axios.get('/api/workflows');
            setWorkflows(response.data);
        } catch (error) {
            console.error("Failed to fetch workflows:", error);
            alert(`Could not load workflows: ${error.message}`);
        }
    };

    useEffect(() => { fetchWorkflows(); }, []);
    useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

    const handleMessageSubmit = async (e) => {
        e.preventDefault();
        const userInput = e.target.elements.userInput.value;
        if (!userInput.trim()) return;
        setMessages(prev => [...prev, { role: 'user', content: userInput }]);
        setIsLoading(true);
        e.target.reset();
        try {
            let result;
            if (executionId) {
                // If an execution is in progress, we resume it. This is correct.
                result = await axios.post('/api/executions/resume', { execution_id: executionId, user_input: userInput });
            } else {
                // If it's a new chat, we start the selected workflow by its ID.
                // This is the critical fix.
                result = await axios.post('/api/executions/start_by_id', {
                    workflow_id: selectedWorkflow.id,
                    query: userInput,
                    context: { username: 'j.doe' }
                });
            }
            const responseText = result.data.response || result.data.error || "An unknown error occurred.";
            setMessages(prev => [...prev, { role: 'assistant', content: responseText }]);
            if (result.data.status === 'awaiting_input') {
                setExecutionId(result.data.execution_id);
            } else {
                setExecutionId(null);
            }
        } catch (error) {
            const errorMsg = error.response?.data?.detail || error.response?.data?.error || error.message;
            setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${errorMsg}` }]);
            setExecutionId(null);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSelectWorkflow = (workflow) => {
        setSelectedWorkflow(workflow);
        setMessages([{ role: 'assistant', content: `Selected workflow: "${workflow.name}". Please state your initial request.` }]);
        setExecutionId(null);
    };

    const handleReset = () => {
        setSelectedWorkflow(null);
        setMessages([]);
        setExecutionId(null);
        setIsLoading(false);
        fetchWorkflows();
    };

    const handleEditWorkflow = (workflowId, event) => {
        event.stopPropagation();
        navigate(`/builder/${workflowId}`);
    };

    const handleDeleteWorkflow = async (workflowId, event) => {
        event.stopPropagation();
        if (window.confirm("Are you sure you want to permanently delete this workflow?")) {
            try {
                await axios.delete(`/api/workflows/${workflowId}`);
                setWorkflows(prev => prev.filter(wf => wf.id !== workflowId));
                alert("Workflow deleted successfully.");
                if (selectedWorkflow?.id === workflowId) {
                    handleReset();
                }
            } catch (error) {
                console.error("Failed to delete workflow:", error);
                alert(`Error: ${error.response?.data?.detail || error.message}`);
            }
        }
    };

    // The rest of the component (the JSX rendering) is unchanged as it was already correct.
    if (!selectedWorkflow) {
        return (
            <div className="p-8 max-w-4xl mx-auto">
                <h1 className="text-2xl font-bold text-gray-800">Select a Workflow</h1>
                <p className="text-gray-500 mt-1 mb-6">Choose a workflow to run, edit, or delete.</p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {workflows.map(wf => (
                        <div key={wf.id} onClick={() => handleSelectWorkflow(wf)} className="p-4 border rounded-lg hover:shadow-lg hover:border-indigo-500 cursor-pointer transition-all bg-white relative group">
                            <h2 className="font-bold text-indigo-700">{wf.name}</h2>
                            <p className="text-sm text-gray-600 mt-1">{wf.description}</p>
                            <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button onClick={(e) => handleEditWorkflow(wf.id, e)} className="p-2 bg-gray-100 rounded-full text-gray-500 hover:bg-indigo-100 hover:text-indigo-600">
                                    <PencilSquareIcon className="h-5 w-5"/>
                                </button>
                                <button onClick={(e) => handleDeleteWorkflow(wf.id, e)} className="p-2 bg-gray-100 rounded-full text-gray-500 hover:bg-red-100 hover:text-red-600">
                                    <TrashIcon className="h-5 w-5"/>
                                </button>
                            </div>
                        </div>
                    ))}
                    {workflows.length === 0 && <p className="text-gray-500">No workflows found. Go to the Builder to create one!</p>}
                </div>
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col max-w-3xl mx-auto bg-white border-x border-gray-200">
            <div className="p-4 border-b flex justify-between items-center">
                <div>
                    <h2 className="font-bold text-lg">{selectedWorkflow.name}</h2>
                    <p className="text-sm text-gray-500">Execution Mode</p>
                </div>
                <button onClick={handleReset} className="flex items-center gap-2 bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-4 rounded-lg transition-colors">
                    <ArrowPathIcon className="h-5 w-5"/>
                    Change Workflow
                </button>
            </div>
            <div className="flex-grow p-4 overflow-y-auto bg-gray-50">
                {messages.map((msg, index) => (
                    <div key={index} className={`flex my-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`p-3 rounded-lg max-w-lg whitespace-pre-wrap ${msg.role === 'user' ? 'bg-indigo-500 text-white' : 'bg-gray-200 text-gray-800'}`}>
                            {msg.content}
                        </div>
                    </div>
                ))}
                {isLoading && ( <div className="flex justify-start my-4"><div className="p-3 rounded-lg bg-gray-200 text-gray-800"><div className="flex items-center gap-2"><div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse"></div><div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse [animation-delay:0.2s]"></div><div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse [animation-delay:0.4s]"></div></div></div></div> )}
                <div ref={chatEndRef} />
            </div>
            <div className="p-4 border-t bg-white">
                <form onSubmit={handleMessageSubmit} className="flex gap-2">
                    <input type="text" name="userInput" className="flex-grow p-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500" placeholder={executionId ? "Provide the requested information..." : "Type your initial request..."} disabled={isLoading} />
                    <button type="submit" className="bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-indigo-300 transition-colors" disabled={isLoading}>Send</button>
                </form>
            </div>
        </div>
    );
};

export default WorkflowExecutor;