### Description of change

<!--
Enter a description of the changes in the PR here.
Include any context that will help reviewers understand the reason for these changes.
-->

### Checklist

* [ ] Has this branch been rebased on top of the current `develop` branch?

  <details>
  <summary>Explanation</summary>
  
  The branch should not be stale or have conflicts at the time reviews are requested.
  
  </details>

* [ ] Is the CircleCI build passing?

### General points

<details>
<summary><strong>Other things to check</strong></summary><p></p>

* Make sure `fixtures/test_data.yaml` is maintained when updating models
* Consider the admin site when making changes to models
* Use select-/prefetch-related field lists in views and search apps, and update them when fields are added
* Make sure the README is updated e.g. when adding new environment variables

</details>

See [docs/CONTRIBUTING.md](https://github.com/uktrade/data-hub-api/blob/develop/docs/CONTRIBUTING.md) for more guidelines.
