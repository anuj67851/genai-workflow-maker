import React from 'react';
import { ChevronRightIcon } from '@heroicons/react/24/solid';

const AccordionItem = ({ id, title, icon, isOpen, onToggle, children }) => {
    return (
        <div className="border-b border-gray-200">
            {/* Header / Button to toggle the section */}
            <button
                onClick={() => onToggle(id)}
                className="w-full flex items-center justify-between p-3 text-left text-gray-800 hover:bg-gray-100 focus:outline-none"
            >
                <div className="flex items-center gap-3">
                    {icon}
                    <span className="text-lg font-bold">{title}</span>
                </div>
                <ChevronRightIcon
                    className={`h-5 w-5 text-gray-500 transform transition-transform duration-200 ${
                        isOpen ? 'rotate-90' : ''
                    }`}
                />
            </button>

            {/* Collapsible content area */}
            <div
                className={`overflow-y-auto transition-all duration-300 ease-in-out ${
                    isOpen ? 'max-h-[600px]' : 'max-h-0'
                }`}
            >
                <div className="p-3">
                    {children}
                </div>
            </div>
        </div>
    );
};

export default AccordionItem;