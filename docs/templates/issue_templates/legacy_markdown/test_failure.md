---
name: 🧪 Test Failure
about: Report a test failure, flaky test, or test infrastructure issue. For application bugs, use the Bug Report template.
title: "[TEST] Short description of the test failure"
labels: test-failure, status: needs-triage
assignees: ""
---

<!--
Thanks for reporting a test failure! 🧪

Reliable tests are essential for project quality.
Please provide as much detail as possible to help us investigate.
-->

<!-- TODO (template users): Replace all JoJo275/simple-python-boilerplate URLs below with your own GitHub username/org and repo name -->

## ⚠️ Before submitting

- [ ] **Not an application bug** – Use the [Bug Report](https://github.com/JoJo275/simple-python-boilerplate/issues/new?template=bug_report.yml) template if the test is exposing a real bug
- [ ] **Not a security issue** – Do **not** open a public issue for vulnerabilities. See [SECURITY.md](https://github.com/JoJo275/simple-python-boilerplate/blob/main/SECURITY.md)
- [ ] **Searched for duplicates** – No [existing issue](https://github.com/JoJo275/simple-python-boilerplate/issues) covers this

---

## Failure Details

### Failure Type

<!-- Select one: -->

- [ ] Test failure (consistent)
- [ ] Flaky test (intermittent failure)
- [ ] Test timeout
- [ ] Test infrastructure issue
- [ ] Test performance issue
- [ ] CI/CD pipeline failure
- [ ] Other (describe below)

**If "Other," please describe:**

### Test Name / Location

<!-- Which test(s) are failing? Include file path and test name. -->
<!-- e.g., tests/test_utils.py::test_parse_input -->

### Summary

<!-- Describe the test failure. What is happening? -->

### Error Output

<!-- Paste the full test failure output, including assertion error or traceback. -->

```
PASTE ERROR OUTPUT HERE
```

### Reproducibility

<!-- Select one: -->

- [ ] Always fails
- [ ] Flaky (fails sometimes)
- [ ] Only in CI
- [ ] Only locally
- [ ] Unsure

### Is this a regression?

<!-- Select one: -->

- [ ] Yes – This test used to pass
- [ ] No – This is a new test
- [ ] No – This test has always been flaky
- [ ] Unsure

**Last known passing (if regression):**

<!-- e.g., commit abc123, PR #42, or version 0.9.0 -->

---

## Environment

### Where does this fail?

<!-- Select one: -->

- [ ] Local development
- [ ] CI/CD (GitHub Actions, etc.)
- [ ] Both local and CI
- [ ] Unsure

**OS (if local):**

<!-- e.g., Windows 11 / macOS 14 / Ubuntu 22.04 -->

**Python Version (if local):**

<!-- e.g., 3.11.5 -->

**Commit / Branch / Release:**

<!-- e.g., abc1234, main, or v1.2.0 -->

**CI Run Link (if applicable):**

<!-- e.g., https://github.com/owner/repo/actions/runs/... -->

**CI Job Name + Runner OS (if applicable):**

<!-- For matrix failures: e.g., test (ubuntu-latest, 3.11) -->

**Flake Rate / Frequency (if intermittent):**

<!-- e.g., ~1 in 20 runs, or 3 times this week -->

**Test Command Used:**

<!-- If not just `pytest`, e.g., pytest -x -v tests/ --timeout=60 -->

---

## Reproduction (Optional)

<!-- Skip if it's just "run the test." Add extra steps only if needed. -->

<!--
Usually just:
1. pip install -e ".[dev]"
2. Run the test command above

Add extra steps only if needed (e.g., specific env vars, seed data, timing).
-->

---

## Additional Context

### Analysis / Suspected Cause (Optional)

<!-- Any insights into what might be causing the failure? -->

### Other Tests Affected? (Optional)

<!-- Are other tests also failing or flaky? e.g., test_auth.py also times out -->

---

## Final Checklist

- [ ] I have searched existing issues for duplicates
- [ ] I have included the full error output
- [ ] I have verified this is a test issue, not an application bug
