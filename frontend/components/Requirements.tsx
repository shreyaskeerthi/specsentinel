"use client";

import React, { useState } from "react";
import type { SpecExtraction } from "@/lib/types";

interface RequirementSection {
  key: keyof SpecExtraction;
  label: string;
  icon: string;
}

const SECTIONS: RequirementSection[] = [
  { key: "insurance_requirements", label: "Insurance", icon: "shield" },
  { key: "bonding_requirements", label: "Bonding", icon: "lock" },
  { key: "warranty_requirements", label: "Warranty", icon: "clock" },
  { key: "liquidated_damages", label: "Liquidated Damages", icon: "alert" },
  { key: "testing_requirements", label: "Testing & TAB", icon: "check" },
  { key: "commissioning_requirements", label: "Commissioning", icon: "zap" },
  { key: "submittals_summary", label: "Submittals", icon: "file" },
  { key: "closeout_requirements", label: "Closeout", icon: "archive" },
  { key: "schedule_requirements", label: "Schedule", icon: "calendar" },
  { key: "div22_requirements", label: "Div 22 — Plumbing", icon: "droplet" },
  { key: "div23_requirements", label: "Div 23 — HVAC", icon: "wind" },
  { key: "div26_requirements", label: "Div 26 — Electrical", icon: "bolt" },
];

export default function Requirements({ extraction }: { extraction: SpecExtraction }) {
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  const availableSections = SECTIONS.filter((s) => extraction[s.key]);

  return (
    <div className="space-y-2">
      {availableSections.length === 0 ? (
        <div className="card text-center py-8">
          <p className="text-gray-500">No requirements extracted from the document.</p>
        </div>
      ) : (
        availableSections.map((section) => {
          const content = extraction[section.key];
          const isExpanded = expandedSection === section.key;

          return (
            <div
              key={section.key}
              className="card cursor-pointer hover:border-gray-700 transition-colors"
              onClick={() => setExpandedSection(isExpanded ? null : section.key)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gray-800 rounded-lg flex items-center justify-center">
                    <span className="text-sm text-gray-400">{section.label.charAt(0)}</span>
                  </div>
                  <h4 className="text-sm font-semibold text-gray-200">{section.label}</h4>
                </div>
                <svg
                  className={`w-4 h-4 text-gray-600 transition-transform ${isExpanded ? "rotate-180" : ""}`}
                  fill="none" viewBox="0 0 24 24" stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>

              {isExpanded && content && (
                <div className="mt-3 pt-3 border-t border-gray-800">
                  <p className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">{content}</p>
                </div>
              )}
            </div>
          );
        })
      )}

      {/* Sections not found */}
      {SECTIONS.filter((s) => !extraction[s.key]).length > 0 && (
        <div className="mt-4">
          <p className="text-xs text-gray-600 mb-2">Not found in spec:</p>
          <div className="flex flex-wrap gap-1">
            {SECTIONS.filter((s) => !extraction[s.key]).map((s) => (
              <span key={s.key} className="text-[10px] px-2 py-0.5 rounded bg-gray-900 text-gray-600 border border-gray-800">
                {s.label}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
