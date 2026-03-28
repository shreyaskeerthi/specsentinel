"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  getProject, updateProject, uploadSpec, pollAnalysis, getAnalysis,
  analyzeMeetingNotes, generateEmails, addTeamMember, removeTeamMember,
  inviteTeamMember,
} from "@/lib/api";
import { isAuthenticated, getUser, logout } from "@/lib/auth";
import type { EmailSet, MeetingAnalysis } from "@/lib/types";
import FileUpload from "@/components/FileUpload";
import MeetingNotes from "@/components/MeetingNotes";
import BidDecision from "@/components/BidDecision";
import FinancialSummary from "@/components/FinancialSummary";
import RiskFlags from "@/components/RiskFlags";
import Requirements from "@/components/Requirements";
import ActionBoardView from "@/components/ActionBoard";
import EmailPanel from "@/components/EmailPanel";
import TeamPanel from "@/components/TeamPanel";
import Calendar from "@/components/Calendar";
import Milestones from "@/components/Milestones";
import TabNav from "@/components/TabNav";
import type { ScheduleEvent } from "@/lib/types";
import { createMilestone, updateMilestone, deleteMilestone } from "@/lib/api";

const TABS = [
  { id: "overview", label: "Overview" },
  { id: "financials", label: "Financials" },
  { id: "risks", label: "Risks" },
  { id: "requirements", label: "Requirements" },
  { id: "actionboard", label: "ActionBoard" },
  { id: "milestones", label: "Milestones" },
  { id: "schedule", label: "Schedule" },
  { id: "emails", label: "Emails" },
  { id: "team", label: "Team" },
];

function formatCurrency(n: number | null | undefined): string {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);
}

