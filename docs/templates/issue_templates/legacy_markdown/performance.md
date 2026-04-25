---
name: ⚡ Performance Issue
about: Report a performance regression or performance-related problem
title: "[PERF] "
labels: bug, status: needs-triage
assignees: ""
# type: (Optionally set specific issue types for issues created with this template (only works if your org has issue types configured; it’s org-level))

---

<!--
Thanks for reporting a performance issue! ⚡

Performance issues help us keep the project fast and efficient.
Please provide as much detail as possible, including measurements and reproduction steps.

<!-- TODO (template users): Replace all JoJo275/simple-python-boilerplate URLs below with your own GitHub username/org and repo name -->

⚠️ **Before submitting**

- For general bugs (not performance-related), use the [Bug Report](https://github.com/JoJo275/simple-python-boilerplate/issues/new?template=bug_report.yml) template.
- **Security vulnerability?** Do **not** open a public issue. See [SECURITY.md](https://github.com/JoJo275/simple-python-boilerplate/blob/main/SECURITY.md).
- **Performance feature request?** Use the [Feature Request](https://github.com/JoJo275/simple-python-boilerplate/issues/new?template=feature_request.yml) template (not this one).
- **Include evidence:** benchmarks, profiling output, and "before vs after" numbers help most.
- Search [existing issues](https://github.com/JoJo275/simple-python-boilerplate/issues) to avoid duplicates.
  -->

## Performance Details

### Issue Type

<!-- Select one -->

- [ ] Performance regression (was faster before)
- [ ] Slow operation / High latency
- [ ] High memory usage
- [ ] High CPU usage
- [ ] Memory leak
- [ ] Slow startup time
- [ ] Inefficient resource usage
- [ ] Scaling issue (performance degrades with size)
- [ ] Unsure
- [ ] Other: <!-- describe -->

### Affected Area

<!-- Select one -->

- [ ] Core library / API
- [ ] CLI
- [ ] Startup / Initialization
- [ ] Data processing
- [ ] I/O operations
- [ ] Network / HTTP operations
- [ ] Memory management
- [ ] Multiple areas
- [ ] Unsure
- [ ] Other: <!-- describe -->

### Description

<!-- Describe the performance issue. What operation is slow? When did you first notice it? -->

### Severity

<!-- Select one -->

- [ ] Critical – Makes the project unusable
- [ ] High – Significantly impacts workflow
- [ ] Medium – Noticeable slowdown but usable
- [ ] Low – Minor performance concern
- [ ] Unsure

### Reproducibility

<!-- Select one -->

- [ ] Always reproducible
- [ ] Intermittent / Flaky
- [ ] Only under specific conditions
- [ ] First run only (cold start)
- [ ] Unsure

### Is this a regression?

<!-- Select one -->

- [ ] Yes – This was faster in a previous version
- [ ] No – This has always been slow
- [ ] Unsure

**Last known good version (if regression):**

<!-- e.g., 0.9.0, or commit hash. Leave blank if not a regression. -->

---

## Environment & Reproduction

| Field                   | Value                                               |
| ----------------------- | --------------------------------------------------- |
| **OS**                  | <!-- e.g., Windows 11 / macOS 14 / Ubuntu 22.04 --> |
| **Python Version**      | <!-- e.g., 3.11.5 -->                               |
| **Package Version**     | <!-- e.g., 0.1.0 -->                                |
| **Hardware** (optional) | <!-- e.g., 8-core CPU, 16GB RAM, SSD -->            |

### Input Size / Data Characteristics (Optional)

<!-- Describe the size or characteristics of the input that triggers the issue. -->
<!--
- Number of records: 100,000
- File size: 500MB
- Iterations: 10,000
-->

### Sample Data (Optional)

<!-- If you can share data that reproduces the issue, provide a link or describe how to generate it. -->
<!--
Link: https://gist.github.com/...
Or: "Run `generate_test_data(n=100000)` to create equivalent data"
Or: "Data is confidential, but it's a 500MB CSV with 100k rows"
-->

### Steps to Reproduce

<!-- Steps to reproduce the performance issue -->

1.
2.
3.

### Minimal Reproduction Code (Optional)

```python
# Paste your code here
```

---

## Measurements

### Timing Measurements (Optional)

<!-- Compare current vs. expected timing -->
<!--
Current:
- Operation takes ~15 seconds
- Throughput: 100 records/second

Expected:
- Should be <1 second
- Previous version (v0.9.0): 200ms
-->

### Memory Measurements (Optional)

<!-- Compare current vs. expected memory usage -->
<!--
Current:
- Memory usage peaks at 2GB
- Memory grows by 100MB per iteration

Expected:
- Should be <500MB peak
- Previous version: stable at 200MB
-->

### Profiling Data (Optional)

<!-- If you have profiling results (cProfile, memory_profiler, py-spy, etc.), paste them here -->

```
# Paste profiling output here
```

---

## Additional Context

### Workaround (Optional)

<!-- If you've found a workaround that improves performance, please share it -->

### Additional Context (Optional)

<!-- Any other context: related issues, suspected causes, profiling screenshots, etc. -->

---

## Contribution Interest

<!-- Select one -->

- [ ] Yes, I'd like to work on this
- [ ] Yes, but I'd need guidance
- [ ] I can help with testing/benchmarking
- [ ] No, I'm just reporting the issue

---

## Checklist

- [ ] I have searched existing issues for duplicates
- [ ] I have provided performance measurements (or explained why I couldn't)
- [ ] I have tested with the latest version
- [ ] I can provide sample data that reproduces this issue
