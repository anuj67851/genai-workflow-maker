import React from 'react';
import BaseNode from './BaseNode';
import { CircleStackIcon } from '@heroicons/react/24/outline';

const VectorDBIngestionNode = ({ data, selected }) => {
    return (
        <BaseNode data={data} selected={selected}>
            <div className="space-y-2">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <CircleStackIcon className="h-4 w-4 text-teal-600" />
                    <span className="font-semibold">Ingesting to Collection</span>
                </div>

                <div className="text-xs text-gray-500">
                    <span className="font-semibold">Collection:</span>
                    <span className="font-mono bg-gray-100 px-1 rounded ml-1">
                        {data.collection_name || 'Not Set'}
                    </span>
                </div>

                <div className="flex justify-between text-xs text-gray-500">
                    <div>
                        <span className="font-semibold">Chunk Size:</span>
                        <span className="font-mono bg-gray-100 px-1 rounded ml-1">{data.chunk_size || 1000}</span>
                    </div>
                    <div>
                        <span className="font-semibold">Overlap:</span>
                        <span className="font-mono bg-gray-100 px-1 rounded ml-1">{data.chunk_overlap || 200}</span>
                    </div>
                </div>

                {data.output_key && (
                    <div className="text-xs text-gray-500 pt-1 border-t border-gray-200">
                        <span className="font-semibold">Saves to:</span>
                        <span className="font-mono bg-green-100 text-green-800 px-1 rounded ml-1">
                            {data.output_key}
                        </span>
                    </div>
                )}
            </div>
        </BaseNode>
    );
};

export const VectorDBIngestionNodeInspector = ({ nodeData, handleChange }) => {
    return (
        <div className="space-y-4 p-4 bg-teal-50 border border-teal-200 rounded-lg">
            <h4 className="font-bold text-teal-800">Vector Ingestion Settings</h4>
            <div>
                <label htmlFor="collection_name">Collection Name</label>
                <input id="collection_name" name="collection_name" value={nodeData.collection_name || ''} onChange={handleChange} placeholder="e.g., project_docs_v1"/>
            </div>
            <div>
                <label htmlFor="embedding_model">Embedding Model</label>
                <input id="embedding_model" name="embedding_model" value={nodeData.embedding_model || ''} onChange={handleChange} placeholder="text-embedding-3-small"/>
            </div>
            <div>
                <label htmlFor="chunk_size">Chunk Size</label>
                <input id="chunk_size" name="chunk_size" type="number" min="1" value={nodeData.chunk_size ?? 1000} onChange={handleChange} />
            </div>
            <div>
                <label htmlFor="chunk_overlap">Chunk Overlap</label>
                <input id="chunk_overlap" name="chunk_overlap" type="number" min="0" value={nodeData.chunk_overlap ?? 200} onChange={handleChange} />
            </div>
        </div>
    );
};

export default VectorDBIngestionNode;