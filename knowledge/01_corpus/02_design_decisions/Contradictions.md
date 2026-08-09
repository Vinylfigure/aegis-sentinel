# Contradictions

## AWS Identity Store UserStatus API Capabilities

- **Previous Position:** Administrators previously faced a significant limitation where the Identity Store API provided user information but had no way to determine if an account was enabled or disabled.
- **Current/Authoritative Update:** The Identity Store API has been updated to include a UserStatus field (ENABLED, DISABLED, or UNKNOWN) in both ListUsers and DescribeUser responses. This allows for the programmatic audit of account status across an entire organization.
- **Flag:** The official AWS CLI reference is the most authoritative technical source, while the January 2026 source explains the transition from the previous limitation.

## Testing Requirements for External Electronic Information (PCAOB AS 1105.10A)

- **Strict Standard Interpretation:** A literal reading of AS 1105.10A suggests auditors must evaluate the reliability of external electronic information by (a) understanding the source/process and (b) testing the information or controls.
- **Risk-Based Override:** A September 2025 Board Policy Statement clarifies that auditors may not need to perform separate testing if they conclude there is "no more than a remote possibility" that the information was modified in a way that renders it unreliable. If this conclusion is supported, the PCAOB will not treat the absence of separate testing as noncompliance.
- **Flag:** The September 2025 Policy Statement is the more current interpretive authority, overriding a rigid application of the original standard.

## The Evolving Focus of FedRAMP 3PAO Assessments

- **Traditional Approach:** 3PAOs have historically focused on manual evidence review, sampling technology types to validate outputs like screenshots and log exports.
- **New Paradigm (FedRAMP 20x):** Under the FedRAMP 20x model, the 3PAO's role is shifting toward automation validation. Instead of reviewing static outputs, auditors are now tasked with reviewing the automation scripts, control logic (e.g., Terraform or OPA/Rego policies), and the fidelity of continuous monitoring systems.
- **Flag:** The June 2025 source is more current for organizations participating in or aligning with the 20x continuous authorization pilot.

## SOX Data Retention Minimums

- **Operational Perspective:** One source states that SOX-relevant systems require a minimum of 366 days of operational logs to cover one full audit cycle.
- **Legal/Workpaper Perspective:** Another source notes that SOX Section 802 mandates a minimum retention of seven years for audit work papers, financial records, and relevant electronic communications.
- **Flag:** Both are authoritative but serve different purposes: the operational source provides the minimum floor for operational readiness, while the legal source provides the legal compliance ceiling.

## GitHub OAuth Scopes and Private Repository Access

- **Official Documentation:** Official GitHub documentation confirms that the repo scope provides full read and write access to private repositories.
- **Community and Practical Tension:** Users and developers have flagged a major security tension, noting that GitHub does not provide a read-only scope for private repositories. This forces apps that only need to read code to request write permissions, which is described by users as "silly" or "stupid" for security.
- **Flag:** The official documentation is the authoritative technical reference, while the September 2025 source accurately captures the ongoing lack of a more granular read-only alternative.
