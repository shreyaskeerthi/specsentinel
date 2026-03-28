/**
 * Billing and subscription management page.
 */

import React, { useEffect, useState } from "react";
import Head from "next/head";
import Layout from "@/components/Layout";
import { billingApi, organizationApi } from "@/lib/api";
import type { Plan, UsageStats, Organization } from "@/lib/types";

const tierColors: Record<string, string> = {
  free: "bg-gray-100 text-gray-800",
  pro: "bg-primary-100 text-primary-800",
  enterprise: "bg-purple-100 text-purple-800",
};

export default function BillingPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [plansData, usageData, orgData] = await Promise.all([
        billingApi.getPlans(),
        billingApi.getUsage(),
        organizationApi.getCurrent(),
      ]);
      setPlans(plansData);
      setUsage(usageData);
      setOrganization(orgData);
    } catch (err) {
      console.error("Failed to load billing data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (planTier: string) => {
    try {
      const result = await billingApi.createCheckout(planTier);
      // TODO: Redirect to Stripe checkout
      alert(`Checkout URL: ${result.checkout_url}\n\n(Stripe integration is a TODO)`);
    } catch (err) {
      console.error("Failed to create checkout:", err);
    }
  };

  const formatPrice = (cents: number) => {
    return `$${(cents / 100).toFixed(0)}`;
  };

  const formatLimit = (value: number) => {
    return value === 0 ? "Unlimited" : value.toString();
  };

  if (loading) {
    return (
      <Layout requireAuth>
        <div className="max-w-7xl mx-auto px-4 py-8 text-center">
          <p className="text-gray-500">Loading...</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout requireAuth>
      <Head>
        <title>Billing - SpecSentinel</title>
      </Head>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-8">Billing & Subscription</h1>

        {/* Current Plan & Usage */}
        <div className="grid md:grid-cols-2 gap-6 mb-12">
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Plan</h2>
            <div className="flex items-center mb-4">
              <span className={`badge ${tierColors[usage?.plan_tier || "free"]} text-lg px-3 py-1`}>
                {usage?.plan_tier?.toUpperCase() || "FREE"}
              </span>
            </div>
            <p className="text-gray-600">
              {organization?.name}
            </p>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Usage This Month</h2>
            {usage && (
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Documents Analyzed</span>
                    <span className="font-medium">
                      {usage.documents_analyzed_this_month} / {formatLimit(usage.documents_limit)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary-600 h-2 rounded-full"
                      style={{
                        width: `${usage.documents_limit > 0
                          ? Math.min((usage.documents_analyzed_this_month / usage.documents_limit) * 100, 100)
                          : 0}%`
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Projects</span>
                    <span className="font-medium">
                      {usage.projects_count} / {formatLimit(usage.projects_limit)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary-600 h-2 rounded-full"
                      style={{
                        width: `${usage.projects_limit > 0
                          ? Math.min((usage.projects_count / usage.projects_limit) * 100, 100)
                          : 0}%`
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">Team Members</span>
                    <span className="font-medium">
                      {usage.users_count} / {formatLimit(usage.users_limit)}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Plans */}
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Available Plans</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`card ${plan.tier === usage?.plan_tier ? "ring-2 ring-primary-500" : ""}`}
            >
              <div className="mb-4">
                <h3 className="text-xl font-bold text-gray-900">{plan.name}</h3>
                <div className="mt-2">
                  <span className="text-3xl font-bold text-gray-900">
                    {formatPrice(plan.price_monthly_cents)}
                  </span>
                  <span className="text-gray-500">/month</span>
                </div>
              </div>

              <ul className="space-y-3 mb-6">
                <li className="flex items-center text-sm text-gray-600">
                  <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  {formatLimit(plan.max_projects)} projects
                </li>
                <li className="flex items-center text-sm text-gray-600">
                  <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  {formatLimit(plan.max_documents_per_month)} documents/month
                </li>
                <li className="flex items-center text-sm text-gray-600">
                  <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  {formatLimit(plan.max_users)} team members
                </li>
              </ul>

              {plan.tier === usage?.plan_tier ? (
                <button className="w-full btn-secondary" disabled>
                  Current Plan
                </button>
              ) : (
                <button
                  onClick={() => handleUpgrade(plan.tier)}
                  className="w-full btn-primary"
                >
                  {plan.price_monthly_cents === 0 ? "Downgrade" : "Upgrade"}
                </button>
              )}
            </div>
          ))}
        </div>

        <p className="text-sm text-gray-500 text-center mt-8">
          Stripe integration is a TODO. Contact support for plan changes.
        </p>
      </div>
    </Layout>
  );
}
