/**
 * Main layout wrapper with navigation.
 */

import React, { useEffect, useState } from "react";
import { useRouter } from "next/router";
import TopNav from "./TopNav";
import { isAuthenticated } from "@/lib/auth";

interface LayoutProps {
  children: React.ReactNode;
  requireAuth?: boolean;
}

export default function Layout({ children, requireAuth = false }: LayoutProps) {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (requireAuth && !isAuthenticated()) {
      router.push("/login");
    }
  }, [requireAuth, router]);

  // Avoid hydration mismatch
  if (!mounted) {
    return null;
  }

  // Public pages don't need nav
  const isPublicPage = ["/", "/login", "/register"].includes(router.pathname);

  return (
    <div className="min-h-screen bg-gray-50">
      {!isPublicPage && <TopNav />}
      <main className={isPublicPage ? "" : "pt-16"}>
        {children}
      </main>
    </div>
  );
}
