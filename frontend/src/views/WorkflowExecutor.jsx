import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { ArrowPathIcon, PencilSquareIcon, TrashIcon, PaperAirplaneIcon, DocumentArrowUpIcon } from '@heroicons/react/24/solid';

const WorkflowExecutor = () => {
    const [workflows, setWorkflows] = useState([]);
    const [selectedWorkflow, setSelectedWorkflow] = useState(null);
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [executionState, setExecutionState] = useState({
        id: null,
        pauseType: 'text_input', // 'text_input' or 'file_upload'
        allowedFileTypes: [],
        maxFiles: 1,
    });
    const [filesToUpload, setFilesToUpload] = useState([]);
    const chatEndRef = useRef(null);
    const fileInputRef = useRef(null);
    const navigate = useNavigate();

    const fetchWorkflows = async () => {
        try {
            const response = await axios.get('/api/workflows');
            setWorkflows(response.data);
        } catch (error) {
            console.error("Failed to fetch workflows:", error);
        }
    };

    useEffect(() => { fetchWorkflows(); }, []);
    useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

    // --- API Interaction Logic ---
    const processApiResponse = (data) => {
        const responseText = data.response || data.error || "An unknown error occurred.";
        setMessages(prev => [...prev, { role: 'assistant', content: responseText }]);

        if (data.status === 'awaiting_input') {
            setExecutionState({
                id: data.execution_id,
                pauseType: data.pause_type === 'awaiting_file_upload' ? 'file_upload' : 'text_input',
                allowedFileTypes: data.allowed_file_types || [],
                maxFiles: data.max_files || 1,
            });
        } else {
            setExecutionState({ id: null, pauseType: 'text_input' });
        }
    };

    // --- Event Handlers ---
    const handleMessageSubmit = async (e) => {
        e.preventDefault();
        const form = e.target;
        const userInput = form.elements.userInput?.value;
        if (userInput && !userInput.trim()) return;

        if (userInput) {
            setMessages(prev => [...prev, { role: 'user', content: userInput }]);
        }
        setIsLoading(true);
        form.reset();

        try {
            let result;
            if (executionState.id) { // Resume existing execution with text
                result = await axios.post('/api/executions/resume', { execution_id: executionState.id, user_input: userInput });
            } else { // Start a new execution
                result = await axios.post('/api/executions/start_by_id', {
                    workflow_id: selectedWorkflow.id,
                    query: userInput,
                    context: { username: 'workflow_runner' } // Example context
                });
            }
            processApiResponse(result.data);
        } catch (error) {
            const errorMsg = error.response?.data?.error || error.message;
            setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${errorMsg}` }]);
            setExecutionState({ id: null, pauseType: 'text_input' });
        } finally {
            setIsLoading(false);
        }
    };

    const handleFileUploadSubmit = async () => {
        if (filesToUpload.length === 0) return;

        const formData = new FormData();
        formData.append('execution_id', executionState.id);
        filesToUpload.forEach(file => {
            formData.append('files', file);
        });

        setMessages(prev => [...prev, { role: 'user', content: `Uploading ${filesToUpload.length} file(s)...` }]);
        setIsLoading(true);
        setFilesToUpload([]);

        try {
            // NOTE: This assumes a new backend endpoint exists at /api/executions/resume_with_file
            const result = await axios.post('/api/executions/resume_with_file', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            processApiResponse(result.data);
        } catch (error) {
            const errorMsg = error.response?.data?.error || error.message;
            setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${errorMsg}` }]);
            setExecutionState({ id: null, pauseType: 'text_input' });
        } finally {
            setIsLoading(false);
        }
    }

    const handleFileSelection = (e) => {
        const selected = Array.from(e.target.files);
        if(selected.length > executionState.maxFiles) {
            alert(`You can only upload a maximum of ${executionState.maxFiles} file(s).`);
            return;
        }
        setFilesToUpload(selected);
    };

    const handleSelectWorkflow = (workflow) => {
        setSelectedWorkflow(workflow);
        setMessages([{ role: 'assistant', content: `Selected workflow: "${workflow.name}". Please state your initial request.` }]);
        setExecutionState({ id: null, pauseType: 'text_input' });
    };

    const handleReset = () => {
        setSelectedWorkflow(null);
        setMessages([]);
        setExecutionState({ id: null, pauseType: 'text_input' });
        setIsLoading(false);
        fetchWorkflows();
    };

    const handleDeleteWorkflow = async (workflowId, event) => {
        event.stopPropagation();
        if (window.confirm("Are you sure you want to permanently delete this workflow?")) {
            try {
                await axios.delete(`/api/workflows/${workflowId}`);
                if (selectedWorkflow?.id === workflowId) handleReset();
                else fetchWorkflows();
            } catch (error) {
                alert(`Error deleting workflow: ${error.response?.data?.detail || error.message}`);
            }
        }
    };

    // --- Render Functions ---
    const renderInputArea = () => {
        if (executionState.pauseType === 'file_upload') {
            return (
                <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2">
                        <input type="file" ref={fileInputRef} multiple={executionState.maxFiles > 1} accept={(executionState.allowedFileTypes || []).join(',')} onChange={handleFileSelection} className="flex-grow p-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500" disabled={isLoading} />
                        <button onClick={handleFileUploadSubmit} className="bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-indigo-300 transition-colors" disabled={isLoading || filesToUpload.length === 0} >
                            <DocumentArrowUpIcon className="h-5 w-5" />
                        </button>
                    </div>
                    {filesToUpload.length > 0 && <p className="text-xs text-gray-500">{filesToUpload.map(f => f.name).join(', ')}</p>}
                </div>
            );
        }

        return (
            <form onSubmit={handleMessageSubmit} className="flex gap-2">
                <input type="text" name="userInput" className="flex-grow p-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500" placeholder={executionState.id ? "Provide the requested information..." : "Type your initial request..."} disabled={isLoading} />
                <button type="submit" className="bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-indigo-300 transition-colors" disabled={isLoading}>
                    <PaperAirplaneIcon className="h-5 w-5"/>
                </button>
            </form>
        );
    };

    if (!selectedWorkflow) {
        // ... (Unchanged selection screen)
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
                                <button onClick={(e) => {e.stopPropagation(); navigate(`/builder/${wf.id}`)}} className="p-2 bg-gray-100 rounded-full text-gray-500 hover:bg-indigo-100 hover:text-indigo-600"><PencilSquareIcon className="h-5 w-5"/></button>
                                <button onClick={(e) => handleDeleteWorkflow(wf.id, e)} className="p-2 bg-gray-100 rounded-full text-gray-500 hover:bg-red-100 hover:text-red-600"><TrashIcon className="h-5 w-5"/></button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    // --- Main Chat View ---
    return (
        <div className="h-full flex flex-col max-w-3xl mx-auto bg-white border-x border-gray-200">
            <div className="p-4 border-b flex justify-between items-center">
                <div><h2 className="font-bold text-lg">{selectedWorkflow.name}</h2><p className="text-sm text-gray-500">Execution Mode</p></div>
                <button onClick={handleReset} className="flex items-center gap-2 bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-4 rounded-lg transition-colors">
                    <ArrowPathIcon className="h-5 w-5"/> Change Workflow
                </button>
            </div>
            <div className="flex-grow p-4 overflow-y-auto bg-gray-50">
                {messages.map((msg, index) => (
                    <div key={index} className={`flex my-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`p-3 rounded-lg max-w-lg whitespace-pre-wrap ${msg.role === 'user' ? 'bg-indigo-500 text-white' : 'bg-gray-200 text-gray-800'}`}>{msg.content}</div>
                    </div>
                ))}
                {isLoading && ( <div className="flex justify-start my-4"><div className="p-3 rounded-lg bg-gray-200 text-gray-800"><div className="flex items-center gap-2"><div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse"></div><div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse [animation-delay:0.2s]"></div><div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse [animation-delay:0.4s]"></div></div></div></div> )}
                <div ref={chatEndRef} />
            </div>
            <div className="p-4 border-t bg-white">
                {renderInputArea()}
            </div>
        </div>
    );
};

export default WorkflowExecutor;