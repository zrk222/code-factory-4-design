# Habit Engineer and AST remediation

The habit skill audits six mechanics from activation to repeat value. Prestige calculates TAFI, TZER, PPDV and SCER, checks the stated controls, and binds its report to the contract and referenced observations.

Run from the Prestige checkout to install this version and try the example. For an app, run the same Prestige commands from the app's root.

```sh
python -m pip install '.[habit]'
prestige install codex --skill app-habit-engineer
prestige habit-audit examples/habit-contract.json --format markdown
```

Use the example contract as a template. It is a design proposal. Switch to `observed` after replaying corresponding before and after journeys. The first evidence file must contain exactly `schema: prestige.habit-observations.v1`, `app_name`, `lens`, `baseline`, `candidate`, and `controls`. The report checks that these values match the submitted contract and that each evidence file matches its workspace-relative SHA-256 binding. In CI, `--strict` exits 1 on proposals or failing thresholds. Invalid inputs exit 2. Capture JSON or Markdown with ordinary stdout redirection.

Every CTA observation includes a stable `id` and viewport `width` and `height`. Completion samples use stable IDs too. Baseline and candidate must contain the same IDs and viewports. Each contract and referenced observation file is limited to 4 MiB. A passing audit covers the submitted observations. Capture additional onboarding, re-entry, recovery and input profiles in your app's browser suite and attach those artifacts for review.

## Replay your app's Playwright tests

`prestige install codex --skill app-habit-engineer` installs `record-journey.mjs` with the skill. Import it into your existing test and create a recorder with your workspace `root`, a new `output` JSON path in an existing folder, `appName`, and a stable `profile` such as `mobile-chromium`.

- Call `primary(page, id, locator)` at the same point on each build to capture the main-frame control's viewport, visibility and center-point reachability.
- Call `checkpoint(page, {id, state, checks})` after testing a named state. Use the same ordered IDs and boolean check keys on both builds. For a save failure, check that the draft still contains the entered text and that retry is enabled and focused. Record a `success` checkpoint too.
- Call `save({taps, inputs, choices, landing, completions, controls})` with the observed workflow counts and the team's assessments. Run on both builds. The recorder writes no raw test trace or input values. With `screenshots: true`, use the checkpoint's `mask` option for sensitive locators. Export requires separate opt-in and copies only the verified PNG bytes.

Keep your authored habit contract in proposal mode when supplying captures. The browser path uses the captured metrics and controls. A failed candidate assertion blocks the journey even when its four metric thresholds pass. Proof covers the supplied runs, named checks, and the selected viewport.

```sh
prestige habit-audit habit.json --capture before.json after.json --strict
prestige pr app.html --root . --design DESIGN.md --journey habit.json before.json after.json
# Use --include-journey-screenshots and a fresh --out-dir to share the approved captures.
prestige brief PRD.md --purpose saas --components components.json
```

The PR bundle contains the metrics and links from findings to the relevant checkpoint. If included, the paired screenshots appear side by side. The component inventory maps a role to a local source identifier, its file and usage guidance. Roles include `primary_action`, `dialog`, `form_error`, `text_input`, `empty_state`, `progress`, `status_message`, and `session_prompt`. The optional `tokens` value is a workspace-relative design contract or `null`. The brief records the source hashes and includes loading, empty, error, retry, session expiry, and success guidance for the app.

See [Workbench onboarding](../examples/saas-onboarding.html), its [Playwright replay](../tests/fixtures/saas-onboarding.mjs), [habit proposal](../examples/saas-habit-contract.json), and [component inventory](../examples/saas-components.json). The example tests a failed first save, draft preservation, one successful retry, and keyboard exit with focus restoration.

## Source markers

Use one set of markers per component. Give each primary control an explicit `type="button"`. The empty action dock must be an authored sibling of the native header containing the marked button. Style the dock for your layout, including safe-area and keyboard behavior. Prestige moves the exact original JSX button into that dock.

```tsx
<main>
  <header><button type="button" data-prestige-primary onClick={onSave}>Save</button></header>
  <div className="action-dock" data-prestige-action-dock></div>
  <section data-prestige-completion data-prestige-next-handler="onNextAction"
    data-prestige-next-label="Add another">
    <button type="button" data-prestige-done onClick={onClose}>Done</button>
  </section>
</main>
```

The completion must be owned by a component with an existing zero-argument action such as `onNextAction?: () => void`. Parameters can be destructured from props. Prestige keeps Done and adds a separate control for that action. It refuses to relocate a CTA that depends on events delegated by its header or dock, or to inject a handler where another binding could shadow it. Review the preview and apply against its exact original source hash.

```sh
prestige habit-remediate src/ExpenseDone.tsx
prestige habit-remediate src/ExpenseDone.tsx --apply --expect-sha256 SHOWN_SOURCE_HASH
```

Apply from an isolated checkout without other writers. The local lock coordinates Prestige invocations. The source limit is 512 KiB and the preview limit is 256 KiB. Re-run the app's typecheck, build and browser journey after application. Verify that the dock is reachable on the affected viewport, the original control activates once, Done exits and restores focus, and Add another appears and runs only when available and chosen. The remediator checks syntax and idempotence and records the source, candidate and receipt hashes. Browser behavior and retention require separate evidence.

[NotebookLM Studio dashboard](https://notebook.google.com/notebook/7cdc799d-753b-47f7-9aa6-0a6478c0bb21/artifact/aea79de2-9a81-4893-8053-c7bef90e845c)
