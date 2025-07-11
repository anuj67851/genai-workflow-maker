import React from 'react';
import BaseNode from './BaseNode';
import { ArrowsUpDownIcon } from '@heroicons/react/24/outline';

const CrossEncoderRerankNode = ({ data, selected }) => {

    return (
        <BaseNode data={data} selected={selected}>
            <div className="space-y-2">
                <div className="flex items-center gap-1 text-xs text-gray-500">
                    <ArrowsUpDownIcon className="h-4 w-4 text-teal-600" />
                    <span className="font-semibold">Re-Ranking Documents</span>
                </div>

                <div className="text-xs text-gray-500">
                    <span className="font-semibold">Returns Top-N:</span>
                    <span className="font-mono bg-gray-100 px-1 rounded ml-1">{data.rerank_top_n || 3}</span>
                </div>

                {data.output_key ? (
                    <div className="text-xs text-gray-500 pt-1 border-t border-gray-200">
                        <span className="font-semibold">Saves to:</span>
                        <span className="font-mono bg-green-100 text-green-800 px-1 rounded ml-1">
                            {data.output_key}
                        </span>
                    </div>
                ) : (
                    <div className="text-xs text-red-500 pt-1 border-t border-gray-200">
                        <span className="font-semibold">Warning:</span>
                        <span> Output key not set.</span>
                    </div>
                )}
            </div>
        </BaseNode>
    );
};

export const CrossEncoderRerankNodeInspector = ({ nodeData, handleChange, handleBlur }) => {
    return (
        <div className="space-y-4 p-4 bg-teal-50 border border-teal-200 rounded-lg">
            <h4 className="font-bold text-teal-800">Re-Ranker Settings</h4>
            <div>
                <label htmlFor="rerank_top_n">Return Top-N</label>
                <input id="rerank_top_n" name="rerank_top_n" type="number" min="1" value={nodeData.rerank_top_n ?? 3} onChange={handleChange} onBlur={handleBlur} />
                <p className="text-xs text-gray-400 mt-1">The final number of documents to return after re-ranking.</p>
            </div>
        </div>
    );
};

export default CrossEncoderRerankNode;