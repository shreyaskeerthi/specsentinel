/**
 * Project detail page with documents and analyses.
 */

import React, { useEffect, useState, useCallback } from "react";
import Head from "next/head";
import { useRouter } from "next/router";
import { format } from "date-fns";
import Layout from "@/components/Layout";
import FileUpload from "@/components/FileUpload";
import AnalysisSummary from "@/components/AnalysisSummary";
import PdfViewer from "@/components/PdfViewer";
import { projectsApi, documentsApi, analysisApi } from "@/lib/api";
import type { Project, AnalysisResult, SpecLocation } from "@/lib/types";

const statusColors: Record<string, string> = {
  pending: "bg-gray-100 text-gray-800",
  processing: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
};

export default function ProjectDetailPage() {
  const router = useRouter();
  const { id } = router.query;

  const [project, setProject] = useState<Project | null>(null);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  // PDF Viewer state
  const [showPdfViewer, setShowPdfViewer] = useState(false);
  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [highlightLocation, setHighlightLocation] = useState<SpecLocation | null>(null);
  const [highlightText, setHighlightText] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadProject(id as string);
    }
  }, [id]);

  const loadProject = async (projectId: string) => {
    try {
      const data = await projectsApi.get(projectId);
      setProject(data);

      // Auto-select first document with analysis
      const docWithAnalysis = data.documents?.find((d: any) => d.status === "completed");
      if (docWithAnalysis) {
        setSelectedDocId(docWithAnalysis.id);
        loadAnalysis(docWithAnalysis.id);
      }
    } catch (err) {
      console.error("Failed to load project:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadAnalysis = async (docId: string) => {
    setAnalysisLoading(true);
    try {
      const data = await analysisApi.get(docId);
      setAnalysis(data);
    } catch (err) {
      console.error("Failed to load analysis:", err);
      setAnalysis(null);
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleDocumentSelect = (docId: string) => {
    setSelectedDocId(docId);
    loadAnalysis(docId);
  };

  const handleUpload = async (file: File) => {
    if (!project) return;

    const result = await documentsApi.upload(project.id, file);
    // Reload project to get updated document list
    loadProject(project.id);

    // If analysis was returned, show it
    if (result.analysis) {
      setSelectedDocId(result.document.id);
      setAnalysis(result.analysis);
    }
  };

  // Load PDF for viewing (regular, no highlights)
  const loadPdfForViewing = useCallback(async (docId: string) => {
    setPdfLoading(true);
    try {
      const blobUrl = await documentsApi.getDocumentBlob(docId);
      // Clean up previous blob URL if exists
      if (pdfBlobUrl) {
        URL.revokeObjectURL(pdfBlobUrl);
      }
      setPdfBlobUrl(blobUrl);
      setShowPdfViewer(true);
    } catch (err) {
      console.error("Failed to load PDF:", err);
    } finally {
      setPdfLoading(false);
    }
  }, [pdfBlobUrl]);

  // Load PDF with highlights for a specific text
  const loadHighlightedPdf = useCallback(async (
    docId: string,
    searchText: string | null,
    page: number | null
  ) => {
    setPdfLoading(true);
    try {
      // Clean up previous blob URL if exists
      if (pdfBlobUrl) {
        URL.revokeObjectURL(pdfBlobUrl);
      }

      // Fetch highlighted PDF from server
      const blobUrl = await documentsApi.getHighlightedDocumentBlob(
        docId,
        searchText || undefined,
        page || undefined
      );
      setPdfBlobUrl(blobUrl);
      setShowPdfViewer(true);
    } catch (err) {
      console.error("Failed to load highlighted PDF:", err);
      // Fall back to regular PDF
      loadPdfForViewing(docId);
    } finally {
      setPdfLoading(false);
    }
  }, [pdfBlobUrl, loadPdfForViewing]);

  // Handle "View in spec" button click
  const handleViewInSpec = useCallback((location: SpecLocation, quote: string | null) => {
    if (!selectedDocId) return;

    setHighlightLocation(location);
    setHighlightText(quote);

    // Always fetch a new highlighted PDF when clicking "View in spec"
    loadHighlightedPdf(selectedDocId, quote, location.page);
  }, [selectedDocId, loadHighlightedPdf]);

  // Clean up blob URL on unmount
  useEffect(() => {
    return () => {
      if (pdfBlobUrl) {
        URL.revokeObjectURL(pdfBlobUrl);
      }
    };
  }, [pdfBlobUrl]);

  // Reset PDF viewer when document changes
  useEffect(() => {
    if (pdfBlobUrl) {
      URL.revokeObjectURL(pdfBlobUrl);
      setPdfBlobUrl(null);
    }
    setShowPdfViewer(false);
    setHighlightLocation(null);
    setHighlightText(null);
  }, [selectedDocId]);

  if (loading) {
    return (
      <Layout requireAuth>
        <div className="max-w-7xl mx-auto px-4 py-8 text-center">
          <p className="text-gray-500">Loading project...</p>
        </div>
      </Layout>
    );
  }

  if (!project) {
    return (
      <Layout requireAuth>
        <div className="max-w-7xl mx-auto px-4 py-8 text-center">
          <p className="text-gray-500">Project not found</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout requireAuth>
      <Head>
        <title>{project.name} - SpecSentinel</title>
      </Head>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push("/dashboard")}
            className="text-sm text-gray-500 hover:text-gray-700 mb-4 flex items-center"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Projects
          </button>

          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
              <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                {project.client_name && <span>Client: {project.client_name}</span>}
                {project.bid_due_date && (
                  <span>Due: {format(new Date(project.bid_due_date), "MMM d, yyyy")}</span>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left sidebar - Documents */}
          <div className="lg:col-span-1">
            <div className="card mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Documents</h2>

              <FileUpload onUpload={handleUpload} />

              {project.documents && project.documents.length > 0 && (
                <div className="mt-6 space-y-3">
                  {project.documents.map((doc) => (
                    <div
                      key={doc.id}
                      onClick={() => doc.status === "completed" && handleDocumentSelect(doc.id)}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedDocId === doc.id
                          ? "border-primary-500 bg-primary-50"
                          : "border-gray-200 hover:border-gray-300"
                      } ${doc.status !== "completed" ? "opacity-60 cursor-not-allowed" : ""}`}
                    >
                      <div className="flex justify-between items-start">
                        <p className="font-medium text-sm text-gray-900 truncate flex-1">
                          {doc.original_filename}
                        </p>
                        <span className={`badge ${statusColors[doc.status]} ml-2`}>
                          {doc.status}
                        </span>
                      </div>
                      {doc.page_count && (
                        <p className="text-xs text-gray-500 mt-1">{doc.page_count} pages</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Main content - Analysis */}
          <div className="lg:col-span-2">
            {analysisLoading ? (
              <div className="card text-center py-12">
                <p className="text-gray-500">Loading analysis...</p>
              </div>
            ) : analysis ? (
              <div className="space-y-4">
                {/* PDF Viewer toggle */}
                {selectedDocId && (
                  <div className="flex justify-between items-center mb-2">
                    <div className="text-sm text-gray-500">
                      {highlightLocation?.page && showPdfViewer && (
                        <span className="inline-flex items-center px-2 py-1 bg-yellow-100 text-yellow-800 rounded">
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          Showing Page {highlightLocation.page}
                          {highlightLocation.section && ` - Section ${highlightLocation.section}`}
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => {
                        if (showPdfViewer) {
                          setShowPdfViewer(false);
                          setHighlightLocation(null);
                          setHighlightText(null);
                        } else if (pdfBlobUrl) {
                          setShowPdfViewer(true);
                        } else {
                          loadPdfForViewing(selectedDocId);
                        }
                      }}
                      disabled={pdfLoading}
                      className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-primary-700 bg-primary-50 rounded-lg hover:bg-primary-100 disabled:opacity-50"
                    >
                      {pdfLoading ? (
                        <>
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Loading PDF...
                        </>
                      ) : showPdfViewer ? (
                        <>
                          <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                          Hide PDF
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          View PDF
                        </>
                      )}
                    </button>
                  </div>
                )}

                {/* PDF Viewer - sticky at top when open */}
                {showPdfViewer && pdfBlobUrl && (
                  <>
                    <div className="sticky top-4 z-10 h-[500px] border-2 border-primary-300 rounded-lg overflow-hidden mb-4 shadow-lg bg-white">
                      <PdfViewer
                        pdfUrl={pdfBlobUrl}
                        highlightLocation={highlightLocation}
                        highlightText={highlightText}
                        onClose={() => {
                          setShowPdfViewer(false);
                          setHighlightLocation(null);
                          setHighlightText(null);
                        }}
                      />
                    </div>
                    {/* Fixed close button - always visible */}
                    <button
                      onClick={() => {
                        setShowPdfViewer(false);
                        setHighlightLocation(null);
                        setHighlightText(null);
                      }}
                      className="fixed top-20 right-8 z-50 p-2 bg-gray-800 hover:bg-gray-900 text-white rounded-lg shadow-lg flex items-center space-x-1 text-sm"
                      title="Close PDF"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                      <span>Close PDF</span>
                    </button>
                  </>
                )}

                {/* Analysis Summary */}
                <AnalysisSummary analysis={analysis} onViewInSpec={handleViewInSpec} />
              </div>
            ) : (
              <div className="card text-center py-12">
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Analysis Selected</h3>
                <p className="text-gray-500">
                  Upload a PDF document or select a completed document to view its analysis.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
