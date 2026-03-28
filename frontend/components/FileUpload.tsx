/**
 * File upload component for PDF documents with progress indicator.
 */

import React, { useCallback, useState, useEffect } from "react";

interface FileUploadProps {
  onUpload: (file: File) => Promise<void>;
  accept?: string;
  maxSizeMB?: number;
}

const PROCESSING_STEPS = [
  { label: "Uploading document...", duration: 2000 },
  { label: "Extracting text from PDF...", duration: 3000 },
  { label: "Analyzing spec requirements...", duration: 4000 },
  { label: "Identifying risk flags...", duration: 4000 },
  { label: "Generating bid report...", duration: 3000 },
];

export default function FileUpload({
  onUpload,
  accept = ".pdf",
  maxSizeMB = 50,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [fileName, setFileName] = useState<string | null>(null);

  useEffect(() => {
    if (!isUploading) {
      setCurrentStep(0);
      return;
    }

    // Cycle through processing steps while uploading
    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= PROCESSING_STEPS.length - 1) {
          return prev; // Stay on last step
        }
        return prev + 1;
      });
    }, PROCESSING_STEPS[currentStep]?.duration || 3000);

    return () => clearInterval(interval);
  }, [isUploading, currentStep]);

  const handleFile = async (file: File) => {
    setError(null);
    setFileName(file.name);

    // Validate file type
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported");
      return;
    }

    // Validate file size
    const maxBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxBytes) {
      setError(`File size must be less than ${maxSizeMB}MB`);
      return;
    }

    setIsUploading(true);
    setCurrentStep(0);
    try {
      await onUpload(file);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Upload failed");
    } finally {
      setIsUploading(false);
      setFileName(null);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  if (isUploading) {
    return (
      <div className="border-2 border-primary-200 bg-primary-50 rounded-lg p-8">
        <div className="flex flex-col items-center">
          {/* Animated spinner */}
          <div className="relative mb-4">
            <div className="w-16 h-16 border-4 border-primary-200 rounded-full"></div>
            <div className="absolute top-0 left-0 w-16 h-16 border-4 border-primary-600 rounded-full border-t-transparent animate-spin"></div>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
              <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>

          {/* File name */}
          {fileName && (
            <p className="text-sm font-medium text-gray-900 mb-2 truncate max-w-full">
              {fileName}
            </p>
          )}

          {/* Current processing step */}
          <p className="text-primary-700 font-medium mb-3">
            {PROCESSING_STEPS[currentStep]?.label || "Processing..."}
          </p>

          {/* Progress dots */}
          <div className="flex space-x-2 mb-4">
            {PROCESSING_STEPS.map((_, idx) => (
              <div
                key={idx}
                className={`w-2 h-2 rounded-full transition-colors duration-300 ${
                  idx <= currentStep ? "bg-primary-600" : "bg-gray-300"
                }`}
              />
            ))}
          </div>

          {/* Info text */}
          <p className="text-xs text-gray-500 text-center">
            AI is analyzing your spec document for bid risks.
            <br />
            This usually takes 15-30 seconds.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging
            ? "border-primary-500 bg-primary-50"
            : "border-gray-300 hover:border-gray-400"
        }`}
      >
        <input
          type="file"
          accept={accept}
          onChange={handleInputChange}
          className="hidden"
          id="file-upload"
        />
        <label htmlFor="file-upload" className="cursor-pointer">
          <div className="flex flex-col items-center">
            <svg
              className="w-12 h-12 text-gray-400 mb-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <p className="text-gray-600 mb-1">
              <span className="text-primary-600 font-medium">Click to upload</span> or drag and
              drop
            </p>
            <p className="text-sm text-gray-500">PDF files up to {maxSizeMB}MB</p>
          </div>
        </label>
      </div>

      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}
