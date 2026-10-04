# Bot Message Decisions

## Decisions

1. Review all contributor-facing autoassign messages, including invalid-PR enforcement, assignment success/failure, reopened PRs, stale warnings, and closure notices. Follow the approach in [openwisp-docs commit 2963631](https://github.com/openwisp/openwisp-docs/commit/2963631dbb20a631bd399ea3fa246f5a431fdb65): remove repeated explanations, use direct instructions, and describe contributor eligibility precisely rather than by experience level. Invalid-PR enforcement is part of autoassign in this checkout.
2. Both ordinary assignment requests and the explicit `@openwisp-companion assign` command warn external contributors when an issue is unvalidated, whether or not they have opened a PR. They direct contributors to the validated-issues guidance. The bot recognizes the literal phrase "assign to me" and preserves the existing local request-pattern additions.
3. Owners, organization members, and repository collaborators are exempt from issue validation, consistent with PR validation. The bot does not tell them that an unvalidated issue is unavailable. It does not describe issues as reserved for experienced contributors.
4. Normal assignment replies tell contributors that they can start working if nobody is assigned to the issue, open a linked draft PR, and join developer chat to coordinate. They remain friendly and appreciative while avoiding repeated instructions.
5. Invalid-PR warnings do not include a supply-chain security explanation or a threat-model link.
6. Comments link to the validated-issues guidance instead of repeating the validation checklist and project-board links. Invalid-PR comments retain their remediation instructions and 24-hour closure warning; ordinary assignment replies omit that warning.
7. The bot continues responding to repeated assignment requests. Redundancy is addressed by shortening messages, not suppressing replies.

## Reply Messages

The templates below use placeholders such as `<user>`, `<issue>`, `<pr>`, and `<days>`.

### Validated Issue Assignment Request

Trigger: a recognized assignment request on a validated issue, or from an exempt contributor.

```markdown
Hi @<user> 👋,

Thanks for your interest in contributing to OpenWISP!

If nobody is assigned to this issue, you can start working.

Open a draft pull request linked to this issue, for example `Fixes #<issue>`.

Join the [developer chat](https://matrix.to/#/#openwisp_development:gitter.im) to coordinate or ask questions.
```

### Unvalidated Issue Assignment Request

Trigger: a recognized assignment request or explicit assign command from an external contributor on an unvalidated issue.

```markdown
Hi @<user> 👋,

Thanks for your interest in contributing to OpenWISP!

This issue is not currently available to external contributors. Please choose a validated issue.

Read [how to find a validated issue](https://openwisp.io/docs/dev/developer/contributing.html#look-for-validated-issues).

Join the [developer chat](https://matrix.to/#/#openwisp_development:gitter.im) to ask questions or coordinate.
```

### Automatic Assignment Succeeded

Trigger: a linked PR is opened and GitHub confirms assignment.

```markdown
This issue has been automatically assigned to @<user>, who opened PR #<pr>. 🎯
```

### Automatic Assignment Needs A Comment

Trigger: GitHub does not assign the PR author automatically.

```markdown
Hi @<user> 👋,

Thank you for opening PR #<pr> to address this issue!

GitHub requires external contributors to comment on the issue before it allows the bot to assign them automatically.

Comment `@openwisp-companion assign` on this issue to try again.
```

### Explicit Assignment Needs A PR

Trigger: `@openwisp-companion assign` is posted but no matching open PR exists.

```markdown
Hi @<user> 👋,

Thanks for your interest in contributing to OpenWISP! I could not find an open PR by you that references this issue (#<issue>). Please open a PR linking to this issue (e.g. `Fixes #<issue>`) and then comment `@openwisp-companion assign` again.
```

### Explicit Assignment Succeeded

Trigger: `@openwisp-companion assign` finds a linked PR and GitHub confirms assignment.

```markdown
This issue has been assigned to @<user>, who opened PR #<pr>. 🎯
```

### Explicit Assignment Failed

Trigger: GitHub does not confirm assignment after an explicit assign command.

```markdown
Sorry @<user>, GitHub still did not allow this assignment. A maintainer must assign this issue manually.
```

### Invalid Pull Request Warning

Trigger: an external contributor opens or updates a PR that does not link a validated issue.

```markdown
Hi @<user>,

Thanks for your contribution to OpenWISP.

This pull request has been flagged as invalid because it does not link to a validated issue.

Link this pull request to a validated issue by adding `Fixes #ISSUE_NUMBER`, `Closes #ISSUE_NUMBER`, or `Related to #ISSUE_NUMBER` to its description.

See the [contributing guidelines](https://openwisp.io/docs/dev/developer/contributing.html#look-for-validated-issues) and [Anti AI Spam Policy](https://openwisp.io/docs/dev/general/code-of-conduct.html#anti-ai-spam-policy).

This pull request will be closed 24 hours after this comment if it remains invalid.

Join the [developer chat](https://matrix.to/#/#openwisp_development:gitter.im) to ask questions or coordinate.

Thank you for your understanding.
```

### Invalid Pull Request Closure

Trigger: an invalid PR remains unlinked to a validated issue for more than 24 hours.

```markdown
This pull request was closed because it was not linked to a validated issue within 24 hours.
```

### Stale Pull Request Warning

Trigger: a PR has been inactive for 7 to 13 days after changes were requested.

```markdown
Hi @<user> 👋,

This pull request has been inactive for **<days> days** since changes were requested.

Address the requested changes, push updates, or reply if you need help or more time.

Linked issues will be unassigned in **<remaining-days> days**.

Thanks for your contribution!
```

### Stale Pull Request Notice

Trigger: a PR has been inactive for at least 14 days after changes were requested.

```markdown
Hi @<user> 👋,

This pull request is now **stale** after **<days> days** without activity following requested changes.

One or more linked issues were unassigned so other contributors can work on them.

Your contribution is still welcome. Push updates or reply to resume work and be reassigned. We are happy to help if you have questions.
```

If no linked issues were unassigned, the bot posts this alternative sentence instead:

```markdown
No linked issues were unassigned.
```

### Final Stale Pull Request Follow-up

Trigger: a previously marked stale PR has been inactive for at least 60 days.

```markdown
Hi @<user> 👋,

This PR has been inactive for **<days> days** since changes were requested.

We would be glad to see it move forward. Push updates or reply if you plan to continue. Otherwise, please close the PR. Closing the PR helps maintainers keep the contribution queue clear.
```

### Reopened Pull Request Reassignment

Trigger: reopening a valid PR reassigns a linked issue to its author.

```markdown
Welcome back, @<user>! 🎉 This issue has been reassigned to you after reopening PR #<pr>.
```

### Stale Pull Request Recovery

Trigger: the author comments on a stale valid PR and at least one linked issue is reassigned.

```markdown
Thanks for following up, @<user>! 🙌 The stale label was removed and at least one linked issue was reassigned to you.
```
