// Exercises the actual TS modules. No microphone, browser, storage or network.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { test } = require('node:test');
const ts = require('typescript');

const cache = new Map();
function loadTs(filename) {
  let resolved = filename;
  if (!fs.existsSync(resolved)) resolved += '.ts';
  if (fs.statSync(resolved).isDirectory()) resolved = path.join(resolved, 'index.ts');
  if (cache.has(resolved)) return cache.get(resolved).exports;
  const module = { exports: {} };
  cache.set(resolved, module);
  const compiled = ts.transpileModule(fs.readFileSync(resolved, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const localRequire = (specifier) => specifier.startsWith('.')
    ? loadTs(path.resolve(path.dirname(resolved), specifier)) : require(specifier);
  new vm.Script(`(function(module,exports,require){${compiled}\n})`, { filename: resolved })
    .runInThisContext()(module, module.exports, localRequire);
  return module.exports;
}

const root = path.resolve(__dirname, '../src/pages/FormFillPage');
const { birthRegistration: template } = loadTs(path.join(root, 'templates/birthRegistration.ts'));
const { findTemplateConfig } = loadTs(path.join(root, 'templates/index.ts'));
const { createFormDraft, draftReducer, qrValuesForRole } = loadTs(path.join(root, 'draft.ts'));
const { createSpeechSession, browserRecognition } = loadTs(path.join(root, 'speech.ts'));
const { captureQrFrame } = loadTs(path.join(root, 'cameraCapture.ts'));
const card = {
  field_cccd: '000000000001', field_cmnd: '', field_ho_ten: 'NGUOI THU NGHIEM',
  field_ngay_sinh: '01/01/1990', field_gioi_tinh: 'Nam',
  field_dia_chi: 'DIA CHI DEMO', field_ngay_cap: '01/01/2021',
};
const scan = (draft, role, data = card) => draftReducer(draft, { type: 'scan', role, data, template });

test('37 exact scan/form markers, including nested form_38 and no form_37', () => {
  assert.equal(template.fields.length, 37);
  assert.equal(new Set(template.fields.map((field) => field.id)).size, 37);
  assert(template.fields.some((field) => field.id === 'form_38'));
  assert(!template.fields.some((field) => field.id === 'form_37'));
  assert.equal(template.fields.filter((field) => field.id.startsWith('scan_')).length, 4);
  assert.equal(template.fields.filter((field) => field.id.startsWith('form_')).length, 33);
});
test('mapping requires matching hash and exact marker set', () => {
  const fields = template.fields.map((field) => field.id);
  assert.equal(findTemplateConfig(template.templateSha256.toUpperCase(), fields), template);
  assert.equal(findTemplateConfig('0'.repeat(64), fields), null);
  assert.equal(findTemplateConfig(undefined, fields), null);
  assert.equal(findTemplateConfig(template.templateSha256, fields.slice(1)), null);
  assert.equal(findTemplateConfig(template.templateSha256, fields.map((field) => field === 'form_38' ? 'form_37' : field)), null);
  assert.equal(findTemplateConfig('9a53eb1d5c7501fc26ced64c4fa9ebb7ab32c4cea62f657a5352ba4fe133f8cf', fields), null);
});
test('requester scan fills only four requester fields', () => {
  const values = qrValuesForRole(template, 'requester', card);
  assert.deepEqual(Object.keys(values), ['scan_ho_ten', 'scan_ngay_sinh', 'scan_dia_chi', 'scan_cccd']);
  assert.equal(values.scan_ho_ten, card.field_ho_ten);
  assert.equal(values.scan_cccd, card.field_cccd); // Bare number, not an invented document description.
  assert(!Object.hasOwn(values, 'form_7'));
  assert(!Object.hasOwn(values, 'form_15'));
});
test('fixed birth template has one QR recipient; all other roles are manual', () => {
  assert.deepEqual(template.roles, [{ id: 'requester', label: 'Người yêu cầu' }]);
  assert.deepEqual(qrValuesForRole(template, 'mother', card), {});
  assert.deepEqual(qrValuesForRole(template, 'father', card), {});
  assert.deepEqual(qrValuesForRole(template, 'child', card), {});
});
test('scan preserves manual values, including deliberately cleared fields', () => {
  let draft = draftReducer(createFormDraft(), { type: 'field', field: 'scan_ho_ten', value: 'DA SUA' });
  draft = draftReducer(draft, { type: 'field', field: 'scan_ngay_sinh', value: '' });
  draft = scan(draft, 'requester');
  assert.equal(draft.values.scan_ho_ten, 'DA SUA');
  assert.equal(draft.values.scan_ngay_sinh, '');
  assert.equal(draft.scanReport.applied, 2);
  assert.equal(draft.scanReport.protected, 2);
});
test('rescan protects prior draft and keeps new QR suggestions separately', () => {
  const first = scan(createFormDraft(), 'requester');
  const changed = { ...card, field_ho_ten: 'NGUOI DEMO KHAC' };
  const second = scan(first, 'requester', changed);
  assert.equal(second.values.scan_ho_ten, card.field_ho_ten);
  assert.equal(second.scans.requester.field_ho_ten, changed.field_ho_ten);
  assert.equal(second.scanReport.protected, 1);
  assert.equal(first.scans.requester.field_ho_ten, card.field_ho_ten);
});
const multiRoleTemplate = {
  ...template,
  roles: [...template.roles, { id: 'mother', label: 'Người mẹ' }],
  fields: template.fields.map((field) => field.id === 'form_15'
    ? { ...field, roleId: 'mother', qrSource: 'field_ho_ten' } : field),
};
test('generic multi-role configurations retain independent QR snapshots', () => {
  const mother = { ...card, field_ho_ten: 'ME DEMO' };
  let draft = scan(createFormDraft(), 'requester');
  draft = draftReducer(draft, { type: 'scan', role: 'mother', data: mother, template: multiRoleTemplate });
  assert.equal(draft.values.scan_ho_ten, card.field_ho_ten);
  assert.equal(draft.values.form_15, mother.field_ho_ten);
  assert.equal(draft.scans.requester, card);
  assert.equal(draft.scans.mother, mother);
});
test('clear scan keeps all entered values; reset drops old template data', () => {
  const before = scan(createFormDraft(), 'requester');
  const cleared = draftReducer(before, { type: 'clearScan', role: 'requester' });
  assert.deepEqual(cleared.values, before.values);
  assert.deepEqual(cleared.scans, {});
  assert.deepEqual(draftReducer(cleared, { type: 'reset' }), createFormDraft());
});
test('unknown template scan is reference only', () => {
  const draft = draftReducer(createFormDraft(), { type: 'scan', role: 'reference', data: card, template: null });
  assert.deepEqual(draft.values, {});
  assert.equal(draft.scans.reference, card);
});

test('camera capture keeps native pixels and encodes lossless PNG', () => {
  const video = { videoWidth: 1920, videoHeight: 1080, readyState: 2, clientWidth: 400, clientHeight: 300 };
  const calls = [];
  const fakeBlob = { type: 'image/png' };
  const canvas = {
    getContext(type) { assert.equal(type, '2d'); return { drawImage: (...args) => calls.push(args) }; },
    toBlob(callback, type, quality) { assert.equal(type, 'image/png'); assert.equal(quality, undefined); callback(fakeBlob); },
  };
  let captured;
  captureQrFrame(video, canvas, (blob) => { captured = blob; });
  assert.equal(canvas.width, 1920);
  assert.equal(canvas.height, 1080);
  assert.deepEqual(calls, [[video, 0, 0]]);
  assert.equal(captured, fakeBlob);
});
test('camera capture refuses missing frames and canvas rather than submitting blank images', () => {
  assert.throws(() => captureQrFrame({ videoWidth: 0, videoHeight: 0, readyState: 0 }, {}, () => {}), /Camera chưa có hình/);
  assert.throws(() => captureQrFrame({ videoWidth: 640, videoHeight: 480, readyState: 2 }, { getContext: () => null }, () => {}), /Không lấy được ảnh/);
});

class FakeRecognition {
  constructor() { FakeRecognition.latest = this; this.starts = 0; this.stops = 0; this.aborts = 0; }
  start() { this.starts++; }
  stop() { this.stops++; }
  abort() { this.aborts++; }
  result(...texts) { this.onresult?.({ results: texts.map((text) => ({ isFinal: true, 0: { transcript: text } })) }); }
}
function fakeClock() {
  let now = 0, serial = 0;
  const jobs = new Map();
  return {
    setTimeout(callback, delay) { const id = ++serial; jobs.set(id, { callback, at: now + delay }); return id; },
    clearTimeout(id) { jobs.delete(id); },
    advance(delay) {
      now += delay;
      for (const [id, job] of [...jobs]) if (job.at <= now && jobs.delete(id)) job.callback();
    },
  };
}
function speechFixture(Constructor = FakeRecognition) {
  const events = { texts: [], listening: [], errors: [] };
  const clock = fakeClock();
  const session = createSpeechSession(Constructor, {
    onText: (text) => events.texts.push(text),
    onListening: (value) => events.listening.push(value),
    onError: (error) => events.errors.push(error),
  }, clock);
  return { session, events, clock, recognition: FakeRecognition.latest };
}
test('recognition never starts during construction or before an explicit click', () => {
  const { session, recognition, events } = speechFixture();
  assert.equal(recognition.starts, 0);
  assert.equal(recognition.lang, 'vi-VN');
  assert.equal(recognition.continuous, false);
  session.start(); session.start();
  assert.equal(recognition.starts, 1);
  assert.deepEqual(events.listening, [true]);
  session.dispose();
});
test('cumulative recognition results replace snapshots instead of duplicating text', () => {
  const { session, recognition, events } = speechFixture();
  session.start();
  recognition.result('mot'); recognition.result('mot', 'hai'); recognition.result('mot', 'hai');
  assert.deepEqual(events.texts, ['mot', 'mot hai', 'mot hai']);
  session.dispose();
});
test('manual stop still accepts final text before end', () => {
  const { session, recognition, events, clock } = speechFixture();
  session.start(); session.stop(); recognition.result('ban cuoi'); recognition.onend();
  clock.advance(5000);
  assert.deepEqual(events.texts, ['ban cuoi']);
  assert.deepEqual(events.listening, [true, false]);
  assert.deepEqual(events.errors, []);
});
test('no legacy two-second timeout', () => {
  const { session, recognition, clock } = speechFixture();
  session.start(); clock.advance(10000);
  assert.equal(recognition.stops, 0);
  clock.advance(50000);
  assert.equal(recognition.stops, 1);
  session.dispose();
});
test('missing end event is bounded and warns instead of hanging', () => {
  const { session, recognition, events, clock } = speechFixture();
  session.start(); session.stop(); clock.advance(3000);
  assert.equal(recognition.aborts, 1);
  assert.deepEqual(events.errors, ['end-timeout']);
  assert.deepEqual(events.listening, [true, false]);
});
test('network error stops capture and does not restart', () => {
  const { session, recognition, events, clock } = speechFixture();
  session.start(); recognition.onerror({ error: 'network' }); clock.advance(90000);
  assert.equal(recognition.starts, 1);
  assert.equal(recognition.aborts, 1);
  assert.deepEqual(events.errors, ['network']);
  assert.deepEqual(events.listening, [true, false]);
});
test('closing the field detaches handlers and ignores late results', () => {
  const { session, recognition, events, clock } = speechFixture();
  session.start(); const lateResult = recognition.onresult;
  session.dispose(); lateResult({ results: [{ isFinal: true, 0: { transcript: 'late' } }] });
  clock.advance(90000);
  assert.equal(recognition.aborts, 1);
  assert.equal(recognition.onresult, null);
  assert.deepEqual(events.texts, []);
});
test('browser capability requires secure context and a real recognition constructor', () => {
  assert.equal(browserRecognition(), null);
  global.window = { isSecureContext: false, webkitSpeechRecognition: FakeRecognition };
  assert.equal(browserRecognition(), null);
  global.window.isSecureContext = true;
  assert.equal(browserRecognition(), FakeRecognition);
  delete global.window;
});

test('dictation UI shows only guidance and starts no microphone while rendering', () => {
  const filename = path.join(root, 'components/FieldDictation.tsx');
  const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX,
    },
  }).outputText;
  const module = { exports: {} };
  const localRequire = (specifier) => {
    if (specifier.endsWith('.module.css')) return { default: {} };
    if (specifier.startsWith('.')) return loadTs(path.resolve(path.dirname(filename), specifier));
    return require(specifier);
  };
  new vm.Script(`(function(module,exports,require){${compiled}\n})`, { filename })
    .runInThisContext()(module, module.exports, localRequire);
  const previousWindow = global.window;
  const recognition = FakeRecognition.latest;
  global.window = { isSecureContext: true, webkitSpeechRecognition: FakeRecognition };
  try {
    const html = require('react-dom/server').renderToStaticMarkup(
      require('react').createElement(module.exports.FieldDictation, { value: '', onChange() {}, onListeningChange() {} }),
    );
    assert.match(html, /Bấm để nói, chữ sẽ hiện ngay trong ô này/);
    assert.doesNotMatch(html, /Chrome|internet|trực tuyến|checkbox|disabled|textarea|Dùng bản nháp/);
    assert.equal(FakeRecognition.latest, recognition);
    delete global.window;
    const unsupported = require('react-dom/server').renderToStaticMarkup(
      require('react').createElement(module.exports.FieldDictation, { value: '', onChange() {}, onListeningChange() {} }),
    );
    assert.match(unsupported, /Bạn vẫn có thể gõ/);
    assert.doesNotMatch(unsupported, /Chrome|internet|trực tuyến/);
  } finally {
    if (previousWindow === undefined) delete global.window;
    else global.window = previousWindow;
  }
});

