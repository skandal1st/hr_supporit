import { Route, Routes } from "react-router-dom";
import { useState, useEffect } from "react";

import { Layout } from "./components/layout/Layout";
import { LoginButton } from "./components/LoginButton";
import { Audit } from "./pages/Audit";
import { Birthdays } from "./pages/Birthdays";
import { HRPanel } from "./pages/HRPanel";
import { OrgChart } from "./pages/OrgChart";
import { Phonebook } from "./pages/Phonebook";

export default function App() {
  const [isAuthed, setIsAuthed] = useState(Boolean(localStorage.getItem("token")));
  const [userRole, setUserRole] = useState<string | null>(null);

  useEffect(() => {
    // Проверяем роль пользователя из токена
    const token = localStorage.getItem("token");
    if (token) {
      try {
        // Простой парсинг JWT (без проверки подписи)
        const payload = JSON.parse(atob(token.split(".")[1]));
        setUserRole(payload.role || null);
      } catch {
        setUserRole(null);
      }
    } else {
      setUserRole(null);
    }
  }, [isAuthed]);

  const handleLogin = () => {
    setIsAuthed(true);
    // Обновим роль после логина
    const token = localStorage.getItem("token");
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        setUserRole(payload.role || null);
      } catch {
        setUserRole(null);
      }
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setIsAuthed(false);
    setUserRole(null);
  };

  // Проверяем, является ли пользователь HR или IT
  const isHRorIT = userRole === "hr" || userRole === "it" || userRole === "admin";

  return (
    <Layout isAuthed={isAuthed} isHRorIT={isHRorIT}>
      <Routes>
        <Route path="/" element={<Phonebook />} />
        <Route path="/birthdays" element={<Birthdays />} />
        {isHRorIT && <Route path="/org" element={<OrgChart />} />}
        {isHRorIT && <Route path="/hr" element={<HRPanel />} />}
        {isHRorIT && <Route path="/audit" element={<Audit />} />}
      </Routes>
      {/* Кнопка логина в нижнем левом углу - видна всем, но только HR/IT могут войти */}
      <LoginButton
        isAuthed={isAuthed}
        onLogin={handleLogin}
        onLogout={handleLogout}
      />
    </Layout>
  );
}
