"""D7 (`docs/DECISIONS.md`): the Cartographer's documentation-source
allowlist — a source is allowed iff it is the vendor's own first-party
documentation domain. Pure and deterministic; no network access, so this
module carries none of the "cannot probe" risk by construction."""

SOURCE_UNREACHABLE = "source_unreachable"

# D7 rule 1: allowed iff vendor first-party doc domain. A source is a
# (domain, required_path_prefix) pair; an empty prefix scopes the whole
# domain, a non-empty one scopes only matching paths -- ruled this way for
# Slack specifically, where slack.com also carries marketing/legal/pricing
# pages that are not documentation ("Slack -> api.slack.com and
# slack.com/help", D7 ruling verbatim). Workday carries no entry (D7 rule
# 2) -- its documentation sits behind Community authentication a sandboxed
# session cannot reach, so every Workday citation is treated as outside the
# allowlist until the Owner supplies cited excerpts directly.
ALLOWED_DOC_SOURCES: dict[str, tuple[tuple[str, str], ...]] = {
    "github": (("docs.github.com", ""),),
    "gcp": (("cloud.google.com", ""),),
    "okta": (("help.okta.com", ""), ("developer.okta.com", "")),
    "slack": (("api.slack.com", ""), ("slack.com", "/help")),
}


def _domain_and_path(citation: str) -> tuple[str, str]:
    """(netloc, path) of a URL, without a URL-parsing library (`urllib`/
    `http` are purity-gate-banned everywhere under `src/aegis_sentinel/` —
    see `scripts/check_purity.py` — this module has no network need of its
    own). Path is `""` when the citation names no path at all (bare
    domain), so it never satisfies a non-empty required prefix."""
    rest = citation.split("://", 1)[-1]
    domain, sep, after = rest.partition("/")
    domain = domain.split("@")[-1].split(":")[0].lower()
    path = ("/" + after) if sep else ""
    return domain, path


def is_allowed_citation(system: str, citation: str) -> bool:
    """D7 rule 1 (+ rule 2's Workday exception): does `citation` sit on one
    of `system`'s vendor first-party documentation domains, under whatever
    path scope that source was ruled to (Slack's `/help`)?"""
    domain, path = _domain_and_path(citation)
    for allowed_domain, required_prefix in ALLOWED_DOC_SOURCES.get(system, ()):
        if domain == allowed_domain or domain.endswith("." + allowed_domain):
            if not required_prefix or path.startswith(required_prefix):
                return True
    return False
