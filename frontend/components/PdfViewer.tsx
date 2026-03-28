/**
 * PDF Viewer component with page navigation.
 * Uses native browser PDF rendering for speed and reliability.
 */

import React, { useState, useEffect, useRef } from "react";
import type { SpecLocation } from "@/lib/types";

interface PdfViewerProps {
  /** URL or blob URL of the PDF file */
  pdfUrl: string;
  /** Currently highlighted location (from clicking "View in spec") */
  highlightLocation?: SpecLocation | null;
  /** Text to highlight on the current page */
  highlightText?: string | null;
  /** Callback when viewer is closed */
  onClose?: () => void;
}

export default function PdfViewer({
  pdfUrl,
  highlightLocation,
  highlightText,
  onClose,
}: PdfViewerProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);

  // Navigate to page when highlight location changes
  useEffect(() => {
    if (highlightLocation?.page && iframeRef.current) {
      // PDF.js viewer supports #page=N in URL
      const pageNum = highlightLocation.page;
      setCurrentPage(pageNum);

      // Update iframe src to navigate to page
      const baseUrl = pdfUrl.split('#')[0];
      iframeRef.current.src = `${baseUrl}#page=${pageNum}`;
    }
  }, [highlightLocation, pdfUrl]);

  // Build initial URL with page if available
  const initialUrl = highlightLocation?.page
    ? `${pdfUrl}#page=${highlightLocation.page}`
    : pdfUrl;

  return (
    <div className="relative flex flex-col h-full bg-gray-100 rounded-lg overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-gray-800 text-white">
        <div className="flex items-center space-x-3">
          {highlightLocation?.page && (
            <span className="text-sm">
              Page {highlightLocation.page}
              {highlightLocation.section && ` · ${highlightLocation.section}`}
            </span>
          )}
          {highlightText && (
            <span className="text-xs text-gray-300 italic truncate max-w-xs">
              "{highlightText}"
            </span>
          )}
        </div>

        <div className="flex items-center space-x-1">
          {/* Open in new tab */}
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1 rounded hover:bg-gray-700 text-gray-300 hover:text-white"
            title="Open in new tab"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>

          {/* Close button */}
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-gray-700 text-gray-300 hover:text-white"
              title="Close (Esc)"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* PDF iframe */}
      <div className="flex-1 bg-gray-200">
        <iframe
          ref={iframeRef}
          src={initialUrl}
          className="w-full h-full border-0"
          title="PDF Document"
        />
      </div>
    </div>
  );
}