// Exercises the real editor/dictation JSX with a tiny synchronous hook host and
// fake recognition/timers. This is not a React DOM or real-microphone test.
function editorFixture(initial = '') {
  const instances = new Map();
  const cleanups = [];
  const modules = new Map();
  const clock = fakeClock();
  const saves = [];
  const jsx = require('react/jsx-runtime');
  let active;
  let cursor;
  const react = {
    useState(initialValue) {
      const slots = active;
      const index = cursor++;
      if (!(index in slots)) slots[index] = typeof initialValue === 'function' ? initialValue() : initialValue;
      return [slots[index], (next) => {
        slots[index] = typeof next === 'function' ? next(slots[index]) : next;
      }];
    },
    useRef(initialValue) {
      const slots = active;
      const index = cursor++;
      if (!(index in slots)) slots[index] = { current: initialValue };
      return slots[index];
    },
    useId() { return react.useRef(`field-${instances.size}`).current; },
    useEffect(effect) {
      const index = cursor++;
      if (!(index in active)) {
        active[index] = true;
        const cleanup = effect();
        if (cleanup) cleanups.push(cleanup);
      }
    },
  };
  function loadComponent(filename) {
    if (modules.has(filename)) return modules.get(filename).exports;
    const module = { exports: {} };
    modules.set(filename, module);
    const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX },
    }).outputText;
    const localRequire = (specifier) => {
      if (specifier === 'react') return react;
      if (specifier === 'react-dom') return { createPortal: (element) => element };
      if (specifier === 'lucide-react') return new Proxy({}, { get: () => () => null });
      if (specifier.endsWith('.module.css')) return { default: {} };
      if (specifier === '../speech') return {
        browserRecognition: () => FakeRecognition,
        speechErrorMessages: loadTs(path.join(root, 'speech.ts')).speechErrorMessages,
        createSpeechSession: (Constructor, callbacks) => createSpeechSession(Constructor, callbacks, clock),
      };
      if (specifier.startsWith('.')) return loadComponent(path.resolve(path.dirname(filename), `${specifier}.tsx`));
      return require(specifier);
    };
    const run = new vm.Script(`(function(module,exports,require){${compiled}\n})`, { filename })
      .runInNewContext({ document: { body: {}, activeElement: null } });
    run(module, module.exports, localRequire);
    return module.exports;
  }
  const { EditablePlaceholder } = loadComponent(path.join(root, 'components/EditablePlaceholder.tsx'));
  let value = initial;
  function resolve(element, location = 'root') {
    if (element === null || element === undefined || typeof element === 'boolean') return null;
    if (Array.isArray(element)) return element.map((child, index) => resolve(child, `${location}.${index}`));
    if (typeof element !== 'object') return element;
    if (typeof element.type === 'function') {
      if (!instances.has(location)) instances.set(location, []);
      active = instances.get(location);
      cursor = 0;
      return resolve(element.type(element.props), `${location}.component`);
    }
    return { ...element, props: { ...element.props, children: resolve(element.props.children, `${location}.children`) } };
  }
  function render() {
    return resolve(jsx.jsx(EditablePlaceholder, {
      fieldName: 'demo', value, config: { label: 'Ô thử nghiệm', group: 'Thử nghiệm' },
      onSave: (field, next) => { saves.push({ field, value: next }); value = next; },
    }));
  }
  function nodes(tree, type) {
    if (Array.isArray(tree)) return tree.flatMap((node) => nodes(node, type));
    if (!tree || typeof tree !== 'object') return [];
    return [...(tree.type === type ? [tree] : []), ...nodes(tree.props.children, type)];
  }
  function textOf(tree) {
    if (Array.isArray(tree)) return tree.map(textOf).join('');
    if (!tree || typeof tree === 'boolean') return '';
    return typeof tree === 'object' ? textOf(tree.props.children) : String(tree);
  }
  function button(label) {
    const found = nodes(render(), 'button').find((node) => textOf(node) === label);
    assert(found, `Missing button: ${label}`);
    return found;
  }
  return {
    saves, clock, render, button,
    open() { nodes(render(), 'button')[0].props.onClick(); },
    input() { return nodes(render(), 'textarea')[0]; },
    inputCount() { return nodes(render(), 'textarea').length; },
    text() { return textOf(render()); },
    close() { for (const cleanup of cleanups.splice(0).reverse()) cleanup(); },
  };
}

