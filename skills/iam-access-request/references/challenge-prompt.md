# The challenge prompt

`challenge_prompt_md` is a **portable context bundle**. A reviewer downloads it from the dashboard
and hands it to whatever LLM they trust, which then has to answer questions about the request:

> *Can this role reach production?*
> *If the access key leaks, what is the blast radius?*
> *Could the holder escalate from here?*
> *What could it read that nobody asked for?*

**It is a briefing, not a verdict request.** The earlier version asked for an opinion in one shot;
this one hands over enough context that a reviewer can interrogate the design. That difference
drives everything below.

## Three properties it must have

**1. Self-contained.** The reading model sees this text and nothing else — no repo, no ticket, no
AWS access, no conversation. Anything it needs to reason with has to be inline.

**2. Enough estate context to answer a blast-radius question.** This is what the old prompt
lacked. "Can this reach production?" is unanswerable without knowing which account the identity
lives in, what else lives there, and what trusts what. Include the relevant slice of
`system-facts.md` — not the whole file, the parts that bear on *this* request.

**3. Neutral.** Do not tell the model the policy is least-privilege. That is the question, not the
premise. State what was drafted and why; let the reader disagree.

## Required shape

```markdown
# Challenge briefing — <title>

You are being handed a proposed AWS IAM change to examine. Everything you need is in this
document; you have no access to the AWS account and should not assume any fact that is not
written here. Answer the reader's questions directly, and say plainly when the document does not
contain enough to answer.

## The request
<the original ask in the requester's own words, translated to English if needed>
Source: <Jira key or Slack thread>. Requester: <name>.

## What is proposed
Identity: <name> (<role|user>) in the <profile> account (<account id>).
<one sentence on why this identity rather than extending an existing one>

### Permission policy
```json
<the full policy document>
```

### Trust policy
```json
<the full trust policy — omit this section entirely for an IAM user>
```

## Where this lives
<the relevant slice of the estate: which account, what else runs in it, which accounts it can and
cannot reach, and any cross-account trust that bears on this request. Enough that a blast-radius
question is answerable.>

## Assumptions made while drafting
<every assumption, including ones the operator resolved and what they resolved to>

## Evidence from the AWS estate
<what was actually looked up, in which account, and what came back — or "discovery has not been
run; every identifier below is a placeholder">

## Still unresolved
<each placeholder and what it stands for — or "none">

## Deliberately excluded
<permissions a careless draft would have included, and why they were left out>

## What the reader may ask
Anything about this request. Common starting points:
- Can this identity reach any environment other than the one named above? By what path?
- If its credentials leaked, what exactly could the holder do, read, or change?
- Is there a privilege-escalation path out of these permissions?
- Is any permission broader than the request requires? Name the statement.
- Is anything missing that the request genuinely needs?
- Is the trust relationship correct and appropriately narrow?
- Would you approve this as written? If not, what would you change?
```

## Notes

- **Include the deliberate exclusions.** They are the fastest thing to check, and they show the
  draft considered the over-grant rather than missing it.
- **Be honest about placeholders.** A briefing whose policy is full of `<PLACEHOLDER>` values is
  still worth challenging for shape and scope, but it has to say that is what it is.
- **Answer in a different model than the one that drafted the policy** — a model reviewing its own
  output agrees with itself. Say so in the opening line, since the reviewer chooses where to paste
  it.
- **Length is not the constraint, completeness is** — but every paragraph should be one the reader
  would miss if it were gone. The 11.7 KB first version was long without being interrogable, which
  is the failure this shape is meant to fix.
- The reviewer can also run it through this skill directly: `/iam-access-request challenge` with
  the downloaded file, or with the request id.
