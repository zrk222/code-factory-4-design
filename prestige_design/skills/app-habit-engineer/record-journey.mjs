// Use inside an existing Playwright test. The test owns actions and assertions.
import {createHash} from 'node:crypto';
import {realpath, writeFile} from 'node:fs/promises';
import {basename, dirname, isAbsolute, join, relative, resolve, sep} from 'node:path';

const stableId = /^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$/;
const workspacePath = (root, file) => {
  const path = relative(root, file);
  if (!path || isAbsolute(path) || path === '..' || path.startsWith('..' + sep)) {
    throw new Error('Use a path within the app workspace');
  }
  return path.split(sep).join('/');
};

export async function recordJourney({root = '.', output, appName, profile, screenshots = false}) {
  root = await realpath(root);
  const filename = resolve(root, output);
  workspacePath(root, filename);
  const directory = await realpath(dirname(filename));
  workspacePath(root, join(directory, basename(filename)));
  if (typeof profile !== 'string' || !stableId.test(profile)) throw new Error('Use a stable profile ID');
  if (typeof screenshots !== 'boolean') throw new Error('Use a boolean screenshot preference');
  const checkpoints = [];
  const ctas = [];
  return {
    async primary(page, id, locator) {
      const viewport = page.viewportSize();
      if (!viewport) throw new Error('Set a fixed Playwright viewport for journey evidence');
      if (!await locator.evaluate(element => element.ownerDocument.defaultView === window.top)) {
        throw new Error('Journey primary controls must be in the main frame');
      }
      const {width, height} = viewport;
      const box = await locator.boundingBox();
      const visible = await locator.isVisible();
      const x = box ? box.x + box.width / 2 : -1;
      const y = box ? box.y + box.height / 2 : -1;
      const inViewport = x >= 0 && x < width && y >= 0 && y < height;
      const reachable = visible && inViewport && await locator.isEnabled() && await locator.evaluate(
        (element, point) => element.contains(document.elementFromPoint(...point)), [x, y],
      );
      ctas.push({id, width, height, center_y: Math.round(Math.min(height, Math.max(0, y))), visible, reachable});
    },
    async checkpoint(page, {id, state, checks, mask = []}) {
      if (typeof id !== 'string' || !stableId.test(id) || checkpoints.some(step => step.id === id)) {
        throw new Error('Use a unique stable checkpoint ID');
      }
      let screenshot = null;
      if (screenshots === true) {
        const bytes = await page.screenshot({animations: 'disabled', mask});
        if (bytes.length > 2 * 1024 * 1024) throw new Error('Checkpoint PNG exceeds 2 MiB');
        const path = join(directory, `${basename(filename)}-${id}.png`);
        await writeFile(path, bytes, {flag: 'wx'});
        screenshot = {path: workspacePath(root, path), sha256: createHash('sha256').update(bytes).digest('hex')};
      }
      checkpoints.push({id, state, checks: {...checks}, screenshot});
    },
    async save({taps, inputs, choices, landing, completions, controls}) {
      const capture = {
        schema: 'prestige.journey-capture.v1', app_name: appName, profile,
        metrics: {taps, inputs, choices, landing, ctas, completions}, controls, checkpoints,
      };
      await writeFile(join(directory, basename(filename)), JSON.stringify(capture, null, 2) + '\n', {flag: 'wx'});
    },
  };
}
