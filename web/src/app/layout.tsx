import type { Metadata } from "next";
import { IBM_Plex_Mono, Inter, Space_Grotesk } from "next/font/google";
import "@/styles/tokens.css";
import "@/styles/globals.css";
import RailNav from "@/components/shell/RailNav";
import { loadEngagement } from "@/lib/data/engagement";

const grotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "700"],
  variable: "--font-grotesk",
});
const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-inter",
});
const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "Aegis — Termination Lane",
  description:
    "Aegis · the lane is the product — compiled proof painted onto the process flow",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const { artifacts } = loadEngagement();
  return (
    <html
      lang="en"
      className={`${grotesk.variable} ${inter.variable} ${plexMono.variable}`}
    >
      <body>
        <RailNav manifestVersion={artifacts.manifest.manifest_version} />
        <div className="frame">{children}</div>
      </body>
    </html>
  );
}
