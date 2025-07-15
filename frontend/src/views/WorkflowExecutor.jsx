import React, { useState, useRef } from 'react';
import { ArrowPathIcon, PencilSquareIcon, TrashIcon, PaperAirplaneIcon, DocumentArrowUpIcon } from '@heroicons/react/24/solid';
import { useWorkflowList } from '../hooks/useWorkflowList';
import { useWorkflowChat } from '../hooks/useWorkflowChat';
import { toast } from 'react-hot-toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const WorkflowExecutor = () => {
    const [selectedWorkflow, setSelectedWorkflow] = useState(null);
    const { workflows, fetchWorkflows, deleteWorkflow, editWorkflow } = useWorkflowList();
    const {
        messages, isLoading, executionState, filesToUpload,
        setFilesToUpload, submitTextInput, submitFiles, chatEndRef, textInputRef
    } = useWorkflowChat(selectedWorkflow);

    const fileInputRef = useRef(null);

    const handleReset = () => {
        setSelectedWorkflow(null);
        fetchWorkflows(); // Refresh the list in case of changes
    };

    const handleDelete = (workflowId, event) => {
        event.stopPropagation();
        const onDeletion = () => {
            if (selectedWorkflow?.id === workflowId) {
                handleReset();
            }
        };
        deleteWorkflow(workflowId, onDeletion);
    };

    const handleMessageSubmit = (e) => {
        e.preventDefault();
        const form = e.target;
        const userInput = form.elements.userInput?.value;
        submitTextInput(userInput);
        form.reset();
    };

    const handleFileSelection = (e) => {
        const selected = Array.from(e.target.files);
        if(selected.length > executionState.maxFiles) {
            toast.error(`You can only upload a maximum of ${executionState.maxFiles} file(s).`);
            return;
        }
        setFilesToUpload(selected);
    };

    // --- Render Functions ---
    const renderInputArea = () => {
        if (executionState.pauseType === 'file_upload') {
            return (
                <div className="flex flex-col gap-2">
                    <div className="flex items-center gap-2">
                        <input type="file" ref={fileInputRef} multiple={executionState.maxFiles > 1} accept={(executionState.allowedFileTypes || []).join(',')} onChange={handleFileSelection} className="flex-grow p-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500" disabled={isLoading} />
                        <button onClick={submitFiles} className="bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-indigo-300 transition-colors" disabled={isLoading || filesToUpload.length === 0} >
                            <DocumentArrowUpIcon className="h-5 w-5" />
                        </button>
                    </div>
                    {filesToUpload.length > 0 && <p className="text-xs text-gray-500">{filesToUpload.map(f => f.name).join(', ')}</p>}
                </div>
            );
        }

        return (
            <form onSubmit={handleMessageSubmit} className="flex gap-2">
                <input type="text" name="userInput" ref={textInputRef} className="flex-grow p-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500" placeholder={executionState.id ? "Provide the requested information..." : "Type your initial request..."} disabled={isLoading} />
                <button type="submit" className="bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-indigo-300 transition-colors" disabled={isLoading}>
                    <PaperAirplaneIcon className="h-5 w-5"/>
                </button>
            </form>
        );
    };

    if (!selectedWorkflow) {
        return (
            <div className="p-8 max-w-4xl mx-auto">
                <h1 className="text-2xl font-bold text-gray-800">Select a Workflow</h1>
                <p className="text-gray-500 mt-1 mb-6">Choose a workflow to run, edit, or delete.</p>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {workflows.map(wf => (
                        <div key={wf.id} onClick={() => setSelectedWorkflow(wf)} className="p-4 border rounded-lg hover:shadow-lg hover:border-indigo-500 cursor-pointer transition-all bg-white relative group">
                            <h2 className="font-bold text-indigo-700">{wf.name}</h2>
                            <p className="text-sm text-gray-600 mt-1">{wf.description}</p>
                            <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button onClick={(e) => {e.stopPropagation(); editWorkflow(wf.id)}} className="p-2 bg-gray-100 rounded-full text-gray-500 hover:bg-indigo-100 hover:text-indigo-600"><PencilSquareIcon className="h-5 w-5"/></button>
                                <button onClick={(e) => handleDelete(wf.id, e)} className="p-2 bg-gray-100 rounded-full text-gray-500 hover:bg-red-100 hover:text-red-600"><TrashIcon className="h-5 w-5"/></button>
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
                        <div className={`p-3 rounded-lg max-w-lg ${msg.role === 'user' ? 'bg-indigo-500' : 'bg-gray-200'}`}>
                            <div className={`prose prose-sm max-w-none font-sans [&_p]:font-medium ${msg.role === 'user' ? 'prose-invert' : ''}`}>
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                    {msg.content}
                                </ReactMarkdown>
                            </div>
                        </div>
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