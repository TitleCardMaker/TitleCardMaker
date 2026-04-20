from __future__ import annotations

import shutil
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from tempfile import gettempdir
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


APP = FastAPI(title='TitleCardMaker Log Viewer')

REQUIRED_COLUMNS = {
  'id',
  'timestamp',
  'level_name',
  'level_number',
  'message',
  'context_id',
  'exception_type',
  'exception_value',
  'exception_traceback',
}

UPLOAD_DIR = Path(gettempdir()) / 'tcm-log-viewer'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Single-process state for currently loaded DB.
CURRENT_DB_PATH: Path | None = None


def _parse_dt(value: str | None) -> str | None:
    if value is None or value.strip() == '':
        return None
    raw = value.strip()
    if raw.endswith('Z'):
        raw = raw[:-1] + '+00:00'
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f'Invalid datetime "{value}". Use ISO 8601 format.',
        ) from exc
    return parsed.isoformat(sep=' ')


def _parse_terms(message: str | None) -> list[str]:
    if not message:
        return []
    # Treat commas as optional separators; keep quoted phrases if present.
    import shlex

    normalized = message.replace(',', ' ')
    return [term for term in shlex.split(normalized) if term]


MAX_FILTER_DEPTH = 24
MAX_FILTER_CHILDREN = 64

LEAF_KEYS = frozenset({
    'message_contains',
    'context_id_equals',
    'timestamp_after',
    'timestamp_before',
    'date_after',
    'date_before',
})


def _parse_dt_strict(value: str, field: str) -> str:
    raw = value.strip()
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        msg = f'Invalid datetime for {field}: {value!r}. Use ISO 8601. ({exc})'
        raise ValueError(msg) from exc
    return parsed.isoformat(sep=' ')


def _as_calendar_date(value: str) -> date:
    raw = value.strip()
    if raw.endswith('Z'):
        raw = raw[:-1] + '+00:00'
    if 'T' in raw or ' ' in raw:
        try:
            return datetime.fromisoformat(raw).date()
        except ValueError as exc:
            raise ValueError(f'Invalid date/datetime: {value!r}') from exc
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f'Invalid date: {value!r}') from exc


def _compile_leaf(node: dict[str, Any]) -> tuple[str, list[Any]]:
    unknown = set(node) - LEAF_KEYS
    if unknown:
        raise ValueError(f'Unknown filter key(s): {sorted(unknown)}')
    keys = [k for k in node if k in LEAF_KEYS]
    if len(keys) != 1:
        raise ValueError('Each leaf must have exactly one filter key')
    key = keys[0]
    val = node[key]
    if not isinstance(val, str):
        raise ValueError(f'{key} value must be a string')

    if key == 'message_contains':
        if not val.strip():
            raise ValueError('message_contains must be non-empty')
        return 'LOWER(message) LIKE LOWER(?)', [f'%{val}%']

    if key == 'context_id_equals':
        if not val.strip():
            raise ValueError('context_id_equals must be non-empty')
        return 'LOWER(COALESCE(context_id, \'\')) = LOWER(?)', [val]

    if key == 'timestamp_after':
        bound = _parse_dt_strict(val, 'timestamp_after')
        return 'timestamp >= ?', [bound]

    if key == 'timestamp_before':
        bound = _parse_dt_strict(val, 'timestamp_before')
        return 'timestamp <= ?', [bound]

    if key == 'date_after':
        d = _as_calendar_date(val)
        nxt = datetime.combine(d + timedelta(days=1), datetime.min.time())
        return 'timestamp >= ?', [nxt.isoformat(sep=' ')]

    if key == 'date_before':
        d = _as_calendar_date(val)
        start = datetime.combine(d, datetime.min.time())
        return 'timestamp < ?', [start.isoformat(sep=' ')]

    raise ValueError(f'Unsupported filter key: {key}')


