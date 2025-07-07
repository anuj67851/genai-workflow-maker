import React from 'react';
import BaseNode from './BaseNode';
import { ArrowsUpDownIcon } from '@heroicons/react/24/outline';

// Override typeStyles for this specific node type
const typeStyles = {
    cross_encoder_rerank: { bg: 'bg-node-vector', border: 'border-node-vector', title: 'Re-Rank Results' },
};

const CrossEncoderRerankNode = ({ data, selected }) => {
    // Manually set action_type for BaseNode styling
    const styledData = { ...data, action_type: 'cross_encoder_rerank' };

    return (
        <BaseNode data={styledData} selected={selected} typeStyles={typeStyles}>
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

export default CrossEncoderRerankNode;