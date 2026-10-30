import { useState } from "react";
import { api } from "../api";

const ROLES = ["Developer", "QA", "Manager"];

const ROLE_HINTS = {
  Developer: "Works on tasks and moves them forward.",
  QA: "Reviews work. The only role that can mark a task Done.",
  Manager: "Plans the work and keeps the team organised.",
};

const FEATURES = [
  "Track every task from To Do to Done",
  "Assign work and see who owns what",
  "QA sign-off keeps finished work honest",
  "A full history of who changed what, and when",
];

export default function AuthPage({ onAuth, message }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "Developer" });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const signingUp = mode === "signup";

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function switchMode(next) {
    setMode(next);
    setError("");
  }

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const result = signingUp
        ? await api.signup(form)
        : await api.login({ email: form.email, password: form.password });
      onAuth(result);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <div className="auth">
      <section className="auth-hero">
        <div className="brand">
          <span className="brand-mark">M</span>
          <span className="brand-name">Mini-Jira</span>
        </div>
        <h1>Plan the work. Own the work. Finish the work.</h1>
        <ul>
          {FEATURES.map((feature) => (
            <li key={feature}>{feature}</li>
          ))}
        </ul>
      </section>

      <section className="auth-panel">
        <div className="auth-card">
          <div className="tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={!signingUp}
              className={!signingUp ? "tab active" : "tab"}
              onClick={() => switchMode("login")}
            >
              Log in
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={signingUp}
              className={signingUp ? "tab active" : "tab"}
              onClick={() => switchMode("signup")}
            >
              Sign up
            </button>
          </div>

          <h2>{signingUp ? "Create your account" : "Welcome back"}</h2>
          <p className="muted">
            {signingUp ? "Join your team in a few seconds." : "Log in to see your team's board."}
          </p>

          {message && !error && <div className="banner info">{message}</div>}
          {error && (
            <div className="banner error" role="alert">
              {error}
            </div>
          )}

          <form onSubmit={submit} className="stack">
            {signingUp && (
              <label className="field">
                Full name
                <input
                  value={form.name}
                  onChange={(e) => update("name", e.target.value)}
                  placeholder="Asha Rao"
                  maxLength={100}
                  autoComplete="name"
                  required
                />
              </label>
            )}

            <label className="field">
              Email
              <input
                type="email"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                placeholder="you@company.com"
                autoComplete="email"
                required
              />
            </label>

            <label className="field">
              Password
              <div className="password-row">
                <input
                  type={showPassword ? "text" : "password"}
                  value={form.password}
                  onChange={(e) => update("password", e.target.value)}
                  placeholder={signingUp ? "At least 8 characters" : "Your password"}
                  minLength={signingUp ? 8 : undefined}
                  maxLength={128}
                  autoComplete={signingUp ? "new-password" : "current-password"}
                  required
                />
                <button
                  type="button"
                  className="ghost small"
                  onClick={() => setShowPassword((shown) => !shown)}
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </label>

            {signingUp && (
              <label className="field">
                Role
                <select value={form.role} onChange={(e) => update("role", e.target.value)}>
                  {ROLES.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
                <span className="hint">{ROLE_HINTS[form.role]}</span>
              </label>
            )}

            <button type="submit" className="primary wide" disabled={busy}>
              {busy ? "Please wait..." : signingUp ? "Create account" : "Log in"}
            </button>
          </form>

          <p className="switch">
            {signingUp ? "Already have an account?" : "New here?"}{" "}
            <button type="button" className="link" onClick={() => switchMode(signingUp ? "login" : "signup")}>
              {signingUp ? "Log in" : "Create an account"}
            </button>
          </p>
        </div>
      </section>
    </div>
  );
}
