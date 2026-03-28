/**
 * Project card component for dashboard list.
 */

import React from "react";
import Link from "next/link";
import { format } from "date-fns";
import type { ProjectListItem } from "@/lib/types";

interface ProjectCardProps {
  project: ProjectListItem;
}

const statusColors: Record<string, string> = {
  active: "bg-blue-100 text-blue-800",
  won: "bg-green-100 text-green-800",
  lost: "bg-red-100 text-red-800",
  no_bid: "bg-gray-100 text-gray-800",
  archived: "bg-gray-100 text-gray-600",
};

export default function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link href={`/projects/${project.id}`}>
      <div className="card hover:shadow-md transition-shadow cursor-pointer">
        <div className="flex justify-between items-start mb-3">
          <h3 className="text-lg font-semibold text-gray-900 truncate">
            {project.name}
          </h3>
          <span className={`badge ${statusColors[project.status] || statusColors.active}`}>
            {project.status}
          </span>
        </div>

        {project.client_name && (
          <p className="text-sm text-gray-600 mb-2">
            Client: {project.client_name}
          </p>
        )}

        <div className="flex justify-between items-center text-sm text-gray-500">
          <div className="flex items-center space-x-4">
            <span>{project.document_count} document(s)</span>
            {project.bid_due_date && (
              <span>Due: {format(new Date(project.bid_due_date), "MMM d, yyyy")}</span>
            )}
          </div>
        </div>

        {project.last_analysis_date && (
          <p className="text-xs text-gray-400 mt-2">
            Last analyzed: {format(new Date(project.last_analysis_date), "MMM d, yyyy h:mm a")}
          </p>
        )}
      </div>
    </Link>
  );
}
