/* Verdict-message parsing: the sealed message is a single line of
 * semicolon-joined findings ("member: finding; member: finding…").
 * We split it into per-member evidence rows for display — display only,
 * the sealed record stays verbatim (record_hash covers the raw message). */

export interface EvidenceRow {
  member: string;
  bucket?: string;
  finding: string;
  emphasized: boolean;
}

export interface ParsedEvidence {
  summary: string;
  rows: EvidenceRow[];
}

const BUCKET_PREFIX = /^(left_only|right_only|unresolvable|conflicts|excluded):\s*(.*)$/;
const MEMBER_PREFIX = /^([A-Za-z0-9][\w.-]*(?:@[\w.-]+)?):\s+(.*)$/;

/** Findings that should visually pop (the poison the lane exists to catch). */
const EMPHASIS =
  /\(>\s*5\)|9 business day|joins to no identity|cannot be attributed|cannot account for|identity join failed/;

export function parseEvidence(message: string | null): ParsedEvidence {
  if (!message) return { summary: "", rows: [] };
  const segments = message.split(/;\s+/);
  const summaryParts: string[] = [];
  const rows: EvidenceRow[] = [];

  for (const seg of segments) {
    const bucketMatch = seg.match(BUCKET_PREFIX);
    if (bucketMatch) {
      const rest = bucketMatch[2];
      const sp = rest.indexOf(" ");
      const member = sp === -1 ? rest : rest.slice(0, sp);
      const finding = sp === -1 ? "" : rest.slice(sp + 1).trim();
      rows.push({
        member,
        bucket: bucketMatch[1],
        finding,
        emphasized: EMPHASIS.test(seg),
      });
      continue;
    }
    const memberMatch = seg.match(MEMBER_PREFIX);
    if (memberMatch && (memberMatch[1].includes("@") || memberMatch[1].includes("-"))) {
      rows.push({
        member: memberMatch[1],
        finding: memberMatch[2],
        emphasized: EMPHASIS.test(seg),
      });
      continue;
    }
    summaryParts.push(seg);
  }

  return { summary: summaryParts.join("; "), rows };
}
