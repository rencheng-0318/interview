import sys

MESSAGE = """\
The indexing workflow is not implemented yet.

  1. Design the chunk/embedding storage and add database/migrations/0002_*.sql
  2. Implement chunking and the indexing run under app/features/indexing/
  3. Wire this entry point to it

Requirements: services/api/app/features/indexing/README.md
"""


def main() -> int:
    print(MESSAGE, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
