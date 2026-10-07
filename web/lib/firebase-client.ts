import { initializeApp, getApps, getApp } from "firebase/app";
import { connectAuthEmulator, getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
};

const app = getApps().length ? getApp() : initializeApp(firebaseConfig);

export const auth = getAuth(app);

const emulatorUrl = process.env.NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL;
// ponytail: try/catch guards against Fast Refresh re-running this module and
// calling connectAuthEmulator twice on the same auth instance, which throws.
if (emulatorUrl) {
  try {
    connectAuthEmulator(auth, emulatorUrl, { disableWarnings: true });
  } catch {
    // already connected
  }
}