def compile_filter(
    node: dict[str, Any] | None, *, depth: int = 0
) -> tuple[str | None, list[Any]]:
    """Turn a JSON filter tree into SQL WHERE fragment and bound parameters."""
    if node is None or node == {}:
        return None, []
    if depth > MAX_FILTER_DEPTH:
        raise ValueError(f'Filter exceeds max nesting depth ({MAX_FILTER_DEPTH})')
    if not isinstance(node, dict):
        raise ValueError('Filter must be a JSON object')

    keys = set(node.keys())
    if 'all' in keys:
        if keys != {'all'}:
            raise ValueError('"all" node must only contain the "all" key')
        children = node['all']
        if not isinstance(children, list):
            raise ValueError('"all" must be a list')
        if len(children) > MAX_FILTER_CHILDREN:
            raise ValueError(f'At most {MAX_FILTER_CHILDREN} children per group')
        parts: list[str] = []
        params: list[Any] = []
        for child in children:
            if not isinstance(child, dict):
                raise ValueError('Each child of "all" must be an object')
            frag, p = compile_filter(child, depth=depth + 1)
            if frag:
                parts.append(f'({frag})')
                params.extend(p)
        if not parts:
            return None, []
        if len(parts) == 1:
            return parts[0][1:-1], params
        return ' AND '.join(parts), params

    if 'any' in keys:
        if keys != {'any'}:
            raise ValueError('"any" node must only contain the "any" key')
        children = node['any']
        if not isinstance(children, list):
            raise ValueError('"any" must be a list')
        if len(children) > MAX_FILTER_CHILDREN:
            raise ValueError(f'At most {MAX_FILTER_CHILDREN} children per group')
        if len(children) == 0:
            return '0', []
        parts = []
        params: list[Any] = []
        for child in children:
            if not isinstance(child, dict):
                raise ValueError('Each child of "any" must be an object')
            frag, p = compile_filter(child, depth=depth + 1)
            if frag:
                parts.append(f'({frag})')
                params.extend(p)
        if not parts:
            return '0', []
        if len(parts) == 1:
            return parts[0][1:-1], params
        return ' OR '.join(parts), params

    return _compile_leaf(node)


class LogQueryBody(BaseModel):
    filter: dict[str, Any] | None = Field(default=None)
    limit: int = Field(default=500, ge=1, le=5000)
    offset: int = Field(default=0, ge=0)


def _get_connection() -> sqlite3.Connection:
    if CURRENT_DB_PATH is None:
        raise HTTPException(status_code=400, detail='Upload a SQLite database first.')
    try:
        conn = sqlite3.connect(str(CURRENT_DB_PATH))
    except sqlite3.Error as exc:
        detail = f'Unable to open database: {exc}'
        raise HTTPException(status_code=500, detail=detail) from exc
    conn.row_factory = sqlite3.Row
    return conn


def _run_logs_query(
    where_frag: str | None,
    params: list[Any],
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    where_sql = f'WHERE {where_frag}' if where_frag else ''
    sql = f"""
        SELECT
            id,
            timestamp,
            level_name,
            level_number,
            message,
            context_id,
            exception_type,
            exception_value,
            exception_traceback
        FROM logs
        {where_sql}
        ORDER BY timestamp DESC, id DESC
        LIMIT ? OFFSET ?
    """
    qparams = [*params, limit, offset]
    conn = _get_connection()
    try:
        _validate_schema(conn)
        rows = conn.execute(sql, qparams).fetchall()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail=f'Query failed: {exc}') from exc
    finally:
        conn.close()
    return [dict(row) for row in rows]


def _validate_schema(conn: sqlite3.Connection) -> None:
    table_row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='logs'"
    ).fetchone()
    if table_row is None:
        raise HTTPException(
            status_code=400,
            detail='Database does not contain a "logs" table.',
        )

    pragma_rows = conn.execute("PRAGMA table_info('logs')").fetchall()
    cols = {row[1] for row in pragma_rows}
    missing = REQUIRED_COLUMNS.difference(cols)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f'Database "logs" table missing required columns: {sorted(missing)}',
        )


