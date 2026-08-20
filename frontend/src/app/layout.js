import { Space_Grotesk, Inter, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

// Display face: technical, geometric grotesk for headlines — carries the
// "engineering report" personality. Body: Inter for long-form readability.
// Mono: IBM Plex Mono for coordinates, confidence scores, timestamps —
// anything that reads as field data rather than prose.
const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  display: "swap",
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
});

export const metadata = {
  title: "VeriGrid — Verified hazard reports, crowdsourced",
  description:
    "VeriGrid crowdsources citizen hazard reports, verifies them through independent-reporter consensus, layers in MirEye infrastructure data, and routes confirmed issues to the right authority.",
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`${spaceGrotesk.variable} ${inter.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-paper text-paper-text font-body">
        {children}
      </body>
    </html>
  );
}
