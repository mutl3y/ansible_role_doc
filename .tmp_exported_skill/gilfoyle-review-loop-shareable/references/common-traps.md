# Common Traps

- Moving a symbol without updating re-export files or package `__init__` surfaces
- Fixing a type smell by widening everything to `Any`
- Replacing a silent fallback with a different silent fallback plus a comment
- Removing a wrapper that still has import consumers
- Fixing duplication while accidentally changing branch behavior
- Updating runtime code but not the tests that pinned the old shape
- Closing a finding after a narrow path-filtered gate without ever running the full gate