test('voice results go straight into the only field input, with one final Xong', (t) => {
  const fixture = editorFixture();
  t.after(() => fixture.close());
  const previousRecognition = FakeRecognition.latest;
  fixture.open();
  assert.equal(fixture.inputCount(), 1);
  assert.equal(FakeRecognition.latest, previousRecognition); // Rendering opens no microphone.
  assert.doesNotMatch(fixture.text(), /Dùng bản nháp|Bản nháp nhận diện/);
  fixture.button('Bấm để nói').props.onClick();
  const recognition = FakeRecognition.latest;
  assert.equal(fixture.input().props.readOnly, true);
  assert.equal(fixture.button('Xong').props.disabled, true);
  recognition.result('NOI DUNG', 'DEMO');
  assert.equal(fixture.input().props.value, 'NOI DUNG DEMO');
  assert.deepEqual(fixture.saves, []);
  recognition.onend();
  assert.equal(fixture.input().props.readOnly, false);
  fixture.input().props.onChange({ target: { value: 'DA SUA DEMO' } });
  fixture.button('Xong').props.onClick();
  assert.deepEqual(fixture.saves, [{ field: 'demo', value: 'DA SUA DEMO' }]);
});

test('Nói lại replaces recognized content and does not erase the field before results', (t) => {
  const fixture = editorFixture('NOI DUNG CU');
  t.after(() => fixture.close());
  fixture.open();
  fixture.button('Nói lại').props.onClick();
  const first = FakeRecognition.latest;
  assert.equal(fixture.input().props.value, 'NOI DUNG CU');
  first.result('');
  assert.equal(fixture.input().props.value, 'NOI DUNG CU');
  first.result('MOI'); first.result('MOI', 'HOAN CHINH'); first.onend();
  assert.equal(fixture.input().props.value, 'MOI HOAN CHINH');
  fixture.button('Nói lại').props.onClick();
  FakeRecognition.latest.result('LAN HAI'); FakeRecognition.latest.onend();
  assert.equal(fixture.input().props.value, 'LAN HAI');
  assert.equal(first.onresult, null);
});