export default function ProjectPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;

  const [project, setProject] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [meetingResult, setMeetingResult] = useState<MeetingAnalysis | null>(null);
  const [emailSet, setEmailSet] = useState<EmailSet | null>(null);
  const [scheduleEvents, setScheduleEvents] = useState<ScheduleEvent[]>([]);
  const [activeTab, setActiveTab] = useState("overview");
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const user = getUser();

  const loadProject = useCallback(async () => {
    try {
      const data = await getProject(projectId);
      setProject(data);

      // Load latest completed analysis if exists
      const completedAnalysis = data.analyses?.find((a: any) => a.status === "completed" && a.has_risk_report);
      if (completedAnalysis) {
        const full = await getAnalysis(completedAnalysis.id);
        setAnalysis(full);
        if (full.email_set) setEmailSet(full.email_set);
      }

      // Check if there's a processing analysis
      const processingAnalysis = data.analyses?.find((a: any) => a.status === "processing" || a.status === "pending");
      if (processingAnalysis) {
        setUploading(true);
        setUploadProgress("Analysis in progress...");
        try {
          const result = await pollAnalysis(processingAnalysis.id, (status) => {
            setUploadProgress(status === "processing" ? "AI is analyzing the spec..." : "Starting analysis...");
          });
          setAnalysis(result);
          setUploading(false);
          setUploadProgress("");
          loadProject(); // Refresh
        } catch (err: any) {
          setError(err.message || "Analysis failed");
          setUploading(false);
          setUploadProgress("");
        }
      }
    } catch {
      router.replace("/dashboard");
    } finally {
      setLoading(false);
    }
  }, [projectId, router]);

  useEffect(() => {
    if (!isAuthenticated()) { router.replace("/login"); return; }
    loadProject();
  }, [router, loadProject]);

  const handleUpload = useCallback(async (file: File) => {
    setUploading(true);
    setError("");
    setUploadProgress("Uploading...");
    try {
      const { analysis_id } = await uploadSpec(projectId, file);
      setUploadProgress("AI is analyzing the spec...");
      const result = await pollAnalysis(analysis_id, (status) => {
        if (status === "processing") setUploadProgress("AI is analyzing the spec... This takes 30-60 seconds.");
      });
      setAnalysis(result);
      setUploadProgress("");
      loadProject();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Upload failed");
      setUploadProgress("");
    } finally {
      setUploading(false);
    }
  }, [projectId, loadProject]);

  const handleMeetingNotes = useCallback(async (notes: string, title?: string) => {
    try {
      const { analysis_id, merging_into } = await analyzeMeetingNotes(projectId, notes, title);
      const result = await pollAnalysis(analysis_id);
      if (result.meeting_result) {
        setMeetingResult(result.meeting_result);
        // Capture schedule events
        if (result.meeting_result.schedule_events) {
          setScheduleEvents((prev) => [...prev, ...result.meeting_result.schedule_events]);
        }
      }
      // Refresh the main analysis if meeting merged into it
      if (merging_into && analysis) {
        const refreshed = await getAnalysis(merging_into);
        setAnalysis(refreshed);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Meeting analysis failed");
    }
  }, [projectId, analysis]);

  const handleGenerateEmails = useCallback(async () => {
    if (!analysis) return;
    try {
      const result = await generateEmails(analysis.id);
      setEmailSet(result);
      setActiveTab("emails");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Email generation failed");
    }
  }, [analysis]);

  const handleTeamAdd = useCallback(async (member: any) => {
    await addTeamMember(projectId, member);
    loadProject();
  }, [projectId, loadProject]);

  const handleTeamRemove = useCallback(async (memberId: string) => {
    await removeTeamMember(projectId, memberId);
    loadProject();
  }, [projectId, loadProject]);

  const handleTeamInvite = useCallback(async (memberId: string) => {
    await inviteTeamMember(projectId, memberId);
    loadProject();
  }, [projectId, loadProject]);

  const handleMilestoneAdd = useCallback(async (data: any) => {
    await createMilestone(projectId, data);
    loadProject();
  }, [projectId, loadProject]);

  const handleMilestoneUpdate = useCallback(async (id: string, data: any) => {
    await updateMilestone(projectId, id, data);
    loadProject();
  }, [projectId, loadProject]);

  const handleMilestoneDelete = useCallback(async (id: string) => {
    await deleteMilestone(projectId, id);
    loadProject();
  }, [projectId, loadProject]);

  if (loading) return <div className="min-h-screen flex items-center justify-center text-gray-500">Loading...</div>;
  if (!project) return null;

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button onClick={() => router.push("/dashboard")} className="text-gray-500 hover:text-gray-300 mr-2">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">SS</span>
              </div>
              <div>
                <h1 className="text-base font-bold text-white">{project.name}</h1>
                <div className="flex items-center gap-3 text-xs text-gray-500">
                  {project.client_name && <span>{project.client_name}</span>}
                  {project.contract_value && <span className="text-green-400 font-semibold">{formatCurrency(project.contract_value)}</span>}
                  {project.bid_due_date && <span>Due: {project.bid_due_date}</span>}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-400">{user?.full_name}</span>
              <button onClick={logout} className="text-sm text-gray-500 hover:text-gray-300">Sign out</button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Upload + Meeting Notes Row (optional) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          <FileUpload onUpload={handleUpload} uploading={uploading} progress={uploadProgress} />
          <MeetingNotes onAnalyze={handleMeetingNotes} meetingResult={meetingResult} disabled={false} projectId={projectId} />
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 bg-red-900/30 border border-red-800 text-red-400 px-4 py-3 rounded-lg text-sm">
            {error}
            <button onClick={() => setError("")} className="ml-2 text-red-500 hover:text-red-300">Dismiss</button>
          </div>
        )}

        {/* Analysis history */}
        {project.analyses?.length > 0 && !analysis && (
          <div className="mb-4">
            <p className="text-sm text-gray-500 mb-2">Previous analyses:</p>
            <div className="flex gap-2 flex-wrap">
              {project.analyses.map((a: any) => (
                <button
                  key={a.id}
                  onClick={async () => {
                    if (a.status === "completed") {
                      const full = await getAnalysis(a.id);
                      setAnalysis(full);
                    }
                  }}
                  className={`text-xs px-3 py-1.5 rounded-lg border ${
                    a.status === "completed" ? "border-green-800 text-green-400 hover:bg-green-950/20" :
                    a.status === "failed" ? "border-red-800 text-red-400" :
                    "border-gray-700 text-gray-400"
                  }`}
                >
                  {a.filename || a.source_type} — {a.status}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Results with tabs */}
        {analysis && analysis.status === "completed" && (
          <>
            <TabNav tabs={TABS} activeTab={activeTab} onChange={setActiveTab} onGenerateEmails={handleGenerateEmails} />
            <div className="mt-4">
              {activeTab === "overview" && <BidDecision analysis={analysis} contractValue={project.contract_value} />}
              {activeTab === "financials" && <FinancialSummary analysis={analysis} contractValue={project.contract_value} budget={project.budget} />}
              {activeTab === "risks" && <RiskFlags flags={analysis.risk_report?.flags || []} />}
              {activeTab === "requirements" && <Requirements extraction={analysis.extraction || {}} />}
              {activeTab === "actionboard" && <ActionBoardView actionBoard={analysis.action_board} meetingTasks={meetingResult?.updated_tasks} />}
              {activeTab === "emails" && <EmailPanel emailSet={emailSet} onGenerate={handleGenerateEmails} analysisId={analysis.id} />}
              {activeTab === "milestones" && (
                <Milestones
                  milestones={project.milestones || { preconstruction: [], construction: [], closeout: [] }}
                  onAdd={handleMilestoneAdd}
                  onUpdate={handleMilestoneUpdate}
                  onDelete={handleMilestoneDelete}
                />
              )}
              {activeTab === "schedule" && (
                <Calendar
                  tasks={[
                    ...(analysis.action_board?.to_clarify || []),
                    ...(analysis.action_board?.must_include || []),
                    ...(analysis.action_board?.internal || []),
                  ]}
                  scheduleEvents={scheduleEvents}
                  bidDueDate={project.bid_due_date}
                  teamMembers={(project.team_members || []).filter((m: any) => m.email)}
                  onAddEvent={(ev) => setScheduleEvents((prev) => [...prev, { ...ev, linked_task_id: null } as ScheduleEvent])}
                  onSendSchedule={(memberIds) => {
                    // Simulate sending
                    alert(`Schedule sent to ${memberIds.length} team member(s)!`);
                  }}
                />
              )}
              {activeTab === "team" && (
                <TeamPanel
                  members={project.team_members || []}
                  onAdd={handleTeamAdd}
                  onRemove={handleTeamRemove}
                  onInvite={handleTeamInvite}
                />
              )}
            </div>
          </>
        )}

        {/* Empty state when no analysis */}
        {!analysis && !uploading && (
          <div className="text-center py-16">
            <div className="w-16 h-16 bg-gray-800 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-300 mb-2">Upload a spec or paste meeting notes</h2>
            <p className="text-gray-500 max-w-md mx-auto">
              Both are optional — upload a PDF spec to get a full risk analysis, or paste meeting notes to extract decisions and tasks.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
