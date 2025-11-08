// src/services/login.ts
import { signInWithEmailAndPassword } from "firebase/auth";
import { ref, get } from "firebase/database";
import { auth, db } from "@/services/firebase/firebase";

export const login = async (email: string, password: string) => {
  try {
    // Authenticate user
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;

    // Read that user’s own data (secure path)
    const userRef = ref(db, `users/${user.uid}`);
    const snapshot = await get(userRef);

    if (snapshot.exists()) {
      return { user, data: snapshot.val() };
    } else {
      console.warn("No user data found in database.");
      return { user, data: null };
    }
  } catch (error: any) {
    console.error("Login error:", error);
    throw error;
  }
};