test('Dừng waits for final text before enabling Xong', (t) => {
  const fixture = editorFixture();
  t.after(() => fixture.close());
  fixture.open(); fixture.button('Bấm để nói').props.onClick();
  const recognition = FakeRecognition.latest;
  recognition.result('TAM');
  fixture.button('Dừng').props.onClick();
  assert.equal(fixture.button('Đang hoàn tất…').props.disabled, true);
  assert.equal(fixture.button('Xong').props.disabled, true);
  fixture.button('Xong').props.onClick(); // Even a direct handler call cannot save while listening.
  assert.deepEqual(fixture.saves, []);
  recognition.result('KET QUA CUOI'); recognition.onend();
  assert.equal(fixture.button('Xong').props.disabled, false);
  fixture.button('Xong').props.onClick();
  assert.deepEqual(fixture.saves, [{ field: 'demo', value: 'KET QUA CUOI' }]);
});

test('Hủy discards spoken changes; closing stops recognition and ignores late text', (t) => {
  const fixture = editorFixture('GIA TRI CU');
  t.after(() => fixture.close());
  fixture.open(); fixture.button('Nói lại').props.onClick();
  const recognition = FakeRecognition.latest;
  recognition.result('CHUA LUU');
  const lateResult = recognition.onresult;
  fixture.button('Hủy').props.onClick();
  fixture.close(); // The hook host runs unmount cleanup explicitly.
  lateResult({ results: [{ isFinal: true, 0: { transcript: 'TRA MUON' } }] });
  assert.deepEqual(fixture.saves, []);
  assert.equal(recognition.aborts, 1);
  assert.match(fixture.text(), /GIA TRI CU/);
});

