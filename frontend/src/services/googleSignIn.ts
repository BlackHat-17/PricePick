// src/services/googleSignIn.ts
import { signInWithPopup, GoogleAuthProvider } from "firebase/auth";
import { ref, set, get, child } from "firebase/database";
import { auth, db } from "@/services/firebase/firebase";

const provider = new GoogleAuthProvider();

export const googleSignIn = async () => {
  try {
    // 🟢 Sign in with Google popup
    const result = await signInWithPopup(auth, provider);
    const user = result.user;

    // 🔍 Check if user already exists in Realtime DB
    const userRef = ref(db, `users/${user.uid}`);
    const snapshot = await get(child(ref(db), `users/${user.uid}`));

    // 💾 If new user, save to Realtime DB
    if (!snapshot.exists()) {
      await set(userRef, {
        username: user.displayName || "Google User",
        email: user.email,
        createdAt: new Date().toISOString(),
        provider: "google",
      });
    }

    console.log("✅ Google sign-in successful:", user);
    return user;
  } catch (error: any) {
    console.error("❌ Google sign-in error:", error.message);
    throw error;
  }
};
