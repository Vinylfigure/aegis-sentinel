# Methodology review — external critiques vs. primary sources (2026-07-24)

Two external reviews of Janus's methodology (Grok; ChatGPT "Sol") were
challenged against anthropic.com/research, claude.com/blog, the engineering
blog, and the Claude Code docs. Every quote below was exact-string verified
in the main thread this session — including one raw-HTML fetch after a
delegated verifier produced a false refutation (see Evidence hygiene).
Verdicts drove the revision set at the bottom; the rejected recommendations
are listed with reasons, because a rejection without a reason is just taste.

Method note: the anthropic.com/research index for Mar–Jul 2026 contains
nothing on agent memory, continual learning, or harnesses — the
methodology-relevant primary sources are the engineering blog, claude.com/blog,
and the docs. "Leverage the research" in practice means one interpretability
paper plus product guidance.

## Verdicts on Sol (ChatGPT)

| # | Claim | Verdict | Decisive evidence |
|---|---|---|---|
| 1 | "Evidence: 2 is not meaningful evidence" | **Adapt.** Threshold fine; independence guard was missing | The curator brief literally said to merge near-duplicates by "summing their Evidence" — two unrelated anecdotes could manufacture a promotable 2. Nothing anywhere defined "recurrence" or barred same-session double-bumps. Fixed as discipline (see revisions); Sol's structured-evidence YAML rejected. |
| 2 | "The system evaluates itself with the same model" | **Mostly reject** | The human gate on every CLAUDE.md change is exactly Anthropic's prescription: "Keep CLAUDE.md under 200 lines, give it an owner, and review changes to it like code" ([Steering Claude Code](https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more), 2026-06-18). The docs table says CLAUDE.md "Who writes it: You". The gate is load-bearing; the answer to same-model risk is the gate plus external evidence preference, not independence theater. |
| 3 | "No outcome evaluation exists" | **Adopt — strongest surviving point** | True: the loop counted compliance (budget assertions, claims-checked tallies), never outcomes, and retirement fired only on contradiction — a useless rule had no path out. Anthropic: "you should consider adding complexity _only_ when it demonstrably improves outcomes" ([building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents)); "Teams without evals get bogged down in reactive loops—fixing one failure, creating another, unable to distinguish real regressions from noise" ([demystifying-evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)). And Anthropic's own instruction-budget change was justified by evals, not reflection: "over 80% of Claude Code's system prompt" removed "with no measurable loss on our coding evaluations". |
| 4 | "The 20-concept cap is too literally derived" | **Adopt (docs corrected)** | The paper *chooses* its number: "we typically choose it to be no more than 25, which we empirically observed to be the number of J-lens vectors that are meaningfully active at a given time" — a lens hyperparameter, from a lens the paper calls "an imperfect tool", covering under 10% of activation variance and single-token concepts only. The paper contains no "~10–25" range (ARCHITECTURE.md previously asserted one) and says nothing about prompts or instruction files. The cap survives on operational grounds: "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence" ([memory docs](https://code.claude.com/docs/en/memory)). |
| 5 | "Persistent-memory poisoning is under-addressed" | **Adopt** | Repo-wide grep for untrusted/poison/injection/source-trust: zero hits, while the ledger→CLAUDE.md→/replicate pipeline is a generational persistence channel. Anthropic names it exactly: "The share of agent context that persists across sessions keeps growing—this includes product memory, CLAUDE.md files, mounted workspaces, and the state directories of scheduled and long-running agents." / "An injection that lands in any of these is reloaded each time the agent starts." / "Tool output is an attack surface even when the tool is trusted." ([how-we-contain-claude](https://www.anthropic.com/engineering/how-we-contain-claude)). Sol's trust-metadata schema rejected; trust-boundary discipline adopted. |
| 6 | "False positives are harmless — not quite" | **Adapt** | Correction signals carried only a timestamp; this very session a leftover signal fired the Stop hook and its cause could only be guessed. Signal lines now carry the matched keyword and a prompt excerpt. Sol's classifier-improvement program rejected — the transcript pass stays primary. |
| 7 | "Append-only ledger becomes an unbounded liability" | **Reject, with watch item** | The repo ran this experiment in reverse: commit 71bbe49 deleted ARCHIVE.md because it "solved a problem zero sessions had demonstrated". At 29 entries the pain Sol predicts has not occurred; his 4-file split re-proposes the reverted mistake. Revisit on demonstrated pain, not prediction. |
| 8 | "Grep dedup is too weak" | **Adapt** | True, but the scale-appropriate fix is reading all entry titles (cheap at 29) plus an explicit disposition per cluster — duplicate / refinement / contradiction / independent. Embedding pipelines rejected at this scale. |
| 9 | "Portability is dangerously broad" | **Adapt** | The census was damning: 29/29 entries `Scope: portable`, zero `project`. Fixed as discipline (default-to-project unless provably repo-independent) plus a human review gate at `/replicate` for the rules that arrive active. Sol's applicability-taxonomy YAML rejected. |
| 10 | "Verification can optimize for the wrong thing" | **Partially adopt** | The verifier already demands a counterfactual before PASS. The real finding underneath: un-bootstrapped `verify.sh quick` is a no-op for `.md` files — all of the template's own substantive work — so the verify-fail signal channel is dead in this repo. Stated honestly here; the `full` arm and CI carry the load until `/bootstrap`. |

## Verdicts on Grok

| Claim | Verdict |
|---|---|
| "Hard capacity limits derived from interpretability work (~10–25 active concepts)... rare and correct" | **Challenged.** The derivation was the methodology's weakest claim, not its strength — see Sol #4. Grok took the repo's framing at face value; the "~10–25" range appears in no primary source. |
| "Staleness is tracked via committed epoch files so it survives clones and cloud runs" | **Challenged.** The mechanism exists, but the stamp on disk was written by the design commit, never by a run (L-020) — a false green Grok read as working machinery. The stamp is now deleted; only a real `/recalibrate` run may write one. |
| "Skill descriptions capped ≤50 words" | **Confirmed** (`add-skill/SKILL.md`). |
| Ceremony overhead; loops depend on the user running them; unproven at scale | **Conceded.** Converges with Sol #3 — the efficacy discipline below is the first answer; a real evaluation waits for a bootstrapped child with task history. |

## Where the sources cut FOR the methodology

- Anthropic's own SDLC describes the session loop's shape in production:
  "Once an agent discovers a bug class, the relevant file is updated to
  prevent it recurring in future code." and guidelines "encoded in CLAUDE.md
  files and references to org-wide skills so the code follows these best
  practices the minute it's generated."
  ([SDLC post](https://claude.com/blog/how-anthropic-secures-its-ai-native-software-development-lifecycle);
  who performs the update is not stated — the human gate remains Janus's answer).
- Agentic note-taking is endorsed: "Structured note-taking, or agentic
  memory, is a technique where the agent regularly writes notes persisted to
  memory outside of the context window."
  ([effective-context-engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)) —
  the endorsed shape (bounded, separate from the rules file, human-owned
  top-level) is the shape Janus already has.
- Recalibration matches: "harnesses encode assumptions about what Claude
  can't do on its own. However, those assumptions need to be frequently
  questioned because they can go stale as models improve."
  ([managed-agents](https://www.anthropic.com/engineering/managed-agents)).

## Evidence hygiene (what this review itself demonstrated)

A delegated research agent reported two Anthropic quotes as fabrications
after exact-string re-fetches failed. Main-thread raw-HTML verification
showed **both sentences are real** — the "absence" was an artifact of
matching a full sentence with terminal punctuation against text that
continues past the claimed ending ("...prevent it recurring **in future
code**."). The refutation, not the quote, was the false claim. Rules this
teaches: a refutation is a claim requiring the same verification rigor as
the claim it refutes, and absence checks must match substrings, never
punctuation-terminated sentences. Neither external critic verbatim-verified
their citations; the repo's L-005 discipline caught what both missed — in
both directions.

## Rejected recommendations, with reasons

| Recommendation (Sol) | Reason rejected |
|---|---|
| Structured YAML evidence bundles per entry | Mechanism for a problem discipline solves; L-014 requires dogfooded need first. Prose Trigger lines already carry provenance. |
| 4-file ledger split (log/active/index/archive) | Re-proposes the ARCHIVE.md design deleted in 71bbe49 on the repo's own evidence rules. |
| Semantic/embedding dedup pipeline | 29 entries; titles fit on one screen. Revisit if grep+titles demonstrably misses. |
| Trust-metadata YAML block per source | Adopted as one sentence of discipline instead: untrusted-origin evidence cannot promote without explicit human confirmation. |
| Scope taxonomy with applicability predicates | Adopted as default-to-project discipline plus the replicate review gate instead. |
| Full baseline-vs-Janus eval suite now | The template is un-bootstrapped: there are no real coding tasks to measure. Filed as a designed-but-deferred ledger candidate with an explicit re-open trigger (first bootstrapped child with task history). Deferred is not rejected. |

## Revisions applied this round

1. Evidence integrity: recurrence defined (distinct incident, separate
   session or task; one bump per session), merges take the max never the
   sum, dispositions named per cluster.
2. Trust boundaries: Trigger lines name their evidence origin class;
   untrusted-origin entries need explicit human confirmation to promote,
   regardless of count.
3. Efficacy accounting: `/reflect` notes when a promoted rule visibly fired
   or failed to help; `/evolve` proposes retirement for promoted rules with
   no observed effect — retirement no longer requires contradiction.
4. Inheritance gate: rules copied active into a child require the user's
   explicit yes per rule at `/replicate` time; scope defaults to `project`.
5. Research grounding rewritten (ARCHITECTURE.md): caps re-grounded on
   docs guidance and dogfooding; the workspace paper demoted to convergent
   context with its limitations quoted.
6. Correction signals carry keyword + excerpt; the false-green
   recalibration stamp deleted.
