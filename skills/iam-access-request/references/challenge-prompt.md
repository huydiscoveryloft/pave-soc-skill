# The challenge prompt

`challenge_prompt_md` is a **design record**. It answers one question in as much depth as it can:

> **Why is this policy drafted the way it is?**

A security engineer downloads it, loads it into whatever LLM they use, and then challenges it —
against their own experience of running IAM systems. *"We got burned by exactly that trust policy
in 2023."* *"Nobody scopes Glue that way in practice; here is what breaks."* *"That statement is
fine, but you have missed the one that will page us at 3am."*

**The human brings the challenge. The document brings the reasoning.** The model is only the
vehicle the engineer loads the context into so the back-and-forth is informed.

## What this is not

- **Not a request for a verdict.** It does not ask the model to approve, score, or judge. The
  engineer does that.
- **Not a checklist for an agent to work through.** An earlier version ended with five questions
  aimed at the model, which made it a review task rather than a briefing.
- **Not a summary.** A summary drops the reasoning, and the reasoning is the whole payload. If a
  decision is stated without its "because", the engineer has nothing to push against.

## The rule that makes it work

**Every design decision appears with the reason it was made and the alternative that was
rejected.** A statement in the policy with no recorded "why" is exactly what an experienced
engineer will attack first — and the model will have nothing to say.

If the real reason was thin — a guess, a default, a ticket comment taken at face value — **say
that**. "This prefix is taken verbatim from the ticket and was never verified" is far more useful
to a challenger than a confident-sounding rationalisation.

## Required shape

```markdown
# Why this IAM change is drafted this way — <title>

This document records the reasoning behind a proposed AWS IAM change: what was asked for, what is
being granted, and why each decision was made. It exists so a security engineer can challenge that
reasoning from experience. It is not a verdict, and nothing here should be treated as settled.

Answer the reader's challenges from what is written here. Where the record does not justify a
decision, say so plainly rather than inventing a justification. Where the reader's experience
contradicts the reasoning, that is a finding — record it, do not defend the draft.

## What was asked for
<the original request in the requester's own words, translated if needed, plus the source>
<how it was interpreted, and anything in the ask that was ambiguous>

## What is being granted
Identity: <name> (<role|user>) in the <profile> account (<account id>).

### Permission policy
```json
<the full policy document>
```

### Trust policy
```json
<the full trust policy — omit for an IAM user>
```

## Why it is shaped this way

### Why this identity
<role vs user; new identity vs extending an existing one; which existing identity was considered
and why it did or did not fit; why this account>

### Why each permission is here
<statement by statement, or grouped: what the requester needs to do that requires it, traced back
to the ask. A reader must be able to see the line from "they said they need X" to "hence this
action".>

### Why the resource scoping is what it is
<how each ARN was narrowed. Every `Resource: "*"` named explicitly, with why it was unavoidable —
usually the API has no resource-level support. If it is "*" for convenience, say that instead.>

### What was deliberately left out
<permissions a careless draft would have included, and the reason each was excluded>

### What was assumed
<every assumption, what it rests on, and what would change in the policy if it turned out wrong>

## Where this lives
<the account, what else runs in it, which accounts it can and cannot reach, any cross-account
trust that bears on this request. Enough that a question about reach or blast radius can be
answered.>

## What is not yet known
<each placeholder, what it stands for, and what discovery would resolve it — or "none">
<anything the record is genuinely weak on, stated as such>

## How this was checked
<which AWS documentation was consulted and what it confirmed — action names, whether an action
supports resource-level permissions. If the tooling was unavailable, say so plainly.>

## Comparable setups found
<the write-ups stored in reference_links_json, each with what it shows and how it differs from
this draft — or "searched and found nothing comparable">

```

## Notes

- **Weak reasoning must look weak.** Do not upgrade "the ticket said so" into "per the documented
  requirement". The engineer is trying to find the soft spots; hiding them wastes the session.
- **Include the estate context.** Questions about reach and blast radius are common and cannot be
  answered without knowing which account this sits in and what it can talk to.
- **Placeholders are fine, silence is not.** A record whose ARNs are still `<PLACEHOLDER>` is
  worth challenging on shape and scope, but it has to say that is what it is.
- **Comparable setups are for comparison, not authority.** Another team's policy is evidence of
  what is normal, not proof of what is correct — plenty of published walkthroughs attach
  `AmazonS3ReadOnlyAccess` where a scoped policy belongs. The `note` on each link should say how
  it differs from this draft, which is exactly what a reviewer wants to argue with.
- **Every link was opened before it was stored.** A search result that looks perfect can contain
  no IAM detail at all, and URLs move — Google Cloud's documentation, for instance, now lives on
  `docs.cloud.google.com`. A dead or irrelevant link in a security review is worse than none.
- **Length is not the constraint, completeness of reasoning is** — but every paragraph should be
  one whose absence would leave a decision unexplained.
