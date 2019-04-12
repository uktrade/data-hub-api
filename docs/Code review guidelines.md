# Code Review guidelines

*Discussed and agreed by all Data Hub developers. If anything changes, please keep this document up-to-date and in sync with the related backend/frontend one.*

## Step 1: Before and when submitting a PR

### Code and tests

- Make sure your code is appropriately documented and includes change log fragments describing the change
- Keep the overall coding style consistent with the rest of the repository unless it's been identified as a particular style that we want to move away from. Avoid using your own style as this can cause disagreements among developers. When adopting a new agreed style (ideally) refactor the existing code to keep the overall codebase consistent
- Follow Uncle Bob’s boy-scout rule: “always leave the code behind in a better state than you found it”
- Include unit, functional, e2e and compatibility tests (when applicable)
- Make sure CI build passes consistently without any flaky tests

### Commit Hygiene
- Follow branch naming conventions by prefixing your branch name with *feature/*, *bugfix/*, *removal/*, *test/*, *hotfix/* or *release/*
- Make sure commits are logical and atomic - each commit should include tests
- Keep each commit small and deployable - each commit should ideally leave the develop branch in a releasable state
- Use [imperative mood](https://git.kernel.org/pub/scm/git/git.git/tree/Documentation/SubmittingPatches?id=HEAD#n133) in commit message but it’s okay to use past tense in the description

### PR Hygiene
- Make sure your PR is atomic and doesn’t solve multiple problems at the same time
- Keep your PR small and deployable - each PR **must** leave the develop branch in a releasable state
- The ideal maximum length for a PR is [400 lines of code](https://smartbear.com/learn/code-review/best-practices-for-peer-code-review/)
- Use feature flags if your PR cannot be deployed to production at any time after being merged
- Use GitHub labels if your PR is blocked or depends on another
- Use [a GitHub draft PR](https://github.blog/2019-02-14-introducing-draft-pull-requests/) for WIP or if you want initial feedback

### Description
- Document what the PR does and why the change is needed
- Give full context - not everyone has access to Jira/Trello
- Detail anything that is out of scope and will be covered by future PRs
- Include details on the lifecycle of the feature and its nature. Is it a new feature or a change to an existing one? Is the code going to be short-lived? Is it part of a bigger piece of work?
- Highlight possible controversies
- Include instructions on how to test (e.g. what should I see?)
- Detail any considerations when releasing

### Screenshots
- Add before / after screenshots or GIFs
- Include screenshots of both mobile and desktop versions
