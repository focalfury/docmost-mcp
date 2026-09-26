# Upgrading Docmost alongside this MCP

Lessons from the 0.95.0 → 0.96.0 upgrade (2026-09-26). This server talks to Docmost
over two channels — the REST API and the hocuspocus collab WebSocket — and only one
of them is likely to break.

## Order of operations

1. **Rebuild the MCP from current source first.** Not during the upgrade — before it.
2. **Run a write-path test against the old Docmost, before upgrading** — keep the output.
3. Back up Postgres. Migrations are forward-only.
4. Pin the Docmost image to an exact version, then pull.
5. Re-run the identical test and diff against step 2.

Steps 1 and 2 exist so that when something breaks in step 5, you know it was the
upgrade. Skip them and every failure has two possible causes.

## Lessons

**Pin the Docmost image.** `docmost/docmost:latest` silently moves on each release.
With `:latest`, any stray `docker compose pull` upgrades the app *and* runs the
forward-only migrations with no warning. An exact tag makes upgrading a decision.

**Verify the running container matches its source.** `docker compose up -d` without
`--build` happily reuses a stale image. Ours was 2 commits behind for three months —
a secret-redaction fix that had never once executed. Compare the image's build
timestamp against the last commit that touched `src/`.

**The REST API is not where the risk is.** Across 0.95→0.96 every endpoint this
server calls changed additively — new optional fields, new decorators, nothing
removed. The real coupling is `@hocuspocus/provider`, which `update_page` uses. That
server-side dependency went 3.4.4 → 4.5.0 in one release.

**Check the collab library version across releases**, not just the API surface:

```bash
for t in vOLD vNEW; do git show $t:package.json | grep hocuspocus; done
```

Hocuspocus v4 documents wire-protocol compatibility in both directions, and a v3
provider did connect to a v4 server unchanged. Don't preemptively bump the provider —
a v4 provider against a v3 server has a `sessionAwareness` caveat that a v3 provider
doesn't.

**Test the write path, not just reads.** Reads break loudly. `update_page` clears the
whole Yjs fragment and rewrites it, so its failures are silent and destructive. It is
the only tool worth real test effort.

**Measure the wiki before building safeguards.** Risk is a function of what your pages
actually contain, not what the schema permits. Scanning all 61 pages found zero
diagrams, mentions, embeds, callouts or math — the failure modes we'd reasoned
ourselves into caring about didn't exist in the data.

**When scanning, recurse.** `/pages/sidebar-pages` returns only top-level pages. Without
recursing via `pageId` we scanned 26 of 61 pages and nearly drew conclusions from a
third of the wiki.

## MCP-specific traps

**This server's write schema is narrower than Docmost's.** The reader understands 40+
node types; the writer understands StarterKit + Image + Link + Table + TaskList. Any
node outside that set is flattened into text on `update_page`, with no error. Every
Docmost release that adds a node type widens the gap — 0.96.0 added footnotes.

**Registering a Tiptap extension is only half a fix.** `marked` renders GFM task lists
as `<li><input type="checkbox">`, but Tiptap's `TaskList`/`TaskItem` parse on
`data-type` attributes and ignore that markup entirely. The HTML has to be rewritten
to match what the extension expects before `generateJSON()` sees it. Always verify by
inspecting the generated ProseMirror JSON, not by assuming the import worked.

**Pin `@tiptap/*` sub-packages to exact versions.** Their peer dependencies demand an
exact `@tiptap/core` match, so `^3.18.0` resolves to the newest 3.x and drags
`@tiptap/core` and `@tiptap/pm` with it — while `starter-kit` and its ~20
sub-extensions stay put. A split ProseMirror tree in a Yjs write path is not
something you want to debug.

**Test the round-trip, not the write.** The meaningful check is feeding `get_page`
output straight back into `update_page` and confirming the content is byte-identical.
That's what an agent actually does, and it catches read-side bugs a write test
misses — our tables were being written correctly and read back as invalid GFM.

## Don't rebuild what Docmost already has

Docmost ships a native MCP server at `${APP_URL}/mcp`. It is enterprise-gated
(`apps/server/src/ee/` is a stub in the public repo), as are API keys — which is why
this server authenticates with email and password. Re-check this on major releases:
if the gating ever changes, most of this project becomes unnecessary.

## Rollback

Re-pinning the image is not enough — the schema has moved forward. Restore the
pre-upgrade `pg_dump` as well.