test('recognition errors preserve text, unlock editing and never restart automatically', (t) => {
  const fixture = editorFixture('NOI DUNG CU');
  t.after(() => fixture.close());
  fixture.open(); fixture.button('Nói lại').props.onClick();
  const recognition = FakeRecognition.latest;
  recognition.onerror({ error: 'network' });
  assert.equal(fixture.input().props.value, 'NOI DUNG CU');
  assert.equal(fixture.input().props.readOnly, false);
  assert.equal(fixture.button('Xong').props.disabled, false);
  assert.match(fixture.text(), /Hãy thử lại hoặc nhập bằng tay/);
  fixture.clock.advance(90000);
  assert.equal(recognition.starts, 1);
  fixture.button('Nói lại').props.onClick();
  assert.doesNotMatch(fixture.text(), /Hãy thử lại hoặc nhập bằng tay/);
});

test('missing end releases the field after bounded wait, and voice input respects length', (t) => {
  const fixture = editorFixture();
  t.after(() => fixture.close());
  fixture.open(); fixture.button('Bấm để nói').props.onClick();
  FakeRecognition.latest.result('a'.repeat(2100));
  assert.equal(fixture.input().props.value.length, 2000);
  fixture.button('Dừng').props.onClick(); fixture.clock.advance(3000);
  assert.equal(fixture.button('Xong').props.disabled, false);
  assert.equal(fixture.input().props.readOnly, false);
  assert.match(fixture.text(), /kiểm tra lại nội dung trong ô/);
});

