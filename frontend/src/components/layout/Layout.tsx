import type { ReactNode } from "react";

import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

type LayoutProps = {
  children: ReactNode;
  isAuthed?: boolean;
  isHRorIT?: boolean;
};

export function Layout({ children, isAuthed = false, isHRorIT = false }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Sidebar isAuthed={isAuthed} isHRorIT={isHRorIT} />
      <div className="lg:pl-64">
        <Header />
        <main className="p-4 lg:p-6">{children}</main>
      </div>
    </div>
  );
}