@APP.get('/', response_class=HTMLResponse)
def index() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>TCM Log Viewer</title>
  <link
    rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/fomantic-ui@2.9.3/dist/semantic.min.css"
  />
  <style>
    body { padding: 1.5rem 0; }
    .table-wrap { max-height: 65vh; overflow: auto; }
    .status { min-height: 1.35rem; margin-top: 0.5rem; }
    .hint { color: rgba(0, 0, 0, 0.6); }
    .filter-builder { margin-top: 0.5rem; }
    .fb-group {
      border: 1px solid rgba(0, 0, 0, 0.12);
      border-radius: 6px;
      padding: 0.75rem 0.75rem 0.5rem;
      margin: 0.5rem 0;
      background: rgba(0, 0, 0, 0.02);
    }
    .fb-group.fb-nested { margin-left: 0.75rem; }
    .fb-group-header {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.5rem;
    }
    .fb-group-header label { margin: 0; font-weight: 600; }
    .fb-logic { min-width: 5.5rem; }
    .fb-children { margin: 0.35rem 0; }
    .fb-condition {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.5rem;
      margin: 0.35rem 0;
    }
    .fb-type { min-width: 11rem; }
    .fb-value { flex: 1 1 12rem; min-width: 10rem; }
    .fb-group-actions { margin-top: 0.35rem; }
    .fb-group-actions .button { margin-right: 0.35rem !important; }
    .fb-select {
      padding: 0.4rem 0.5rem;
      border: 1px solid rgba(34, 36, 38, 0.35);
      border-radius: 4px;
      background: #fff;
      font-size: 0.9rem;
      cursor: pointer;
    }
    .fb-select:focus { outline: none; border-color: #85b7d9; }
  </style>
</head>
<body>
  <div class="ui container">
    <h1 class="ui header">TitleCardMaker Log Viewer</h1>
    <p class="hint">
      Upload a logs SQLite DB. Use quick fields and/or the visual filter builder
      (nested <code>AND</code>/<code>OR</code> groups).
    </p>

    <form class="ui segment form" id="upload-form">
      <div class="field">
        <label>SQLite database file</label>
        <input type="file" id="db-file" accept=".sqlite,.db,.sqlite3" required />
      </div>
      <button class="ui primary button" type="submit">Upload</button>
      <div class="status" id="upload-status"></div>
    </form>

    <section class="ui segment form">
      <div class="three fields">
        <div class="field">
          <label>Start time (ISO 8601)</label>
          <input id="start-time" placeholder="2026-03-20T00:00:00" />
        </div>
        <div class="field">
          <label>End time (ISO 8601)</label>
          <input id="end-time" placeholder="2026-03-26T23:59:59" />
        </div>
        <div class="field">
          <label>Message terms (space/comma separated)</label>
          <input id="message-text" placeholder='error timeout "api key"' />
        </div>
      </div>
      <div class="three fields">
        <div class="field">
          <label>Message term logic</label>
          <select class="ui dropdown" id="message-logic">
            <option value="and">AND</option>
            <option value="or">OR</option>
          </select>
        </div>
        <div class="field">
          <label>Context IDs (space/comma separated)</label>
          <input id="context-ids" placeholder='run-1234 "context alpha"' />
        </div>
        <div class="field">
          <label>Context ID logic</label>
          <select class="ui dropdown" id="context-logic">
            <option value="and">AND</option>
            <option value="or">OR</option>
          </select>
        </div>
      </div>
      <p class="hint">
        Use quotes for phrases. Example: <code>failed "no route"</code>
      </p>

      <div class="ui divider"></div>
      <h4 class="ui header" style="margin-top: 0;">Advanced filter builder</h4>
      <p class="hint">
        Groups combine nested rules with <strong>All (AND)</strong> or
        <strong>Any (OR)</strong>. Each condition picks a field and a value.
        Date/time: ISO for timestamp fields; <code>YYYY-MM-DD</code> for date fields.
        Empty value rows are ignored. This stacks with the quick fields above
        (combined with AND).
      </p>
      <div id="filter-builder-root" class="filter-builder"></div>
      <button class="ui teal button" id="run-filter">Run Filter</button>
      <div class="status" id="query-status"></div>
    </section>

    <table class="ui compact celled striped table" id="results-table">
      <thead>
        <tr>
          <th>Timestamp</th>
          <th>Level</th>
          <th>Message</th>
          <th>Context ID</th>
          <th>Exception</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>

  <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/fomantic-ui@2.9.3/dist/semantic.min.js"></script>
  <script>
    $('.ui.dropdown').dropdown();

    const FB_ROOT = document.getElementById('filter-builder-root');

    const FB_CONDITION_TYPES = [
      ['message_contains', 'Message contains'],
      ['context_id_equals', 'Context ID equals'],
      ['timestamp_after', 'Timestamp on or after (ISO)'],
      ['timestamp_before', 'Timestamp on or before (ISO)'],
      ['date_after', 'Date after (YYYY-MM-DD)'],
      ['date_before', 'Date before (YYYY-MM-DD)'],
    ];

    function fbPlaceholderForType(type) {
      const map = {
        message_contains: 'Substring…',
        context_id_equals: 'Exact context id',
        timestamp_after: '2026-04-30T00:00:00',
        timestamp_before: '2026-04-30T23:59:59',
        date_after: '2026-04-30',
        date_before: '2026-04-30',
      };
      return map[type] ?? '';
    }

    function makeConditionRow(type, value) {
      const t = type || 'message_contains';
      const row = document.createElement('div');
      row.className = 'fb-condition';
      const sel = document.createElement('select');
      sel.className = 'fb-select fb-type';
      sel.setAttribute('aria-label', 'Condition type');
      for (const [optVal, label] of FB_CONDITION_TYPES) {
        const opt = document.createElement('option');
        opt.value = optVal;
        opt.textContent = label;
        if (optVal === t) opt.selected = true;
        sel.appendChild(opt);
      }
      const inp = document.createElement('input');
      inp.type = 'text';
      inp.className = 'fb-value';
      if (value != null && value !== '') inp.value = value;
      inp.placeholder = fbPlaceholderForType(sel.value);
      sel.addEventListener('change', () => {
        inp.placeholder = fbPlaceholderForType(sel.value);
      });
      const rm = document.createElement('button');
      rm.type = 'button';
      rm.className = 'ui mini button fb-remove-condition';
      rm.textContent = 'Remove';
      row.append(sel, inp, rm);
      return row;
    }

    function makeGroup(isRoot, logic) {
      const g = document.createElement('div');
      g.className = 'fb-group' + (isRoot ? '' : ' fb-nested');
      if (isRoot) g.dataset.fbRoot = 'true';
      g.innerHTML = `
        <div class="fb-group-header">
          <label>Match</label>
          <select class="fb-select fb-logic" aria-label="Group logic">
            <option value="all">All (AND)</option>
            <option value="any">Any (OR)</option>
          </select>
          <button type="button" class="ui mini button fb-remove-group"
            ${isRoot ? 'style="display:none"' : ''}>Remove group</button>
        </div>
        <div class="fb-children"></div>
        <div class="fb-group-actions">
          <button type="button" class="ui mini primary button fb-add-condition">
            + Condition
          </button>
          <button type="button" class="ui mini button fb-add-group">
            + Group
          </button>
        </div>
      `;
      const logicSel = g.querySelector('.fb-logic');
      if (logic === 'any') logicSel.value = 'any';
      return g;
    }

    function serializeGroup(groupEl) {
      const logic = groupEl.querySelector('.fb-logic').value;
      const box = groupEl.querySelector(':scope > .fb-children');
      const parts = [];
      for (const child of box.children) {
        if (child.classList.contains('fb-group')) {
          const inner = serializeGroup(child);
          if (inner) parts.push(inner);
        } else if (child.classList.contains('fb-condition')) {
          const kind = child.querySelector('.fb-type').value;
          const val = child.querySelector('.fb-value').value.trim();
          if (!val) continue;
          parts.push({ [kind]: val });
        }
      }
      if (parts.length === 0) return null;
      if (parts.length === 1) return parts[0];
      return { [logic]: parts };
    }

    function buildFilterFromBuilder() {
      const root = FB_ROOT.querySelector('.fb-group');
      if (!root) return null;
      return serializeGroup(root);
    }

    function mergeQuickAndBuilder() {
      const quick = buildFilterFromForm();
      const adv = buildFilterFromBuilder();
      const stack = [];
      if (quick) stack.push(quick);
      if (adv) stack.push(adv);
      if (stack.length === 0) return null;
      if (stack.length === 1) return stack[0];
      return { all: stack };
    }

    function mountExampleFilterBuilder() {
      FB_ROOT.innerHTML = '';
      const root = makeGroup(true);
      FB_ROOT.appendChild(root);
      const sub = makeGroup(false, 'any');
      sub.querySelector('.fb-children').appendChild(
        makeConditionRow('message_contains', 'substring'),
      );
      sub.querySelector('.fb-children').appendChild(
        makeConditionRow('message_contains', 'test'),
      );
      root.querySelector('.fb-children').appendChild(sub);
      root.querySelector('.fb-children').appendChild(
        makeConditionRow('date_after', '2026-04-30'),
      );
    }

    FB_ROOT.addEventListener('click', (e) => {
      const addCond = e.target.closest('.fb-add-condition');
      if (addCond) {
        const group = addCond.closest('.fb-group');
        group.querySelector('.fb-children').appendChild(makeConditionRow());
        return;
      }
      const addGrp = e.target.closest('.fb-add-group');
      if (addGrp) {
        const group = addGrp.closest('.fb-group');
        group.querySelector('.fb-children').appendChild(makeGroup(false));
        return;
      }
      const rmCond = e.target.closest('.fb-remove-condition');
      if (rmCond) {
        const row = rmCond.closest('.fb-condition');
        row?.remove();
        return;
      }
      const rmGrp = e.target.closest('.fb-remove-group');
      if (rmGrp) {
        const g = rmGrp.closest('.fb-group');
        if (g?.dataset.fbRoot === 'true') return;
        g?.remove();
      }
    });

    mountExampleFilterBuilder();

    function splitTerms(input) {
      if (!input || !input.trim()) return [];
      const normalized = input.replace(/,/g, ' ');
      const out = [];
      const re = /"([^"]*)"|'([^']*)'|(\\S+)/g;
      let m;
      while ((m = re.exec(normalized)) !== null) {
        const token = m[1] ?? m[2] ?? m[3];
        if (token) out.push(token);
      }
      return out;
    }

    function buildFilterFromForm() {
      const start = document.getElementById('start-time').value.trim();
      const end = document.getElementById('end-time').value.trim();
      const messageRaw = document.getElementById('message-text').value.trim();
      const messageLogic = document.getElementById('message-logic').value;
      const contextRaw = document.getElementById('context-ids').value.trim();
      const contextLogic = document.getElementById('context-logic').value;

      const parts = [];
      if (start) parts.push({ timestamp_after: start });
      if (end) parts.push({ timestamp_before: end });

      const terms = splitTerms(messageRaw);
      if (terms.length) {
        const leaves = terms.map((t) => ({ message_contains: t }));
        parts.push(messageLogic === 'and' ? { all: leaves } : { any: leaves });
      }

      const contexts = splitTerms(contextRaw);
      if (contexts.length) {
        const leaves = contexts.map((c) => ({ context_id_equals: c }));
        parts.push(contextLogic === 'and' ? { all: leaves } : { any: leaves });
      }

      if (parts.length === 0) return null;
      if (parts.length === 1) return parts[0];
      return { all: parts };
    }

    const uploadForm = document.getElementById('upload-form');
    const uploadStatus = document.getElementById('upload-status');
    const queryStatus = document.getElementById('query-status');
    const tbody = document.querySelector('#results-table tbody');

    function escapeHtml(text) {
      return text
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }

    function renderRows(rows) {
      tbody.innerHTML = '';
      if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="5">No matching logs.</td></tr>';
        return;
      }
      const html = rows.map((row) => {
        const exception = [row.exception_type, row.exception_value]
          .filter(Boolean)
          .join(': ');
        return `
          <tr>
            <td>${escapeHtml(String(row.timestamp ?? ''))}</td>
            <td>${escapeHtml(String(row.level_name ?? ''))}</td>
            <td>${escapeHtml(String(row.message ?? ''))}</td>
            <td>${escapeHtml(String(row.context_id ?? ''))}</td>
            <td>${escapeHtml(exception)}</td>
          </tr>
        `;
      }).join('');
      tbody.innerHTML = html;
    }

    uploadForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const fileInput = document.getElementById('db-file');
      const file = fileInput.files?.[0];
      if (!file) {
        uploadStatus.textContent = 'Select a file first.';
        return;
      }
      const formData = new FormData();
      formData.append('file', file);
      uploadStatus.textContent = 'Uploading...';
      try {
        const response = await fetch('/api/upload', { method: 'POST', body: formData });
        const payload = await response.json();
        if (!response.ok) {
          uploadStatus.textContent = payload.detail ?? 'Upload failed.';
          return;
        }
        uploadStatus.textContent = `Uploaded: ${payload.filename}`;
        queryStatus.textContent = 'Run filter to load logs.';
      } catch (error) {
        uploadStatus.textContent = `Upload error: ${error}`;
      }
    });

    document.getElementById('run-filter').addEventListener('click', async (event) => {
      event.preventDefault();
      const filter = mergeQuickAndBuilder();

      queryStatus.textContent = 'Querying...';
      try {
        const response = await fetch('/api/logs/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filter, limit: 1000, offset: 0 }),
        });
        const payload = await response.json();
        if (!response.ok) {
          const detail = payload.detail;
          const errText = typeof detail === 'string'
            ? detail
            : JSON.stringify(detail ?? 'Query failed.');
          queryStatus.textContent = errText;
          renderRows([]);
          return;
        }
        queryStatus.textContent = `Showing ${payload.count} row(s).`;
        renderRows(payload.results);
      } catch (error) {
        queryStatus.textContent = `Query error: ${error}`;
        renderRows([]);
      }
    });
  </script>