// A small synchronous hook host exercises the real hook's async guards without
// mounting a DOM or sending network requests. It is not a React/browser E2E test.
function hookFixture(configOverride) {
  const slots = [];
  const calls = [];
  let cursor = 0;
  const react = {
    useState(initial) {
      const index = cursor++;
      if (!(index in slots)) slots[index] = typeof initial === 'function' ? initial() : initial;
      return [slots[index], (next) => {
        slots[index] = typeof next === 'function' ? next(slots[index]) : next;
      }];
    },
    useReducer(reducer, initial, initialize) {
      const [value, setValue] = react.useState(() => initialize ? initialize(initial) : initial);
      return [value, (action) => setValue((previous) => reducer(previous, action))];
    },
    useRef(initial) {
      const index = cursor++;
      if (!(index in slots)) slots[index] = { current: initial };
      return slots[index];
    },
    useCallback(callback) { return callback; },
    useEffect() { /* Cleanup is covered separately by session tests. */ },
  };
  const api = {
    post(url, payload, options) {
      let resolve;
      const promise = new Promise((finish) => { resolve = finish; });
      calls.push({ url, payload, signal: options.signal, resolve: (data) => resolve({ data }) });
      return promise;
    },
  };
  const filename = path.join(root, 'hooks/useFormFill.ts');
  const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  const module = { exports: {} };
  const hookRequire = (specifier) => {
    if (specifier === '../templates' && configOverride) return { findTemplateConfig: () => configOverride };
    if (specifier === 'react') return react;
    if (specifier === '@/services/api/client') return { queryClient: api };
    if (specifier === '@/services/api/endpoints') return {
      ENDPOINTS: { QUERY: { FORMS: { RENDER: '/render', CCCD_SCAN: '/scan', FILL: '/fill' } } },
    };
    return loadTs(path.resolve(path.dirname(filename), specifier));
  };
  new vm.Script(`(function(module,exports,require){${compiled}\n})`, { filename })
    .runInThisContext()(module, module.exports, hookRequire);
  return {
    calls,
    render() { cursor = 0; return module.exports.useFormFill(); },
  };
}
const renderedTemplate = {
  success: true, html_content: '<p>demo</p>', template_sha256: template.templateSha256,
  placeholders: template.fields.map((field) => field.id),
};
const partialFile = { success: true, file_bytes: 'ZGVtbw==', filename: 'demo.docx', total_fields: 37, filled_fields: 1 };
async function loadedHook(configOverride) {
  const fixture = hookFixture(configOverride);
  const loading = fixture.render().loadForm('demo', 'demo.docx');
  fixture.calls[0].resolve(renderedTemplate);
  await loading;
  return fixture;
}

