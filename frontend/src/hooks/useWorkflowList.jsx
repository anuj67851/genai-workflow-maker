import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';

export const useWorkflowList = () => {
    const [workflows, setWorkflows] = useState([]);
    const navigate = useNavigate();

    const fetchWorkflows = useCallback(async () => {
        try {
            const response = await axios.get('/api/workflows');
            setWorkflows(response.data);
        } catch (error) {
            console.error("Failed to fetch workflows:", error);
            toast.error("Could not fetch the list of workflows.");
        }
    }, []);

    const deleteWorkflow = useCallback(async (workflowId, onDeletionCallback) => {
        if (window.confirm("Are you sure you want to permanently delete this workflow?")) {
            try {
                await axios.delete(`/api/workflows/${workflowId}`);
                toast.success("Workflow deleted successfully.");
                if (onDeletionCallback) {
                    onDeletionCallback();
                }
                fetchWorkflows(); // Refresh the list after deletion
            } catch (error) {
                toast.error(`Error deleting workflow: ${error.response?.data?.detail || error.message}`);
            }
        }
    }, [fetchWorkflows]);

    const editWorkflow = useCallback((workflowId) => {
        navigate(`/builder/${workflowId}`);
    }, [navigate]);

    useEffect(() => {
        fetchWorkflows();
    }, [fetchWorkflows]);

    return { workflows, fetchWorkflows, deleteWorkflow, editWorkflow };
};