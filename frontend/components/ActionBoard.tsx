"use client";

import React from "react";
import type { ActionBoard, ActionTask, MeetingTaskUpdate } from "@/lib/types";

const PRIORITY_STYLES = {
  high: "border-l-red-500 bg-red-950/10",
  medium: "border-l-yellow-500 bg-yellow-950/10",
  low: "border-l-green-500 bg-green-950/10",
};

const OWNER_COLORS: Record<string, string> = {
  Estimating: "bg-blue-900/40 text-blue-400",
  PM: "bg-purple-900/40 text-purple-400",
  Finance: "bg-green-900/40 text-green-400",
  Ops: "bg-orange-900/40 text-orange-400",
};

function TaskCard({ task }: { task: ActionTask }) {
  return (
    <div className={`rounded-lg border-l-4 ${PRIORITY_STYLES[task.priority] || PRIORITY_STYLES.medium} bg-gray-900 border border-gray-800 p-3`}>
      <div className="flex items-start justify-between gap-2">
        <h4 className="text-sm font-medium text-gray-200">{task.title}</h4>
        <div className="flex items-center gap-1 shrink-0">
          <span className={`text-[10px] px-1.5 py-0.5 rounded ${OWNER_COLORS[task.owner_type] || "bg-gray-800 text-gray-400"}`}>
            {task.owner_type}
          </span>
        </div>
      </div>
      <p className="text-xs text-gray-400 mt-1">{task.description}</p>
      <div className="flex items-center gap-2 mt-2 flex-wrap">
        {task.due_date && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-900/30 text-blue-400 font-mono">
            {task.due_date}
          </span>
        )}
        {task.assignee && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-700 text-gray-300">
            {task.assignee}
          </span>
        )}
        {task.linked_risk_id && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-900/30 text-red-400">
            {task.linked_risk_id}
          </span>
        )}
        {task.page_reference && (
          <span className="text-[10px] text-gray-600">p.{task.page_reference}</span>
        )}
        <span className={`text-[10px] px-1.5 py-0.5 rounded ${
          task.priority === "high" ? "bg-red-900/30 text-red-400" :
          task.priority === "medium" ? "bg-yellow-900/30 text-yellow-400" :
          "bg-green-900/30 text-green-400"
        }`}>
          {task.priority}
        </span>
      </div>
    </div>
  );
}

interface ActionBoardViewProps {
  actionBoard: ActionBoard | null;
  meetingTasks?: MeetingTaskUpdate[];
}

export default function ActionBoardView({ actionBoard, meetingTasks }: ActionBoardViewProps) {
  const columns = [
    {
      id: "to_clarify",
      title: "To Clarify (RFI)",
      color: "text-yellow-400",
      borderColor: "border-yellow-800",
      tasks: actionBoard?.to_clarify || [],
    },
    {
      id: "must_include",
      title: "Must Include in Bid",
      color: "text-blue-400",
      borderColor: "border-blue-800",
      tasks: actionBoard?.must_include || [],
    },
    {
      id: "internal",
      title: "Internal Tasks",
      color: "text-purple-400",
      borderColor: "border-purple-800",
      tasks: actionBoard?.internal || [],
    },
  ];

  // Add meeting tasks to appropriate columns
  if (meetingTasks && meetingTasks.length > 0) {
    for (const mt of meetingTasks) {
      const task: ActionTask = {
        id: `MT-${Math.random().toString(36).slice(2, 6)}`,
        title: mt.title,
        description: mt.description,
        priority: mt.priority,
        category: mt.category,
        owner_type: mt.owner_type,
        linked_risk_id: null,
        page_reference: null,
        due_date: mt.due_date || null,
        assignee: mt.assignee || null,
        status: "open",
      };
      const col = columns.find((c) => c.id === mt.category);
      if (col) col.tasks.push(task);
    }
  }

  const isEmpty = columns.every((c) => c.tasks.length === 0);

  if (isEmpty) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-500">No action items generated yet.</p>
        <p className="text-gray-600 text-sm mt-1">Upload a spec to generate the action board.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {columns.map((col) => (
        <div key={col.id}>
          <div className={`flex items-center gap-2 mb-3 pb-2 border-b ${col.borderColor}`}>
            <h3 className={`text-sm font-semibold ${col.color}`}>{col.title}</h3>
            <span className="text-xs bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded-full">
              {col.tasks.length}
            </span>
          </div>
          <div className="space-y-2">
            {col.tasks.map((task, i) => (
              <TaskCard key={task.id || i} task={task} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
