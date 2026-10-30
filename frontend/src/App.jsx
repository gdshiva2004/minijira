import { useEffect, useState } from "react";
import { api, clearToken, getToken, onUnauthorized, setToken } from "./api";
import AuthPage from "./components/AuthPage";
import Dashboard from "./Dashboard";

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(Boolean(getToken()));
  const [sessionMessage, setSessionMessage] = useState("");

  useEffect(() => {
    onUnauthorized(() => {
      clearToken();
      setUser(null);
      setSessionMessage("Your session has expired. Please log in again.");
    });
    if (!getToken()) return;
    api
      .me()
      .then(setUser)
      .catch(() => {})
      .finally(() => setChecking(false));
  }, []);

  function handleAuth(result) {
    setToken(result.token);
    setSessionMessage("");
    setUser(result.member);
  }

  function logout() {
    clearToken();
    setSessionMessage("");
    setUser(null);
  }

  if (checking) {
    return (
      <div className="splash">
        <div className="spinner" />
      </div>
    );
  }

  if (!user) {
    return <AuthPage onAuth={handleAuth} message={sessionMessage} />;
  }

  return <Dashboard user={user} onLogout={logout} />;
}