</body>
</html>
    """


@APP.post('/api/upload')
async def upload_db(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail='Missing filename.')
    if not file.filename.lower().endswith(('.sqlite', '.db', '.sqlite3')):
        raise HTTPException(status_code=400, detail='Upload a SQLite file.')

    destination = UPLOAD_DIR / file.filename
    with destination.open('wb') as output:
        shutil.copyfileobj(file.file, output)

    try:
        conn = sqlite3.connect(str(destination))
        _validate_schema(conn)
    except HTTPException:
        destination.unlink(missing_ok=True)
        raise
    except sqlite3.Error as exc:
        destination.unlink(missing_ok=True)
        detail = f'Invalid SQLite database: {exc}'
        raise HTTPException(status_code=400, detail=detail) from exc
    finally:
        try:
            conn.close()  # type: ignore[reportPossiblyUnboundVariable]
        except Exception:
            pass

    global CURRENT_DB_PATH
    CURRENT_DB_PATH = destination
    return {'filename': file.filename}


@APP.get('/api/logs')
def query_logs(
    start_time: str | None = Query(default=None),
    end_time: str | None = Query(default=None),
    message: str | None = Query(default=None),
    message_logic: str = Query(default='and', pattern='^(and|or)$'),
    context_ids: str | None = Query(default=None),
    context_logic: str = Query(default='or', pattern='^(and|or)$'),
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    start_dt = _parse_dt(start_time)
    end_dt = _parse_dt(end_time)
    terms = _parse_terms(message)
    contexts = _parse_terms(context_ids)

    where: list[str] = []
    params: list[Any] = []

    if start_dt is not None:
        where.append('timestamp >= ?')
        params.append(start_dt)
    if end_dt is not None:
        where.append('timestamp <= ?')
        params.append(end_dt)

    if terms:
        joiner = ' AND ' if message_logic == 'and' else ' OR '
        fragments = []
        for term in terms:
            fragments.append('LOWER(message) LIKE LOWER(?)')
            params.append(f'%{term}%')
        where.append(f'({joiner.join(fragments)})')

    if contexts:
        joiner = ' AND ' if context_logic == 'and' else ' OR '
        fragments = []
        for context in contexts:
            fragments.append('LOWER(COALESCE(context_id, \'\')) = LOWER(?)')
            params.append(context)
        where.append(f'({joiner.join(fragments)})')

    where_frag = ' AND '.join(where) if where else None
    results = _run_logs_query(where_frag, params, limit, offset)
    return {'count': len(results), 'results': results}


@APP.post('/api/logs/query')
def query_logs_with_filter(body: LogQueryBody) -> dict[str, Any]:
    try:
        where_frag, filter_params = compile_filter(body.filter)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    results = _run_logs_query(where_frag, filter_params, body.limit, body.offset)
    return {'count': len(results), 'results': results}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('scripts.log_viewer:APP', host='127.0.0.1', port=8050, reload=False)
