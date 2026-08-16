import type { Metadata } from "next";
import { StubPage } from "@/components/StubPage/StubPage";

export const metadata: Metadata = { title: "Registry" };

export default function RegistryPage() {
  return (
    <StubPage
      title="Capability registry"
      plannedIn="B3"
      description="Capability entries with lifecycle state, and E-codes rendered as compiler errors. REQUIRED (see web/README.md): this page MUST render registry.json's top-level DEMO-ONLY note and every entry's DRAFT caveats verbatim — omitting them misrepresents ratification state."
    />
  );
}
