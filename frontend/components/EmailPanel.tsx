"use client";

import React, { useState } from "react";
import { sendEmail } from "@/lib/api";
import type { EmailSet, GeneratedEmail } from "@/lib/types";

const EMAIL_TYPE_CONFIG: Record<string, { label: string; icon: string; color: string }> = {
  rfi: { label: "RFI Email", icon: "?", color: "text-yellow-400" },
  internal: { label: "Internal Alignment", icon: "!", color: "text-blue-400" },
  finance: { label: "Finance Summary", icon: "$", color: "text-green-400" },
};

interface EmailPanelProps {
  emailSet: EmailSet | null;
  onGenerate: () => void;
  analysisId: string;
}

export default function EmailPanel({ emailSet, onGenerate, analysisId }: EmailPanelProps) {
  const [editedEmails, setEditedEmails] = useState<Record<number, GeneratedEmail>>({});
  const [sentEmails, setSentEmails] = useState<Set<number>>(new Set());
  const [sending, setSending] = useState<number | null>(null);
  const [generating, setGenerating] = useState(false);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await onGenerate();
    } finally {
      setGenerating(false);
    }
  };

  const handleEdit = (index: number, field: keyof GeneratedEmail, value: string) => {
    const email = emailSet?.emails[index];
    if (!email) return;
    setEditedEmails((prev) => ({
      ...prev,
      [index]: { ...email, ...prev[index], [field]: value },
    }));
  };

  const handleSend = async (index: number) => {
    const email = editedEmails[index] || emailSet?.emails[index];
    if (!email) return;
    setSending(index);
    try {
      await sendEmail(email);
      setSentEmails((prev) => new Set(prev).add(index));
    } finally {
      setSending(null);
    }
  };

  if (!emailSet) {
    return (
      <div className="card text-center py-12">
        <div className="w-12 h-12 bg-gray-800 rounded-xl flex items-center justify-center mx-auto mb-3">
          <svg className="w-6 h-6 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <h3 className="text-gray-300 font-medium mb-1">Generate Stakeholder Emails</h3>
        <p className="text-gray-600 text-sm mb-4">Auto-draft RFI, internal alignment, and finance summary emails</p>
        <button onClick={handleGenerate} disabled={generating} className="btn-primary">
          {generating ? "Generating..." : "Generate Emails"}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {emailSet.emails.map((email, i) => {
        const edited = editedEmails[i] || email;
        const config = EMAIL_TYPE_CONFIG[email.type] || { label: email.type, icon: "@", color: "text-gray-400" };
        const isSent = sentEmails.has(i);

        return (
          <div key={i} className={`card ${isSent ? "border-green-800 bg-green-950/10" : ""}`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className={`w-7 h-7 rounded-lg bg-gray-800 flex items-center justify-center text-sm font-bold ${config.color}`}>
                  {config.icon}
                </span>
                <h3 className="text-sm font-semibold text-gray-200">{config.label}</h3>
              </div>
              {isSent ? (
                <span className="text-xs text-green-400 flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Sent successfully
                </span>
              ) : (
                <button
                  onClick={() => handleSend(i)}
                  disabled={sending === i}
                  className="btn-primary text-xs"
                >
                  {sending === i ? "Sending..." : "Send"}
                </button>
              )}
            </div>

            {/* To */}
            <div className="mb-2">
              <label className="text-[10px] text-gray-600 uppercase">To</label>
              <input
                className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
                value={edited.recipients}
                onChange={(e) => handleEdit(i, "recipients", e.target.value)}
              />
            </div>

            {/* Subject */}
            <div className="mb-2">
              <label className="text-[10px] text-gray-600 uppercase">Subject</label>
              <input
                className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-gray-300 font-medium focus:outline-none focus:ring-1 focus:ring-blue-500"
                value={edited.subject}
                onChange={(e) => handleEdit(i, "subject", e.target.value)}
              />
            </div>

            {/* Body */}
            <div>
              <label className="text-[10px] text-gray-600 uppercase">Body</label>
              <textarea
                className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-2 text-sm text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
                rows={8}
                value={edited.body}
                onChange={(e) => handleEdit(i, "body", e.target.value)}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
