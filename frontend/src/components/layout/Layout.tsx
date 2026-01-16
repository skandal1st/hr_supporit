import type { ReactNode } from "react";

import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

type LayoutProps = {
  children: ReactNode;
};

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Sidebar />
      <div className="lg:pl-64">
        <Header />
        <main className="p-4 lg:p-6">{children}</main>
      </div>
    </div>
  );
}
