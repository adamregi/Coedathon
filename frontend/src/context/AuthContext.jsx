import { createContext, useContext, useState, useEffect } from "react";
import { authApi } from "../services/api";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("user");
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [loading, setLoading] = useState(true);

  // Restore authenticated session on mount
  useEffect(() => {
    async function rehydrateUser() {
      const token = localStorage.getItem("access_token");
      if (token) {
        try {
          const me = await authApi.getMe();
          setUser(me);
          localStorage.setItem("user", JSON.stringify(me));
        } catch (err) {
          console.warn("Session restore failed, clearing token", err);
          localStorage.removeItem("user");
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          setUser(null);
        }
      }
      setLoading(false);
    }
    rehydrateUser();
  }, []);

  // Real backend Login
  const login = async (email, password) => {
    if (!email || !password) {
      return { success: false, message: "Email and password are required" };
    }
    try {
      const tokenData = await authApi.login(email, password);
      localStorage.setItem("access_token", tokenData.access_token);
      if (tokenData.refresh_token) {
        localStorage.setItem("refresh_token", tokenData.refresh_token);
      }

      // Fetch user identity
      const me = await authApi.getMe();
      setUser(me);
      localStorage.setItem("user", JSON.stringify(me));

      return { success: true, user: me };
    } catch (err) {
      return { success: false, message: err.message || "Invalid credentials" };
    }
  };

  // Real backend Signup
  const signup = async ({ email, password, full_name, role }) => {
    if (!email || !password || !full_name) {
      return { success: false, message: "Please fill in all required fields" };
    }
    try {
      await authApi.register({ email, password, full_name, role: role || "student" });
      // Immediately log the user in after registration
      return await login(email, password);
    } catch (err) {
      return { success: false, message: err.message || "Registration failed" };
    }
  };

  const logout = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        signup,
        logout,
        isAuthenticated: !!user,
        isEmployer: user?.role === "employer" || user?.role === "admin",
        isAdmin: user?.role === "admin",
      }}
    >
      {!loading && children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
