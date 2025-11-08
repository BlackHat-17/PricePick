// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getDatabase } from "firebase/database";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyDT56IR2hrxDrnGS3KhWphu29lT9wOF8yg",
  authDomain: "pricepick-ecab5.firebaseapp.com",
  databaseURL: "https://pricepick-ecab5-default-rtdb.firebaseio.com",
  projectId: "pricepick-ecab5",
  storageBucket: "pricepick-ecab5.firebasestorage.app",
  messagingSenderId: "1073108387100",
  appId: "1:1073108387100:web:eb37dc8bf74ebee420a6d9",
  measurementId: "G-MPX2ZWLNYK"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getDatabase(app);
