// src/services/register.ts
import { createUserWithEmailAndPassword } from "firebase/auth";
import { ref, set } from "firebase/database";
import { auth, db } from "@/services/firebase/firebase";

export const register = async (username: string, email: string, password: string) => {
  try {
    // Create a new user with email/password
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;

    // Save user data securely in their own node
    await set(ref(db, `users/${user.uid}`), {
      username,
      email,
      createdAt: new Date().toISOString(),
    });

    return user;
  } catch (error: any) {
    console.error("Register error:", error);
    throw error;
  }
};
