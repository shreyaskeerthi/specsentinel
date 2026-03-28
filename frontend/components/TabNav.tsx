"use client";

import React from "react";

interface Tab {
  id: string;
  label: string;
}

interface TabNavProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (id: string) => void;
  onGenerateEmails?: () => void;
}

export default function TabNav({ tabs, activeTab, onChange, onGenerateEmails }: TabNavProps) {
  return (
    <div className="flex items-center justify-between border-b border-gray-800">
      <div className="flex gap-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={`px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === tab.id
                ? "bg-gray-900 text-white border-b-2 border-blue-500"
                : "text-gray-500 hover:text-gray-300 hover:bg-gray-900/50"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {onGenerateEmails && (
        <button
          onClick={onGenerateEmails}
          className="btn-primary text-sm flex items-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          Generate Emails
        </button>
      )}
    </div>
  );
}
