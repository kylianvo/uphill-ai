import type { Metadata } from "next";
import { Outfit, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Uphill AI | Science-Backed Trail & Mountain Coaching",
  description:
    "Personalized AI running coach combining Training for the Uphill Athlete principles, 80/20 intensity, and precision fueling. Upload your GPX, plan your race, and get coached.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${outfit.variable} ${jetbrainsMono.variable}`}
    >
      <head>
        {/* Fustat from Google Fonts — used for massive display headers */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fustat:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
        {/* Google Sign-In SDK */}
        <script src="https://accounts.google.com/gsi/client" async defer></script>
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
