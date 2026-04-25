"""Example experiment: Quick data exploration.

This is a scratch file for ad-hoc data analysis.
Delete this file when creating your own project.
"""

from collections import Counter
from pathlib import Path

# Example: Analyze file types in the project


def count_file_extensions(directory: str = ".") -> dict[str, int]:
    """Count file extensions in a directory tree."""
    extensions: Counter[str] = Counter()

    for path in Path(directory).rglob("*"):
        if path.is_file():
            ext = path.suffix or "(no extension)"
            extensions[ext] += 1

    return dict(extensions.most_common())


def main():
    print("File extension counts in project:\n")

    counts = count_file_extensions(".")

    for ext, count in counts.items():
        print(f"  {ext:15} {count:4}")

    print(f"\nTotal files: {sum(counts.values())}")


if __name__ == "__main__":
    main()
