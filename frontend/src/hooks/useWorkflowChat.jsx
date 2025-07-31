import { useState, useEffect, useRef } from 'react';
import axios from 'axios';

export const useWorkflowChat = (selectedWorkflow) => {
    const [messages, setMessages] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [executionState, setExecutionState] = useState({
        id: null,
        pauseType: 'text_input',
        allowedFileTypes: [],
        maxFiles: 1,
    });
    const [filesToUpload, setFilesToUpload] = useState([]);

    const chatEndRef = useRef(null);
    const textInputRef = useRef(null);

    // Effect to scroll to the bottom of the chat
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Effect to focus the correct input
    useEffect(() => {
        if (!isLoading && executionState.pauseType === 'text_input' && textInputRef.current) {
            textInputRef.current.focus();
        }
    }, [isLoading, messages, executionState.pauseType]);

    // Initialize messages when a workflow is selected
    useEffect(() => {
        if (selectedWorkflow) {
            setMessages([{ role: 'assistant', content: `Selected workflow: "${selectedWorkflow.name}". Please state your initial request.` }]);
            setExecutionState({ id: null, pauseType: 'text_input' });
            setIsLoading(false);
        }
    }, [selectedWorkflow]);

    const processApiResponse = (data) => {
        // Create a buffer for all new messages to be added in this turn.
        const newMessages = [];

        // 1. Check for and add any 'display_message' outputs from the history.
        // This only runs on a completed or failed workflow that returns the full state.
        if (data.state?.step_history) {
            const displayMessages = data.state.step_history
                .filter(step => (step.type === 'display_message' || step.type === 'llm_response') && step.output)
                .map(step => ({ role: 'assistant', content: `${step.output}` })); // Render message in italics

            if(displayMessages.length > 0) {
                newMessages.push(...displayMessages);
            }
        }

        // 2. Add the main response or error message.
        let responseText = data.response || data.error || "An unknown error occurred.";
        if (typeof responseText === 'object') {
            responseText = "```json\n" + JSON.stringify(responseText, null, 2) + "\n```";
        }
        newMessages.push({ role: 'assistant', content: responseText });

        // 3. Update the state with all new messages at once.
        setMessages(prev => [...prev, ...newMessages]);


        // This part remains the same: handle the pause/resume state.
        if (data.status === 'awaiting_input') {
            setExecutionState({
                id: data.execution_id,
                pauseType: data.pause_type === 'awaiting_file_upload' ? 'file_upload' : 'text_input',
                allowedFileTypes: data.allowed_file_types || [],
                maxFiles: data.max_files || 1,
            });
        } else {
            // Workflow is completed or failed, so reset.
            setExecutionState({ id: null, pauseType: 'text_input', allowedFileTypes: [], maxFiles: 1 });
        }
    };

    const submitTextInput = async (userInput) => {
        if (!userInput || !userInput.trim()) return;

        setMessages(prev => [...prev, { role: 'user', content: userInput }]);
        setIsLoading(true);

        try {
            let result;
            if (executionState.id) { // Resume existing execution
                result = await axios.post('/api/executions/resume', { execution_id: executionState.id, user_input: userInput });
            } else { // Start a new execution
                result = await axios.post('/api/executions/start_by_id', {
                    workflow_id: selectedWorkflow.id,
                    query: userInput,
                    context: { username: 'workflow_runner' }
                });
            }
            processApiResponse(result.data);
        } catch (error) {
            const errorMsg = error.response?.data?.detail || error.response?.data?.error || error.message;
            setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${errorMsg}` }]);
            setExecutionState({ id: null, pauseType: 'text_input' });
        } finally {
            setIsLoading(false);
        }
    };

    const submitFiles = async () => {
        if (filesToUpload.length === 0 || !executionState.id) return;

        const formData = new FormData();
        formData.append('execution_id', executionState.id);
        filesToUpload.forEach(file => formData.append('files', file));

        setMessages(prev => [...prev, { role: 'user', content: `Uploading ${filesToUpload.length} file(s)...` }]);
        setIsLoading(true);
        setFilesToUpload([]);

        try {
            const result = await axios.post('/api/executions/resume_with_file', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            processApiResponse(result.data);
        } catch (error) {
            const errorMsg = error.response?.data?.detail || error.response?.data?.error || error.message;
            setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${errorMsg}` }]);
            setExecutionState({ id: null, pauseType: 'text_input' });
        } finally {
            setIsLoading(false);
        }
    };

    return {
        messages,
        isLoading,
        executionState,
        filesToUpload,
        setFilesToUpload,
        submitTextInput,
        submitFiles,
        chatEndRef,
        textInputRef
    };
};