/**
 * Landing page for SpecSentinel.
 */

import React from "react";
import Head from "next/head";
import Link from "next/link";

export default function HomePage() {
  return (
    <>
      <Head>
        <title>SpecSentinel - AI-Powered Spec Checker for Contractors</title>
        <meta
          name="description"
          content="AI-powered spec-checker for commercial HVAC/Plumbing/Electrical contractors. Analyze project manuals and identify risks instantly."
        />
      </Head>

      <div className="min-h-screen bg-gradient-to-b from-primary-50 to-white">
        {/* Nav */}
        <nav className="px-6 py-4">
          <div className="max-w-6xl mx-auto flex justify-between items-center">
            <span className="text-2xl font-bold text-primary-600">SpecSentinel</span>
            <div className="space-x-4">
              <Link href="/login" className="text-gray-600 hover:text-gray-900">
                Log In
              </Link>
              <Link href="/register" className="btn-primary">
                Get Started
              </Link>
            </div>
          </div>
        </nav>

        {/* Hero */}
        <section className="px-6 py-20">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-5xl font-bold text-gray-900 mb-6">
              Stop Missing Critical Spec Requirements
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              SpecSentinel uses AI to analyze project manuals and surface key requirements,
              risks, and red flags for HVAC, Plumbing, and Electrical contractors.
            </p>
            <div className="flex justify-center space-x-4">
              <Link href="/register" className="btn-primary text-lg px-8 py-3">
                Start Free Trial
              </Link>
              <Link href="#features" className="btn-secondary text-lg px-8 py-3">
                Learn More
              </Link>
            </div>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="px-6 py-20 bg-white">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
              Everything You Need for Spec Review
            </h2>

            <div className="grid md:grid-cols-3 gap-8">
              <div className="card">
                <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2">PDF Analysis</h3>
                <p className="text-gray-600">
                  Upload project manuals and specifications. Our AI extracts and organizes
                  key requirements by division.
                </p>
              </div>

              <div className="card">
                <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2">Risk Detection</h3>
                <p className="text-gray-600">
                  Automatically identify high-risk clauses: liquidated damages, extended
                  warranties, bonding requirements, and more.
                </p>
              </div>

              <div className="card">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2">Bid Summaries</h3>
                <p className="text-gray-600">
                  Get organized summaries of insurance, warranty, testing, commissioning,
                  and submittal requirements.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="px-6 py-20 bg-primary-600">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl font-bold text-white mb-4">
              Ready to streamline your spec review?
            </h2>
            <p className="text-primary-100 mb-8">
              Join contractors who save hours on every bid with SpecSentinel.
            </p>
            <Link href="/register" className="bg-white text-primary-600 px-8 py-3 rounded-lg font-medium hover:bg-primary-50 transition-colors">
              Get Started Free
            </Link>
          </div>
        </section>

        {/* Footer */}
        <footer className="px-6 py-8 bg-gray-900 text-gray-400">
          <div className="max-w-6xl mx-auto text-center">
            <p>&copy; 2024 SpecSentinel. All rights reserved.</p>
          </div>
        </footer>
      </div>
    </>
  );
}
