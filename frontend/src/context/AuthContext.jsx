import { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("qy_user");
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {}
    }
    setLoading(false);
  }, []);

  const login = (email, password) => {
    // Simulate API auth — accept any non-empty credentials
    if (!email || !password)
      return { ok: false, error: "Email and password required" };
    const userData = {
      id: "usr_001",
      name: email
        .split("@")[0]
        .replace(/[._]/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase()),
      email,
      role: "Portfolio Manager",
      initials: email.slice(0, 2).toUpperCase(),
      plan: "Enterprise",
    };
    setUser(userData);
    localStorage.setItem("qy_user", JSON.stringify(userData));
    return { ok: true };
  };

  const register = (data) => {
    if (!data.name || !data.email || !data.password)
      return { ok: false, error: "All fields required" };
    if (data.password.length < 8)
      return { ok: false, error: "Password must be at least 8 characters" };
    const userData = {
      id: "usr_" + Math.random().toString(36).slice(2, 7),
      name: data.name,
      email: data.email,
      role: "Analyst",
      initials: data.name.slice(0, 2).toUpperCase(),
      plan: "Pro",
    };
    setUser(userData);
    localStorage.setItem("qy_user", JSON.stringify(userData));
    return { ok: true };
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("qy_user");
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
