/**
 * Top navigation bar for authenticated users.
 */

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import { logout } from "@/lib/auth";
import { authApi } from "@/lib/api";
import type { User } from "@/lib/types";

export default function TopNav() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    authApi.getMe().then(setUser).catch(() => {});
  }, []);

  const handleLogout = () => {
    logout();
  };

  return (
    <nav className="fixed top-0 left-0 right-0 bg-white border-b border-gray-200 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo & main nav */}
          <div className="flex items-center">
            <Link href="/dashboard" className="flex items-center">
              <span className="text-xl font-bold text-primary-600">SpecSentinel</span>
            </Link>
            <div className="hidden md:ml-10 md:flex md:space-x-8">
              <Link
                href="/dashboard"
                className={`inline-flex items-center px-1 pt-1 text-sm font-medium border-b-2 ${
                  router.pathname === "/dashboard"
                    ? "border-primary-500 text-gray-900"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                Dashboard
              </Link>
            </div>
          </div>

          {/* Right side */}
          <div className="flex items-center">
            <Link
              href="/account/billing"
              className="mr-4 text-sm text-gray-500 hover:text-gray-700"
            >
              Billing
            </Link>

            {/* User menu */}
            <div className="relative">
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                  <span className="text-primary-700 font-medium">
                    {user?.full_name?.charAt(0) || "U"}
                  </span>
                </div>
              </button>

              {menuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1">
                  <div className="px-4 py-2 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
                    <p className="text-xs text-gray-500">{user?.email}</p>
                  </div>
                  <Link
                    href="/account/billing"
                    className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    onClick={() => setMenuOpen(false)}
                  >
                    Account Settings
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
