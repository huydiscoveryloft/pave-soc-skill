# The cross-check prompt

`crosscheck_instruction_md` is a prompt a reviewer copies out of the dashboard and pastes into
an external LLM. The verdict comes back as text they paste into their review.

## Two properties it must have

**1. Self-contained.** The external model sees this text and nothing else — no repo, no ticket,
no conversation. Every fact it needs to judge the policy has to be inline. If the prompt says
"the policy above" and the policy is not in the prompt, the verdict is worthless.

**2. Answered by a different model than the one that drafted it.** A model reviewing its own
output agrees with itself. Tell the reviewer this in the prompt's first line, because they are
the one choosing where to paste it. It is also why the platform stores a pasted verdict instead
of calling a model itself.

## Required shape

```markdown
Review this proposed AWS IAM grant for least privilege. Please answer in a model *other than*
the one that drafted it — a model reviewing its own work will agree with itself.

## What was asked for
<the original request in the requester's own words, translated to English if needed, plus the
source: Jira key or Slack thread>

## What is being proposed
Identity: <name> (<role|user>) in account <profile / id>
<one sentence on why this identity rather than extending an existing one>

### Permission policy
```json
<the full policy document>
```

### Trust policy
```json
<the full trust policy — omit this whole section for an IAM user>
```

## Assumptions made while drafting
<every assumption, including the ones the operator resolved and what they resolved to>

## Evidence from the AWS estate
<what was actually looked up, which account it was read from, and what came back — or
"discovery has not been run; identifiers below are placeholders">

## Still unresolved
<each <PLACEHOLDER> and what it stands for — or "none">

## Deliberately excluded
<permissions a careless draft would have included and why they were left out>

## Please answer
1. Is any permission here broader than the request requires? Name the statement.
2. Is anything missing that the request genuinely needs, which would send the requester back
   for a second grant?
3. Is the trust relationship correct and appropriately narrow?
4. Are the resource ARNs scoped as tightly as the APIs allow? Where `"*"` is used, is that
   genuinely unavoidable?
5. Would you approve this as written? If not, give a corrected policy.
```

## Notes

- **Include the deliberate exclusions.** They are the fastest thing for a reviewer to check, and
  they show the draft considered the over-grant rather than missing it.
- **Be honest about placeholders.** A cross-check of a policy full of `<PLACEHOLDER>` values is
  still useful for shape and scope, but the prompt has to say that is what it is.
- **Do not tell the model what verdict you want.** No "I believe this is least-privilege" — that
  is the question, not the premise.
- Keep it long enough to be complete. This field is stored and rendered in a scrollable panel;
  brevity is not the constraint, completeness is.
