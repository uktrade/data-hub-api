# Code Review guidelines

*Discussed and agreed by all Data Hub developers. If anything changes, please keep this document up-to-date and in sync with the related backend/frontend one.*

# Table of Contents
- [Step 1: Before and when submitting a PR](#step-1)
- [Step 2: PR submitted](#step-2)
- [Step 3: PR approved](#step-3)

## <a name="step-1"></a>Step 1: Before and when submitting a PR

#### Code and tests

- Make sure your code is appropriately documented and includes change log fragments describing the change
- Keep the overall coding style consistent with the rest of the repository unless it's been identified as a particular style that we want to move away from. Avoid using your own style as this can cause disagreements among developers. When adopting a new agreed style (ideally) refactor the existing code to keep the overall codebase consistent
- Follow Uncle Bob's boy-scout rule: “always leave the code behind in a better state than you found it”
- Include unit, functional, e2e and compatibility tests (when applicable)
- Make sure CI build passes consistently without any flaky tests

#### Commit Hygiene
- Follow branch naming conventions by prefixing your branch name with *feature/*, *bugfix/*, *removal/*, *test/*, *hotfix/* or *release/*
- Make sure commits are logical and atomic - each commit should include tests
- Keep each commit small and deployable - each commit should ideally leave the develop branch in a releasable state
- Use [imperative mood](https://git.kernel.org/pub/scm/git/git.git/tree/Documentation/SubmittingPatches?id=HEAD#n133) in commit message but it's okay to use past tense in the description

#### PR Hygiene
- Make sure your PR is atomic and doesn't solve multiple problems at the same time
- Keep your PR small and deployable - each PR **must** leave the develop branch in a releasable state
- PRs shouldn't normally add or change more than [400 lines of code](https://smartbear.com/learn/code-review/best-practices-for-peer-code-review/) at the time
- Use feature flags if your PR cannot be deployed to production at any time after being merged
- Alternatively hide a new piece of functionality behind an express.js route being careful not to expose the URL
- Use GitHub labels if your PR is blocked or depends on another
- Use [a GitHub draft PR](https://github.blog/2019-02-14-introducing-draft-pull-requests/) for WIP or if you want initial feedback

#### Description
- Document what the PR does and why the change is needed
- Give full context - not everyone has access to Jira/Trello
- Detail anything that is out of scope and will be covered by future PRs
- Include details on the lifecycle of the feature and its nature. Is it a new feature or a change to an existing one? Is the code going to be short-lived? Is it part of a bigger piece of work?
- Highlight possible controversies
- Include instructions on how to test (e.g. what should I see?)
- Detail any considerations when releasing

#### Screenshots
- Add before / after screenshots or GIFs
- Include screenshots of both mobile and desktop versions


## <a name="step-2"></a>Step 2: PR submitted

### For both authors and reviewers:

#### <a name="attitude"></a>Attitude
- Remember that you are starting a conversation
- Don't take feedback personally
- Be honest, but don't be rude

#### GitHub
- Non-trivial questions and issues are best discussed via Slack or face-to-face
- The same applies to PRs with large number of comments
- At the end of a conversation, update GitHub with a summary

### If you are the author:

- Make sure you read and follow the guidelines in [Step 1: before and when submitting a PR](#step-1)
- Don't `rebase` or `push --force` whilst the PR is being reviewed otherwise reviewers won't be able to see what's changed
- Don't dismiss change requests except in rare circumstances (e.g. when the reviewer is on holiday), document the reason
- Mark commits that will be squashed into other commits with the *fixup:* prefix. This helps reviewers understand how you are planning to organise your PR after approval
- Respond to comments if you don't agree with them
- If you decide not to implement the suggestion, come to a mutual understanding with the reviewer

### If you are a reviewer:

#### Time
- Allocate 30 minutes in the morning and 30 minutes in the afternoon for reviewing PRs
- If there are multiple PRs, the preferred method for selection is FIFO (first in first out). However, this could result in fewer PRs being reviewed by multiple developers, so use common sense
- Whenever possible, review a PR in one go so that the author understands the amount of work needed and can plan with his/her team

#### Architectural feedback
- Focus on big architectural issues or problems with overall design first. If you spot any, give your feedback immediately before continuing with the review
- Check out the branch and run it locally for a broader view as GitHub tends to focus on single lines

#### Language
- Offer suggestions - “It might be easier to...”, “Consider...”
- Be objective - “this method is missing a docstring” instead of “you forgot to write a docstring”

#### Being diplomatic
- Feel free to constructively challenge approaches and solutions, even when coming from a seasoned developer
- It's OK to nit-pick on syntax issues, spelling errors, poor variable/function names, missing corner cases
- But don't be a perfectionist - allow some flexibility

#### Levels of importance
- Prefix non-critical comments with *Non-critical:* so that the author knows what is important and what is not
- If all your comments are non-critical, leave your feedback but accept the PR at the same time so that you are not a blocker and you keep [a positive attitude](#attitude)


## <a name="step-3"></a>Step 3: PR approved

- `rebase develop` before merging to keep the history clean
- Squash the fixup commits into their related ones
