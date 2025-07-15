import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { toast } from 'react-hot-toast';
import { TableCellsIcon, ChevronRightIcon, CpuChipIcon } from '@heroicons/react/24/outline';

const DataManager = () => {
    const [schema, setSchema] = useState({});
    const [sql, setSql] = useState('SELECT * FROM your_table_name LIMIT 10;');
    const [result, setResult] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [expandedTables, setExpandedTables] = useState({});

    const fetchSchema = useCallback(async () => {
        try {
            const response = await axios.get('/api/database/schema');
            setSchema(response.data);
        } catch (error) {
            toast.error('Failed to fetch database schema.');
            console.error(error);
        }
    }, []);

    useEffect(() => {
        fetchSchema();
    }, [fetchSchema]);

    const handleExecuteSql = async () => {
        if (!sql.trim()) {
            toast.error('SQL command cannot be empty.');
            return;
        }
        setIsLoading(true);
        setResult(null);
        try {
            const response = await axios.post('/api/database/execute', { sql });
            setResult(response.data);
            toast.success(response.data.message || 'Command executed successfully.');
            // Refresh schema if a table was created or dropped
            if (/CREATE|DROP|ALTER/i.test(sql)) {
                fetchSchema();
            }
        } catch (error) {
            const errorMessage = error.response?.data?.detail || 'An unknown error occurred.';
            setResult({ status: 'error', message: errorMessage });
            toast.error(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    const toggleTable = (tableName) => {
        setExpandedTables(prev => ({ ...prev, [tableName]: !prev[tableName] }));
    };

    const renderResults = () => {
        if (!result) return null;

        if (result.status === 'error') {
            return <div className="p-4 bg-red-50 text-red-700 rounded-md">Error: {result.message}</div>;
        }

        if (result.results && result.results.length > 0) {
            const headers = Object.keys(result.results[0]);
            return (
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                        <tr>
                            {headers.map(header => (
                                <th key={header} scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    {header}
                                </th>
                            ))}
                        </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                        {result.results.map((row, rowIndex) => (
                            <tr key={rowIndex}>
                                {headers.map(header => (
                                    <td key={`${rowIndex}-${header}`} className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                                        {String(row[header])}
                                    </td>
                                ))}
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>
            );
        }

        return <div className="p-4 bg-green-50 text-green-700 rounded-md">{result.message}</div>;
    };

    return (
        <div className="flex h-full bg-gray-100">
            {/* Sidebar */}
            <aside className="w-80 bg-white p-4 border-r border-gray-200 flex flex-col">
                <h2 className="text-xl font-bold text-gray-800 mb-4">Database Schema</h2>
                <div className="flex-grow overflow-y-auto">
                    {Object.keys(schema).length > 0 ? (
                        Object.entries(schema).map(([tableName, columns]) => (
                            <div key={tableName} className="mb-2">
                                <div onClick={() => toggleTable(tableName)} className="flex items-center justify-between p-2 rounded-md hover:bg-gray-100 cursor-pointer">
                                    <div className="flex items-center gap-2">
                                        <TableCellsIcon className="h-5 w-5 text-gray-500" />
                                        <span className="font-semibold text-gray-700">{tableName}</span>
                                    </div>
                                    <ChevronRightIcon className={`h-5 w-5 text-gray-400 transition-transform ${expandedTables[tableName] ? 'rotate-90' : ''}`} />
                                </div>
                                {expandedTables[tableName] && (
                                    <ul className="pl-6 mt-1 border-l-2 border-indigo-200">
                                        {columns.map(col => (
                                            <li key={col.name} className="text-sm text-gray-600 py-1 flex items-center gap-2">
                                                <span className="font-mono text-indigo-700">{col.name}</span>
                                                <span className="text-gray-400">({col.type})</span>
                                                {col.pk ? <span className="text-xs font-bold text-amber-600 bg-amber-100 px-1.5 py-0.5 rounded-full">PK</span> : null}
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        ))
                    ) : (
                        <p className="text-sm text-gray-500">No tables found in the database.</p>
                    )}
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 p-6 flex flex-col gap-6">
                <div className="flex items-center gap-3">
                    <CpuChipIcon className="h-8 w-8 text-indigo-600"/>
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800">Data Manager</h1>
                        <p className="text-gray-500">Directly query the application data database.</p>
                    </div>
                </div>

                <div className="flex-grow flex flex-col gap-4">
                    <div className="flex-shrink-0">
                        <label htmlFor="sql-editor" className="block text-sm font-medium text-gray-700 mb-1">
                            SQL Command Editor
                        </label>
                        <textarea
                            id="sql-editor"
                            value={sql}
                            onChange={(e) => setSql(e.target.value)}
                            className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm"
                            rows={8}
                        />
                    </div>
                    <div>
                        <button
                            onClick={handleExecuteSql}
                            disabled={isLoading}
                            className="bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-700 disabled:bg-indigo-300 transition-colors"
                        >
                            {isLoading ? 'Executing...' : 'Execute SQL'}
                        </button>
                    </div>
                    <div className="flex-grow bg-white border border-gray-200 rounded-lg p-1">
                        <h3 className="text-lg font-semibold text-gray-700 p-3">Results</h3>
                        {renderResults()}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default DataManager;