import { Bricolage_Grotesque } from "next/font/google";

// Display face for the landing page only; the app keeps Geist.
export const displayFont = Bricolage_Grotesque({
  subsets: ["latin"],
  variable: "--font-display",
});