test('late render cannot replace the newer selected template', async () => {
  const fixture = hookFixture();
  const old = fixture.render().loadForm('old', 'old.docx');
  const current = fixture.render().loadForm('new', 'new.docx');
  assert.equal(fixture.calls[0].signal.aborted, true);
  fixture.calls[1].resolve(renderedTemplate); await current;
  fixture.render().handleFieldChange('scan_ho_ten', 'NEW DRAFT');
  fixture.calls[0].resolve({ ...renderedTemplate, html_content: '<p>old</p>' }); await old;
  const state = fixture.render();
  assert.equal(state.templatePath, 'forms/new/new.docx');
  assert.equal(state.formHtml, '<p>demo</p>');
  assert.equal(state.draft.values.scan_ho_ten, 'NEW DRAFT');
});

test('template change clears the old draft and discards late QR data', async () => {
  const fixture = await loadedHook();
  fixture.render().handleFieldChange('scan_ho_ten', 'OLD DRAFT');
  const scanning = fixture.render().handleCCCDScan('synthetic-image');
  const loading = fixture.render().loadForm('unknown', 'unknown.docx');
  assert.deepEqual(fixture.render().draft, createFormDraft());
  assert.equal(fixture.calls[1].signal.aborted, true);
  fixture.calls[1].resolve({ success: true, data: card }); await scanning;
  fixture.calls[2].resolve({ ...renderedTemplate, template_sha256: '0'.repeat(64) }); await loading;
  const state = fixture.render();
  assert.deepEqual(state.draft, createFormDraft());
  assert.equal(state.templateConfig, null);
  assert.equal(state.selectedRole, 'reference');
});

