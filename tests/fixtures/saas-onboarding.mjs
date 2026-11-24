import {rejects} from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFile} from 'node:fs/promises';
import {join, resolve} from 'node:path';
import {recordJourney} from '../../prestige_design/skills/app-habit-engineer/record-journey.mjs';

const {chromium} = createRequire(import.meta.url)(process.argv[2]);
const root = resolve(process.argv[3]);
const markup = await readFile(new URL('../../examples/saas-onboarding.html', import.meta.url), 'utf8');
const app = 'https://workbench.test';
await rejects(recordJourney({root, output: 'unrequested.json', appName: 'Workbench',
  profile: 'mobile-chromium', screenshots: 'false'}), /screenshot preference/);
const browser = await chromium.launch({headless: true});
try {
  for (const [build, screenshots] of [['baseline', true], ['candidate', true], ['private', false]]) {
    const page = await browser.newPage({viewport: {width: 390, height: 844}});
    const writes = [];
    let requests = 0;
    await page.route(app + '/**', route => {
      const request = route.request();
      if (request.method() === 'GET') return route.fulfill({contentType: 'text/html', body: markup});
      if (++requests === 1) return route.fulfill({status: 503});
      writes.push(request.postData());
      return route.fulfill({status: 201});
    });
    const capture = await recordJourney({root, output: join(root, build + '.json'),
      appName: 'Workbench', profile: 'mobile-chromium', screenshots});
    const step = (id, state, checks, mask) => capture.checkpoint(page, {id, state, checks, mask});
    await page.goto(app + '/?build=' + (build === 'baseline' ? build : 'candidate'));
    const start = page.getByRole('button', {name: 'Create project'});
    await step('empty-workspace', 'empty', {'start-reachable': await start.isEnabled() && await start.isVisible()});
    await start.click();
    const input = page.getByLabel('Project name');
    const primary = page.getByRole('button', {name: 'Save project'});
    const name = 'Private project name';
    await input.fill(name);
    await capture.primary(page, 'save-project', primary);
    await primary.click();
    const error = page.getByRole('alert');
    await error.waitFor();
    const retained = await input.inputValue() === name;
    await step('save-error', 'error', {
      'draft-preserved': retained,
      'retry-available': await primary.isEnabled(),
      'retry-focused': await primary.evaluate(el => el === document.activeElement),
    }, [input]);
    if (!retained) await input.fill(name);
    await primary.focus();
    await page.keyboard.press('Enter');
    const complete = page.getByRole('heading', {name: 'Project saved'});
    await complete.waitFor();
    await step('save-retry', 'retry', {'one-write': writes.length === 1 && writes[0] === name});
    const hasNext = await page.getByRole('button', {name: 'Create another'}).isVisible();
    await step('project-saved', 'success', {
      'confirmation-focused': await complete.evaluate(el => el === document.activeElement),
      'next-available': hasNext,
    });
    const done = page.getByRole('button', {name: 'Done'});
    await done.focus();
    await page.keyboard.press('Enter');
    const canExit = await start.isVisible() && await start.evaluate(el => el === document.activeElement);
    await step('project-done', 'success', {'keyboard-exit': canExit});
    await capture.save({
      taps: 3, inputs: retained ? 1 : 2, choices: 0, landing: 'recommended',
      completions: [{id: 'project-saved', can_exit: canExit, has_next: hasNext, auto_advances: false, user_enabled: false}],
      controls: {no_deceptive_controls: true, no_predatory_rewards: true, feasible_streak: true,
        notification_controls: true, portable_data: true},
    });
    await page.close();
  }
} finally {
  await browser.close();
}
