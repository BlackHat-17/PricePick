/**
 * Authentication Context (Firebase)
 * Manages Firebase user state and provides login/register/logout methods
 */

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { onAuthStateChanged, signOut, User as FirebaseUser } from "firebase/auth";
import { auth } from "@/services/firebase/firebase";
import { login as loginService } from "@/services/login";
import { googleSignIn as googleLoginService } from "@/services/googleSignin";
import { register as registerService } from "@/services/register";
import { useNavigate } from "react-router-dom";

interface AuthContextType {
  user: FirebaseUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  googleLogin: () => Promise<void>; // ✅ added
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<FirebaseUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  // 🔄 Listen to Firebase auth changes
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser);
      setIsLoading(false);
    });
    return () => unsubscribe();
  }, []);

  // 🔑 LOGIN (email/password)
  const handleLogin = async (email: string, password: string) => {
    try {
      await loginService(email, password);
      navigate("/dashboard");
    } catch (error) {
      console.error("❌ Login failed:", error);
      throw error;
    }
  };

  // 🆕 REGISTER
  const handleRegister = async (email: string, password: string, name: string) => {
    try {
      await registerService(email, password, name);
      navigate("/dashboard");
    } catch (error) {
      console.error("❌ Registration failed:", error);
      throw error;
    }
  };

  // 🔐 GOOGLE LOGIN
  const handleGoogleLogin = async () => {
    try {
      setIsLoading(true);
      await googleLoginService();
      navigate("/dashboard");
    } catch (error) {
      console.error("❌ Google Sign-In failed:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // 🚪 LOGOUT
  const logout = async () => {
    await signOut(auth);
    setUser(null);
    navigate("/login");
  };

  // 🔁 REFRESH USER
  const refreshUser = async () => {
    if (auth.currentUser) {
      await auth.currentUser.reload();
      setUser(auth.currentUser);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login: handleLogin,
        register: handleRegister,
        googleLogin: handleGoogleLogin, // ✅ new
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
