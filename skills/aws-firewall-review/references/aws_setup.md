# AWS setup for the collector

The collector runs as the `aws-firewall-review` MCP server (its source and the
build/registration guide live in the `mcp_server/` directory at the project
root, separate from this plugin). It needs read-only access to EC2 describe APIs
and authenticates either from named `~/.aws` profiles (SSO-capable, the default)
or from environment variables inside the container (with an optional assume-role
handoff). This file covers the AWS-side IAM, SSO, and SCP details; the container
plumbing lives in the `mcp_server/` README.

## IAM permissions required

The identity used (directly or via an assumed role) needs exactly these four actions:

```
ec2:DescribeRegions
ec2:DescribeSecurityGroups
ec2:DescribeNetworkInterfaces
sts:GetCallerIdentity
```

These are all list/describe actions that AWS does not allow to be scoped to
specific ARNs, so the policy `Resource` must be `"*"`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "FirewallReviewReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeRegions",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeNetworkInterfaces",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

The AWS managed policies `SecurityAudit` or `ReadOnlyAccess` also cover this,
but a scoped custom policy is the cleaner evidence story. The same permission
set must exist in **every account** you review; with SSO each profile maps to a
permission set granting these actions.

## Profile / SSO mode (default)

The review runs against three account profiles by default — `development`,
`uat`, and `production` — defined in `~/.aws/config`. The MCP container reads the
host's `~/.aws` (mounted read-only), and boto3 resolves SSO cached tokens and
`source_profile` / `role_arn` chaining natively, so signing in once per profile
on the host is all that's needed:

```bash
aws sso login --profile development
aws sso login --profile uat
aws sso login --profile production
# then, via the MCP server:  collect_security_groups()
```

Each account is collected separately and returned as its own object under
`accounts[]`. Call `collect_security_groups(profiles=[...])` to review a subset.

**The run is all-or-nothing.** Every profile is authenticated up front; if any
one fails (typically an expired SSO session), the tool errors before collecting
anything and returns the exact `aws sso login --profile <name>` command to fix
it. No account is ever skipped — this guarantees a multi-account review is never
partial. Sign in to the failing profile (on the host) and call the tool again.

`AWS_DEFAULT_REGION` is honoured if a profile omits a region (otherwise
`us-east-1` is used for the initial discovery calls).

## Environment variables (for unattended automation)

Used when the tool is called with `profiles=[]`. Set these on the container
(e.g. `-e` in the `docker run` args). Direct-credential mode (minimum):

```
AWS_ACCESS_KEY_ID        (required)
AWS_SECRET_ACCESS_KEY    (required)
AWS_SESSION_TOKEN        (optional — only if the base identity is already temporary)
AWS_DEFAULT_REGION       (optional, default us-east-1)
AWS_REGIONS              (optional, comma-separated; overrides scanning all regions)
```

Assume-role mode (recommended) adds:

```
AWS_ROLE_ARN             arn:aws:iam::<acct>:role/FirewallReviewReadOnly
AWS_ROLE_EXTERNAL_ID     shared secret matching the role's trust policy
AWS_ROLE_SESSION_NAME    optional, default dlvn-firewall-review
AWS_ROLE_DURATION        optional, default 3600 (seconds)
```

When `AWS_ROLE_ARN` is set, the collector authenticates with the base
credentials, calls `sts:AssumeRole`, and uses the resulting 1-hour credentials
for all API calls. The base identity then only needs `sts:AssumeRole` permission
on that one role ARN — nothing else.

## Assume-role trust policy (on the FirewallReviewReadOnly role)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "AWS": "arn:aws:iam::<acct>:user/<base-identity>" },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": { "sts:ExternalId": "<your-external-id>" }
      }
    }
  ]
}
```

## Verifying assume-role worked

After a run, the output JSON's `metadata.aws_caller_arn` should show the
assumed-role ARN (`arn:aws:sts::<acct>:assumed-role/FirewallReviewReadOnly/...`)
rather than the base user — that confirms the handoff happened.

## Service Control Policy regions

If an AWS Organizations SCP denies EC2 in some regions, those regions return an
`UnauthorizedOperation` error, which the collector captures in
`regions[].error`. This is expected and is positive evidence the SCP is
enforcing — it is reported in Appendix A of the report, not treated as a failure.
