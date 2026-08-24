import { Inter } from "next/font/google";
import "./globals.css";

// Single family for display, body, and labels — matches the reference's
// Inter Display system rather than the old display/body/mono three-way
// split. Heavy weights (700/800) carry headlines; 400/500/600 carry body
// and UI text.
const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  display: "swap",
});

export const metadata = {
  title: "VeriGrid: Verified hazard reports, crowdsourced",
  description:
    "VeriGrid crowdsources citizen hazard reports, verifies them through independent-reporter consensus, layers in MirEye infrastructure data, and routes confirmed issues to the right authority.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${inter.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-paper text-paper-text font-body">
        {children}
      </body>
    </html>
  );
}
