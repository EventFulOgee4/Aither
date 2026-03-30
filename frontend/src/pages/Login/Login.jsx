import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, register } from "../../api/auth";
import "./login.css";

export default function LoginPage() {
  const nav = useNavigate();
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [username, setUsername] = useState("");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm]   = useState("");
  const [loading, setLoading]   = useState(false);
  const [err, setErr]           = useState("");

  function switchMode(m) {
    setMode(m);
    setErr("");
    setUsername("");
    setEmail("");
    setPassword("");
    setConfirm("");
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setErr("");

    if (mode === "register") {
      if (password !== confirm) {
        setErr("Passwords don't match.");
        return;
      }
      if (password.length < 6) {
        setErr("Password must be at least 6 characters.");
        return;
      }
    }

    setLoading(true);
    try {
      if (mode === "login") {
        await login(username.trim(), password);
      } else {
        await register(username.trim(), email.trim(), password);
      }
      nav("/");
    } catch (e) {
      if (mode === "login") {
        setErr("Login failed. Check your username and password.");
      } else {
        setErr("Registration failed. Username or email may already be taken.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-root">
      <div className="login-orb-bg" />

      <div className="login-card">
        {/* Header */}
        <div className="login-header">
          <div className="login-orb" />
          <div>
            <div className="login-logo-text">Aither</div>
            <div className="login-tagline">Your reflective companion</div>
          </div>
        </div>

        {/* Mode toggle */}
        <div className="login-tabs">
          <button
            className={`login-tab ${mode === "login" ? "active" : ""}`}
            type="button"
            onClick={() => switchMode("login")}
          >
            Sign in
          </button>
          <button
            className={`login-tab ${mode === "register" ? "active" : ""}`}
            type="button"
            onClick={() => switchMode("register")}
          >
            Create account
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="login-form">
          <div className="login-field">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
              autoComplete="username"
              required
            />
          </div>

          {mode === "register" && (
            <div className="login-field">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>
          )}

          <div className="login-field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              placeholder={mode === "register" ? "Min. 6 characters" : "Enter your password"}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              required
            />
          </div>

          {mode === "register" && (
            <div className="login-field">
              <label htmlFor="confirm">Confirm password</label>
              <input
                id="confirm"
                placeholder="Repeat your password"
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>
          )}

          <button className="login-submit" type="submit" disabled={loading}>
            {loading
              ? mode === "login" ? "Signing in…" : "Creating account…"
              : mode === "login" ? "Continue" : "Create account"
            }
          </button>
        </form>

        {err && (
          <div className="login-error">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.8"/>
              <path d="M12 8v4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              <circle cx="12" cy="16" r="1" fill="currentColor"/>
            </svg>
            {err}
          </div>
        )}

        {mode === "login" && (
          <div className="login-hint">
            Don't have an account?{" "}
            <button
              className="login-hint-link"
              type="button"
              onClick={() => switchMode("register")}
            >
              Create one free
            </button>
          </div>
        )}
      </div>
    </div>
  );
}