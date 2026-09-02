import type { Metadata } from "next";
import LegalShell from "@/components/LegalShell";
import { privacyEn, privacyVi } from "./content";

export const metadata: Metadata = {
  title: "Privacy Notice | Uphill AI",
  description:
    "How Uphill AI collects, uses, retains and deletes your personal data, including data from connected device accounts and our use of artificial intelligence.",
};

export default function PrivacyPage() {
  return <LegalShell en={privacyEn} vi={privacyVi} />;
}
