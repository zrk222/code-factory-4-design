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
