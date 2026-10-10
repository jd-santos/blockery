# Tooling

## Packwiz

Packwiz is a local build-time tool. It is not installed on either Bloom server
and is not required while Minecraft is running.

The approved local build is pinned to:

- Source: `github.com/packwiz/packwiz`
- Commit: `ef87d964f8cb`
- Go module version: `v0.0.0-20260906154125-ef87d964f8cb`
- Go toolchain: `go1.27.1 darwin/arm64`
- Output architecture: `darwin/arm64`
- SHA-256: `d3af7948dfdeb6ddf4d00817415543e171ac60eaed6faf2a405f2d299af34214`

Packwiz does not currently expose a version flag. Inspect an installed binary's
embedded module and toolchain information instead:

```sh
go version -m "$(command -v packwiz)"
shasum -a 256 "$(command -v packwiz)"
```

### Rebuild the approved version

Build the pinned source revision directly into the user's command path:

```sh
GOBIN="$HOME/.local/bin" go install github.com/packwiz/packwiz@ef87d964f8cb
```

Do not replace the pinned revision with `@latest`. To update Packwiz, choose and
record a new commit, build it locally, inspect its embedded module information,
and review the changes it produces in a disposable pack before adopting it here.
