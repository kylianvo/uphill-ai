import type { Metadata } from "next";
import LegalShell from "@/components/LegalShell";
import { supportEn, supportVi } from "./content";

export const metadata: Metadata = {
  title: "Support | Uphill AI",
  description:
    "Get help with Uphill AI: your account, connecting and disconnecting a device account, activity sync, workout delivery, and data requests.",
};

export default function SupportPage() {
  return <LegalShell en={supportEn} vi={supportVi} />;
}
