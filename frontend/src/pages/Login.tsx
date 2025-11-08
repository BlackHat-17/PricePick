import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { TrendingDown, Loader2, Chrome } from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext"; // ✅ Use Auth Context

const Login = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const { toast } = useToast();

  const { login, googleLogin, isLoading } = useAuth(); // ✅ use from context

  // 🔑 Handle Email/Password Login
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(username, password);
      toast({
        title: "Welcome back!",
        description: "You've successfully logged in.",
      });
    } catch (error: any) {
      toast({
        title: "Login failed",
        description: error.message || "Invalid username or password",
        variant: "destructive",
      });
    }
  };

  // 🔐 Handle Google Login
  const handleGoogleLogin = async () => {
    try {
      await googleLogin();
      toast({
        title: "Welcome!",
        description: "Logged in with Google successfully.",
      });
    } catch (error: any) {
      toast({
        title: "Google Sign-In failed",
        description: error.message || "Something went wrong",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/5 via-accent/5 to-background p-4">
      <Card className="w-full max-w-md p-8">
        <div className="mb-8 text-center">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent mb-4">
            <TrendingDown className="h-6 w-6 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold mb-2">Welcome Back</h1>
          <p className="text-muted-foreground">Sign in to your PricePick account</p>
        </div>

        {/* 🔑 Email Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="username">Username or Email</Label>
            <Input
              id="username"
              type="text"
              placeholder="username or email"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="password">Password</Label>
              <Button variant="link" size="sm" className="px-0 h-auto text-sm" type="button" asChild>
                <NavLink to="/forgot-password">Forgot password?</NavLink>
              </Button>
            </div>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Signing in...
              </>
            ) : (
              "Sign In"
            )}
          </Button>
        </form>

        {/* 🟢 Google Sign-In Button */}
        <div className="mt-4">
          <Button
            type="button"
            variant="outline"
            className="w-full flex items-center justify-center gap-2"
            onClick={handleGoogleLogin}
            disabled={isLoading}
          >
            <Chrome className="h-5 w-5" />
            {isLoading ? "Connecting..." : "Sign in with Google"}
          </Button>
        </div>

        <div className="mt-6 text-center text-sm">
          <span className="text-muted-foreground">Don't have an account? </span>
          <Button variant="link" size="sm" className="px-0 h-auto" asChild>
            <NavLink to="/signup">Sign up</NavLink>
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default Login;
