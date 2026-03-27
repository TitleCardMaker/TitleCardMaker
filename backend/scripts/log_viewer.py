from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from tempfile import gettempdir
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse


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


def _get_connection() -> sqlite3.Connection:
    if CURRENT_DB_PATH is None:
        raise HTTPException(status_code=400, detail='Upload a SQLite database first.')
    try:
        conn = sqlite3.connect(str(CURRENT_DB_PATH))
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail=f'Unable to open database: {exc}') from exc
    conn.row_factory = sqlite3.Row
    return conn


def _validate_schema(conn: sqlite3.Connection) -> None:
    table_row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='logs'"
    ).fetchone()
    if table_row is None:
        raise HTTPException(status_code=400, detail='Database does not contain a "logs" table.')

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
  </style>
</head>
<body>
  <div class="ui container">
    <h1 class="ui header">TitleCardMaker Log Viewer</h1>
    <p class="hint">Upload a logs SQLite DB, then filter by time, message text, and context IDs.</p>

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
      <p class="hint">Use quotes for phrases. Example: <code>failed "no route"</code></p>
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
        tbody.innerHTML = '<tr><td colspan="6">No matching logs.</td></tr>';
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
      const params = new URLSearchParams({
        start_time: document.getElementById('start-time').value.trim(),
        end_time: document.getElementById('end-time').value.trim(),
        message: document.getElementById('message-text').value.trim(),
        message_logic: document.getElementById('message-logic').value,
        context_ids: document.getElementById('context-ids').value.trim(),
        context_logic: document.getElementById('context-logic').value,
        limit: '1000',
      });

      queryStatus.textContent = 'Querying...';
      try {
        const response = await fetch(`/api/logs?${params.toString()}`);
        const payload = await response.json();
        if (!response.ok) {
          queryStatus.textContent = payload.detail ?? 'Query failed.';
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
        raise HTTPException(status_code=400, detail=f'Invalid SQLite database: {exc}') from exc
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

    where_sql = f"WHERE {' AND '.join(where)}" if where else ''
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
    params.extend([limit, offset])

    conn = _get_connection()
    try:
        _validate_schema(conn)
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail=f'Query failed: {exc}') from exc
    finally:
        conn.close()

    results = [dict(row) for row in rows]
    return {'count': len(results), 'results': results}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('scripts.log_viewer:APP', host='127.0.0.1', port=8050, reload=False)
