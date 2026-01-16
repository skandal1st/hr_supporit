import { Route, Routes } from "react-router-dom";
import { useState } from "react";

import { login } from "./api/client";
import { Layout } from "./components/layout/Layout";
import { Audit } from "./pages/Audit";
import { Birthdays } from "./pages/Birthdays";
import { HRPanel } from "./pages/HRPanel";
import { OrgChart } from "./pages/OrgChart";
import { Phonebook } from "./pages/Phonebook";

export default function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isAuthed, setIsAuthed] = useState(Boolean(localStorage.getItem("token")));

  const handleLogin = async () => {
    try {
      await login(username, password);
      setIsAuthed(true);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setIsAuthed(false);
  };

  return (
    <Layout>
      <div className="mb-4">
        {isAuthed ? (
          <button
            onClick={handleLogout}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg"
          >
            Выйти
          </button>
        ) : (
          <div className="flex flex-wrap items-center gap-2">
            <input
              className="px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm"
              placeholder="Логин"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
            />
            <input
              className="px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-sm"
              placeholder="Пароль"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <button
              onClick={handleLogin}
              className="px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg"
            >
              Войти
            </button>
            {error && <span className="text-sm text-red-600">{error}</span>}
          </div>
        )}
      </div>
      <Routes>
        <Route path="/" element={<Phonebook />} />
        <Route path="/birthdays" element={<Birthdays />} />
        <Route path="/org" element={<OrgChart />} />
        <Route path="/hr" element={<HRPanel />} />
        <Route path="/audit" element={<Audit />} />
      </Routes>
    </Layout>
  );
}
