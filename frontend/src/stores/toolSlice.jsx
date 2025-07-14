import axios from 'axios';

export const createToolSlice = (set, get) => ({
    tools: [],
    fetchTools: async () => {
        if (get().tools.length > 0) return;
        try {
            const response = await axios.get('/api/tools');
            if (response.data) set({ tools: response.data });
        } catch (error) {
            console.error("Error fetching tools:", error);
            set({ tools: [] });
        }
    },
});