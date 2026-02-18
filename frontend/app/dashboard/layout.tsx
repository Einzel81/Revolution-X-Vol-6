"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Menu,
  X,
  Home,
  BarChart3,
  Target,
  Settings,
  Bell,
  User,
  TrendingUp,
  Shield,
  Zap
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { AlertCenter } from "@/components/notifications/alert-center";
import { ToastProvider } from "@/components/notifications/toast-provider";

const sidebarItems = [
  { icon: Home, label: "الرئيسية", href: "/dashboard" },
  { icon: BarChart3, label: "الرسوم البيانية", href: "/dashboard/charts" },
  { icon: Target, label: "الفرص", href: "/dashboard/scanner" },
  { icon: TrendingUp, label: "المراكز", href: "/dashboard/positions" },
  { icon: Shield, label: "DXY Guardian", href: "/dashboard/dxy" },
  { icon: Zap, label: "الذكاء الاصطناعي", href: "/dashboard/ai" },
  { icon: Settings, label: "الإعدادات", href: "/dashboard/settings" },
];

const bottomNavItems = [
  { icon: Home, label: "الرئيسية", href: "/dashboard" },
  { icon: BarChart3, label: "الرسوم", href: "/dashboard/charts" },
  { icon: Target, label: "الفرص", href: "/dashboard/scanner" },
  { icon: User, label: "حسابي", href: "/dashboard/profile" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isMobile, setIsMobile] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 1024);
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="p-6 border-b border-slate-700">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Revolution X</h1>
            <p className="text-xs text-slate-400">نظام التداول المتقدم</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {sidebarItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setSidebarOpen(false)}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span>{item.label}</span>
              {isActive && (
                <motion.div
                  layoutId="activeIndicator"
                  className="mr-auto w-1.5 h-1.5 rounded-full bg-white"
                />
              )}
            </Link>
          );
        })}
      </nav>

      {/* User Profile Summary */}
      <div className="p-4 border-t border-slate-700">
        <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg">
          <div className="w-10 h-10 bg-slate-700 rounded-full flex items-center justify-center">
            <User className="w-5 h-5 text-slate-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-white">المستخدم</p>
            <p className="text-xs text-slate-400">متصل</p>
          </div>
          <div className="w-2 h-2 rounded-full bg-green-500" />
        </div>
      </div>
    </div>
  );

  return (
    <ToastProvider>
      <div className="min-h-screen bg-slate-900">
        {/* Desktop Sidebar */}
        {!isMobile && (
          <aside className="fixed right-0 top-0 h-full w-64 bg-slate-900 border-l border-slate-800 z-40">
            <SidebarContent />
          </aside>
        )}

        {/* Mobile Header */}
        {isMobile && (
          <header className="fixed top-0 left-0 right-0 h-16 bg-slate-900/95 backdrop-blur-xl border-b border-slate-800 z-40 flex items-center justify-between px-4">
            <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Menu className="w-6 h-6 text-white" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-64 bg-slate-900 border-slate-800 p-0">
                <SidebarContent />
              </SheetContent>
            </Sheet>

            <div className="flex items-center gap-2">
              <TrendingUp className="w-6 h-6 text-blue-500" />
              <span className="font-bold text-white">Revolution X</span>
            </div>

            <AlertCenter />
          </header>
        )}

        {/* Desktop Header */}
        {!isMobile && (
          <header className="fixed top-0 left-0 right-64 h-16 bg-slate-900/95 backdrop-blur-xl border-b border-slate-800 z-30 flex items-center justify-between px-6">
            <div>
              <h2 className="text-lg font-semibold text-white">
                {sidebarItems.find(item => item.href === pathname)?.label || "لوحة التحكم"}
              </h2>
            </div>
            <div className="flex items-center gap-4">
              <AlertCenter />
              <Button variant="ghost" size="icon">
                <Settings className="w-5 h-5 text-slate-400" />
              </Button>
            </div>
          </header>
        )}

        {/* Main Content */}
        <main
          className={`${
            isMobile ? "pt-20 pb-24 px-4" : "pr-64 pt-20 px-6"
          } min-h-screen`}
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>

        {/* Mobile Bottom Navigation */}
        {isMobile && (
          <nav className="fixed bottom-0 left-0 right-0 h-16 bg-slate-900/95 backdrop-blur-xl border-t border-slate-800 z-40">
            <div className="grid grid-cols-4 h-full">
              {bottomNavItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex flex-col items-center justify-center gap-1 transition-colors ${
                      isActive ? "text-blue-500" : "text-slate-400"
                    }`}
                  >
                    <item.icon className="w-5 h-5" />
                    <span className="text-[10px]">{item.label}</span>
                    {isActive && (
                      <motion.div
                        layoutId="mobileIndicator"
                        className="absolute bottom-1 w-1 h-1 rounded-full bg-blue-500"
                      />
                    )}
                  </Link>
                );
              })}
            </div>
          </nav>
        )}
      </div>
    </ToastProvider>
  );
}
