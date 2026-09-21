// Test-runner injection only. Never copied into site/ or registered by the released app.
// Existing regression suites retain their observations while production AI tools stay removed.
(() => {
  if (window.__giralabTestDriver) return;
  window.__giralabTestDriver = true;
  function fibers() {
    const el = document.querySelector('audio') || document.querySelector('main');
    let f = el?.[Object.keys(el).find(k => k.startsWith('__reactFiber$'))];
    const result = [];
    for (; f; f = f.return) result.push(f);
    return result;
  }
  function hooks() {
    for (const fiber of fibers()) {
      const list = [];
      for (let h = fiber.memoizedState; h && Object.hasOwn(h, 'memoizedState'); h = h.next) list.push(h.memoizedState);
      if (list.some(v => v?.current?.board?.length === 9)) return list;
    }
    return [];
  }
  function game() {
    const g = hooks().find(v => v?.current?.board?.length === 9)?.current;
    if (!g) throw Error('Game not mounted yet');
    return g;
  }
  function findProps(predicate) {
    const root = document.querySelector('#root');
    let fiber = root?.[Object.keys(root).find(k => k.startsWith('__reactContainer$'))];
    if (!fiber) return null;
    while (fiber.return) fiber = fiber.return;
    fiber = fiber.stateNode?.current || fiber;
    const queue = [fiber], seen = new Set();
    while (queue.length) {
      const node = queue.pop(); if (!node || seen.has(node)) continue; seen.add(node);
      if (predicate(node.memoizedProps)) return node.memoizedProps;
      queue.push(node.child, node.sibling);
    }
    return null;
  }
  const driver = {
    get_game_state: { execute() {
      const list = hooks(), g = game();
      const progress = list.find(v => Array.isArray(v?.current?.unlocked))?.current;
      const motion = list.findIndex(v => v && Array.isArray(v.removed) && v.falls);
      const settling = motion >= 0 ? list[motion + 1]?.current || 0 : 0;
      return { status: g.status, elapsed: g.elapsed, presenting: performance.now() < settling,
        score: g.score, danger: g.danger, combo: g.chain, slow: g.freeze,
        multiplier: Math.min(8, 1 + Math.max(0, g.chain - 1) * .5),
        regenerating: g.regenerationPause > 0, rulesVersion: 3,
        board: g.board.map(row => row.map(t => t?.type ?? null)), unlocked: progress?.unlocked ?? g.known };
    } },
    get_audio_state: { execute() {
      const audio = hooks().find(v => typeof v?.current?.getState === 'function')?.current;
      return audio?.getState() ?? { context: 'uninitialized', labPlaying: false, gamePlaying: false };
    } },
    start_game: { execute() {
      const props = findProps(p => p && typeof p.onPlay === 'function' && typeof p.onSettings === 'function');
      if (!props || !['ready', 'over'].includes(game().status)) throw Error('Game cannot start');
      props.onPlay(); return { status: game().status };
    } },
    submit_ingredient_path: { execute({ cells }) {
      const g = game();
      if (g.status !== 'playing' || driver.get_game_state.execute().presenting) throw Error('Game is not accepting input');
      const ids = cells.map((p, i) => {
        const prev = cells[i - 1];
        if (prev && (Math.abs(p.row-prev.row)>1 || Math.abs(p.col-prev.col)>1)) throw Error('Not adjacent');
        const id = g.board[p.row]?.[p.col]?.id; if (!id) throw Error('Missing tile'); return id;
      });
      if (new Set(ids).size !== ids.length) throw Error('Repeated tile');
      const finish = hooks().filter(v => Array.isArray(v) && typeof v[0] === 'function').map(v => v[0])
        .find(fn => fn.toString().includes('.selected') && fn.toString().includes('.recipe.id') && fn.toString().includes('matchMedia'));
      if (!finish) throw Error('Selection callback not found');
      g.selected = ids;
      const result = finish();
      return { success: !!result, recipe: result?.recipe.name ?? null, score: g.score };
    } }
  };
  Object.defineProperty(window, '__gameTools', { configurable: false, get: () => driver, set: () => {} });
})();