test('generic multi-role QR completion uses the captured role, not a newly selected role', async () => {
  const fixture = await loadedHook(multiRoleTemplate);
  const scanning = fixture.render().handleCCCDScan('synthetic-image');
  assert.equal(fixture.calls[1].payload.scan_mode, 'qr');
  fixture.render().setSelectedRole('mother');
  fixture.calls[1].resolve({ success: true, data: card }); await scanning;
  const state = fixture.render();
  assert.equal(state.selectedRole, 'mother');
  assert.equal(state.draft.values.scan_ho_ten, card.field_ho_ten);
  assert.equal(state.draft.values.form_15, undefined);
  assert.equal(state.cccdData, null);
});

test('export sends the shared draft and refuses stale output after editing', async () => {
  const fixture = await loadedHook();
  fixture.render().handleFieldChange('scan_ho_ten', '  FIRST DRAFT  ');
  const filling = fixture.render().handleDownload();
  assert.deepEqual(fixture.calls[1].payload.data, { scan_ho_ten: 'FIRST DRAFT' });
  assert.equal(fixture.calls[1].payload.template_sha256, template.templateSha256);
  fixture.render().handleFieldChange('scan_ho_ten', 'SECOND DRAFT');
  fixture.calls[1].resolve(partialFile); await filling;
  const state = fixture.render();
  assert.equal(state.validationModal.isOpen, false);
  assert.equal(state.toast.variant, 'info');
  state.executeDownload(); // No DOM is provided: an old file must never be downloaded.
  assert.match(fixture.render().toast.message, /Bản nháp đã thay đổi/);
});

test('cancel or edit invalidates a pending download without saving a dossier', async () => {
  const fixture = await loadedHook();
  fixture.render().handleFieldChange('scan_ho_ten', 'DRAFT');
  let filling = fixture.render().handleDownload();
  fixture.calls[1].resolve(partialFile); await filling;
  assert.equal(fixture.render().validationModal.missingCount, 36);
  fixture.render().cancelDownload();
  assert.equal(fixture.render().validationModal.isOpen, false);
  fixture.render().executeDownload();
  assert.equal(fixture.render().toast.variant, 'info');
  filling = fixture.render().handleDownload();
  fixture.calls[2].resolve(partialFile); await filling;
  fixture.render().handleFieldChange('scan_ho_ten', 'CHANGED');
  assert.equal(fixture.render().validationModal.isOpen, false);
  assert.deepEqual(fixture.calls.map((call) => call.url), ['/render', '/fill', '/fill']);
});

test('only the latest export response may show a download confirmation', async () => {
  const fixture = await loadedHook();
  const first = fixture.render().handleDownload();
  const second = fixture.render().handleDownload();
  assert.equal(fixture.calls[1].signal.aborted, true);
  fixture.calls[1].resolve(partialFile); await first;
  assert.equal(fixture.render().validationModal.isOpen, false);
  assert.equal(fixture.render().downloadLoading, true);
  fixture.calls[2].resolve(partialFile); await second;
  assert.equal(fixture.render().validationModal.isOpen, true);
  assert.equal(fixture.render().downloadLoading, false);
});
