const SHEET_NAME = "O'Reilly resources";
const SHEET_LIVE = "O'Reilly live";
const SHEET_AUTHORS = "O'Reilly authors";
const NUM_RESOURCES = 200;

const BASE_API_URL = "https://learning.oreilly.com/api/v2/search/";
const RESOURCE_FORMATS = ["book", "article", "video"];
const LIVE_FORMATS = ["live online training"];
const SORT_FIELD = "publication_date";
const SORT_ORDER = "desc";
const LIVE_SORT_ORDER = "asc";
const OPEN_LABEL = "Open";
const SELECT_HIGHLIGHT_COLOR = "#b7e1cd";
const RESOURCE_BASE_HEADERS = [
  "id",
  "select",
  "publisher",
  "title",
  "edition",
  "url",
  "issued",
  "last modified",
  "format",
  "video classification",
  "quiz",
  "time required",
];
const LIVE_BASE_HEADERS = [
  "id",
  "select",
  "publisher",
  "title",
  "url",
  "start_datetime",
  "end_datetime",
  "format",
];

function getAllOreilly() {
  Logger.log("Starting O'Reilly resources sync...");
  getResources();
  Logger.log("Starting O'Reilly live events sync...");
  getLiveEvents();
  Logger.log("O'Reilly sync finished.");
}

function getResources() {
  syncSheetByConfig({
    sheetName: SHEET_NAME,
    formats: RESOURCE_FORMATS,
    sort: SORT_FIELD,
    order: SORT_ORDER,
    limit: NUM_RESOURCES,
    issuedBefore: Utilities.formatDate(new Date(), "UTC", "yyyy-MM-dd"),
    logLabel: "resource",
    baseHeaders: RESOURCE_BASE_HEADERS,
    mode: "resources",
  });
}

function getLiveEvents() {
  syncSheetByConfig({
    sheetName: SHEET_LIVE,
    formats: LIVE_FORMATS,
    sort: SORT_FIELD,
    order: LIVE_SORT_ORDER,
    limit: NUM_RESOURCES,
    issuedBefore: "",
    logLabel: "live event",
    baseHeaders: LIVE_BASE_HEADERS,
    mode: "live",
    enforceSchema: true,
  });
}

function syncSheetByConfig({ sheetName, formats, sort, order, limit, issuedBefore, logLabel, baseHeaders, mode, enforceSchema }) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);
  const authorsSheet = ss.getSheetByName(SHEET_AUTHORS);

  if (!sheet) throw new Error(`Sheet "${sheetName}" not found.`);
  if (!authorsSheet) throw new Error(`Sheet "${SHEET_AUTHORS}" not found.`);

  const allowedAuthors = getAuthorsFromSheet(authorsSheet);
  if (!allowedAuthors.length) throw new Error(`No authors found in "${SHEET_AUTHORS}".`);

  // Ensure author columns exist only for names from authors sheet
  const headers = ensureHeaders(sheet, allowedAuthors, baseHeaders, enforceSchema);
  ensureIdColumnAsText(sheet, headers);

  // Existing IDs in sheet
  const existingIds = getExistingIds(sheet);

  // Fetch from O'Reilly API
  const resources = fetchResources({
    limit,
    allowedAuthors,
    formats,
    sort,
    order,
    issuedBefore,
  });

  // Build rows for IDs not already present
  const newRows = [];
  for (const resource of resources) {
    const candidateRows = mode === "live"
      ? buildLiveRows(resource, headers, allowedAuthors)
      : [buildRow(resource, headers, allowedAuthors)];

    for (const row of candidateRows) {
      const rowId = row[0];
      const idKey = normalizeIdForComparison(rowId);
      if (!idKey || existingIds.has(idKey)) continue;
      newRows.push(row);
      existingIds.add(idKey);
    }
  }

  if (!newRows.length) {
    applySelectRowHighlight(sheet, headers);
    Logger.log(`No new ${logLabel}s to add in "${sheetName}".`);
    return;
  }

  // Insert on top (below header row)
  sheet.insertRowsAfter(1, newRows.length);
  const normalizedRows = normalizeRowsForWrite(newRows, headers);
  sheet.getRange(2, 1, normalizedRows.length, headers.length).setValues(normalizedRows);
  applySelectRowHighlight(sheet, headers);

  Logger.log(`Added ${newRows.length} new ${logLabel}(s) at the top of "${sheetName}".`);
}

function applySelectRowHighlight(sheet, headers) {
  const selectIndex = headers.findIndex(h => normalizeName(h) === "select");
  if (selectIndex === -1) return;

  const lastRow = sheet.getLastRow();
  const lastCol = headers.length;
  if (lastRow < 2 || lastCol < 1) return;

  const rowCount = lastRow - 1;
  const selectValues = sheet.getRange(2, selectIndex + 1, rowCount, 1).getValues();

  const backgrounds = selectValues.map(([value]) => {
    const isSelected = toText(value).trim() !== "";
    const color = isSelected ? SELECT_HIGHLIGHT_COLOR : null;
    return new Array(lastCol).fill(color);
  });

  sheet.getRange(2, 1, rowCount, lastCol).setBackgrounds(backgrounds);
}

function getAuthorsFromSheet(authorsSheet) {
  const lastRow = authorsSheet.getLastRow();
  if (lastRow < 1) return [];

  const values = authorsSheet.getRange(1, 1, lastRow, 1).getValues().flat();
  const cleaned = values
    .map(v => toText(v).trim())
    .filter(Boolean);

  // skip optional header if present
  const filtered = cleaned.filter(name => normalizeName(name) !== "author");

  const dedup = new Map();
  for (const name of filtered) {
    const key = normalizeName(name);
    if (!dedup.has(key)) dedup.set(key, name);
  }
  return [...dedup.values()];
}

function ensureHeaders(sheet, authors, baseHeaders, enforceSchema) {

  const lastCol = Math.max(sheet.getLastColumn(), 1);
  const currentHeaders = sheet.getRange(1, 1, 1, lastCol).getValues()[0].map(toText);

  const desiredHeaders = [...baseHeaders, ...authors];

  // If row 1 is empty, initialize full header
  const hasAnyHeader = currentHeaders.some(h => h.trim() !== "");
  if (!hasAnyHeader) {
    sheet.getRange(1, 1, 1, desiredHeaders.length).setValues([desiredHeaders]);
    return desiredHeaders;
  }

  if (enforceSchema) {
    enforceSheetSchema(sheet, desiredHeaders);
    return desiredHeaders;
  }

  // Ensure base headers exist (append missing in order)
  const headerSet = new Set(currentHeaders.map(normalizeName));
  const missingBase = baseHeaders.filter(h => !headerSet.has(normalizeName(h)));
  let headers = [...currentHeaders];

  if (missingBase.length) {
    headers = headers.concat(missingBase);
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  }

  // Ensure author columns exist ONLY for authors in authors sheet
  const updatedHeaderSet = new Set(headers.map(normalizeName));
  const missingAuthors = authors.filter(a => !updatedHeaderSet.has(normalizeName(a)));
  if (missingAuthors.length) {
    headers = headers.concat(missingAuthors);
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  }

  return headers;
}

function enforceSheetSchema(sheet, desiredHeaders) {
  const lastRow = sheet.getLastRow();
  const lastCol = Math.max(sheet.getLastColumn(), 1);

  const oldHeaders = sheet.getRange(1, 1, 1, lastCol).getValues()[0].map(toText);
  const oldHeaderIndex = new Map(oldHeaders.map((h, i) => [normalizeName(h), i]));

  if (lastRow > 1) {
    const oldData = sheet.getRange(2, 1, lastRow - 1, lastCol).getValues();
    const oldFormulas = sheet.getRange(2, 1, lastRow - 1, lastCol).getFormulas();
    const oldDisplayData = sheet.getRange(2, 1, lastRow - 1, lastCol).getDisplayValues();
    const newData = oldData.map((oldRow, rowIndex) => {
      const oldFormulaRow = oldFormulas[rowIndex];
      const oldDisplayRow = oldDisplayData[rowIndex];
      const mappedRow = new Array(desiredHeaders.length).fill("");
      desiredHeaders.forEach((header, idx) => {
        const oldIdx = oldHeaderIndex.get(normalizeName(header));
        if (oldIdx === undefined) return;
        if (normalizeName(header) === "id") {
          mappedRow[idx] = toIdCellValue(oldDisplayRow[oldIdx]);
          return;
        }
        const formula = oldFormulaRow[oldIdx];
        mappedRow[idx] = formula || oldRow[oldIdx];
      });
      return mappedRow;
    });

    sheet.getRange(1, 1, 1, desiredHeaders.length).setValues([desiredHeaders]);
    const normalizedData = normalizeRowsForWrite(newData, desiredHeaders);
    sheet.getRange(2, 1, normalizedData.length, desiredHeaders.length).setValues(normalizedData);
  } else {
    sheet.getRange(1, 1, 1, desiredHeaders.length).setValues([desiredHeaders]);
  }

  if (lastCol > desiredHeaders.length) {
    sheet.deleteColumns(desiredHeaders.length + 1, lastCol - desiredHeaders.length);
  }

  ensureIdColumnAsText(sheet, desiredHeaders);
}

function normalizeRowsForWrite(rows, headers) {
  const idIndex = headers.findIndex(h => normalizeName(h) === "id");
  if (idIndex === -1) return rows;

  return rows.map(row => {
    const cloned = [...row];
    cloned[idIndex] = toIdCellValue(cloned[idIndex]);
    return cloned;
  });
}

function ensureIdColumnAsText(sheet, headers) {
  const idIndex = headers.findIndex(h => normalizeName(h) === "id");
  if (idIndex === -1) return;

  const rowCount = Math.max(sheet.getMaxRows(), 1);
  sheet.getRange(1, idIndex + 1, rowCount, 1).setNumberFormat("@");
}

function toIdCellValue(value) {
  const id = normalizeId(value);
  if (!id) return "";
  return `'${id}`;
}

function getExistingIds(sheet) {
  const lastRow = sheet.getLastRow();
  const ids = new Set();

  if (lastRow < 2) return ids;

  const values = sheet.getRange(2, 1, lastRow - 1, 1).getDisplayValues().flat();
  for (const v of values) {
    const norm = normalizeIdForComparison(v);
    if (norm) ids.add(norm);
  }
  return ids;
}

function fetchResources({ limit, allowedAuthors, formats, sort, order, issuedBefore }) {
  const query = allowedAuthors.map(name => `author:"${name}"`).join(" OR ");

  const params = {
    query,
    formats,
    sort,
    order,
    limit,
  };

  if (issuedBefore) {
    params.issued_before = issuedBefore;
  }

  const url = `${BASE_API_URL}?${toQueryString(params)}`;
  console.log(`Fetching O'Reilly API with URL: ${url}`);

  const response = UrlFetchApp.fetch(url, {
    method: "get",
    muteHttpExceptions: true,
    headers: { Accept: "application/json" },
  });

  const code = response.getResponseCode();
  const body = response.getContentText();

  if (code < 200 || code >= 300) {
    throw new Error(`O'Reilly API error ${code}: ${body}`);
  }

  const data = JSON.parse(body);
  return Array.isArray(data.results) ? data.results : [];
}

function buildRow(resource, headers, authorColumns) {
  const row = new Array(headers.length).fill("");

  const headerIndex = new Map(headers.map((h, i) => [normalizeName(h), i]));

  const archiveId = toText(resource.archive_id);
  const title = toText(resource.title);
  const webUrl = toText(resource.web_url);
  const fullUrl = webUrl ? `https://learning.oreilly.com${webUrl}` : "";

  setCell(row, headerIndex, "id", `'${archiveId}`);
  setCell(row, headerIndex, "select", ""); // default empty
  setCell(row, headerIndex, "publisher", toPublisher(resource.publishers));
  setCell(row, headerIndex, "title", title);
  setCell(row, headerIndex, "edition", extractEditionFromTitle(title));
  setCell(row, headerIndex, "url", toHyperlinkFormulaWithLabel(fullUrl, OPEN_LABEL));
  setCell(row, headerIndex, "issued", toLocalTimeLabel(resource.issued));
  setCell(row, headerIndex, "last modified", toLocalTimeLabel(resource.last_modified_time));
  setCell(row, headerIndex, "format", toText(resource.format));
  setCell(row, headerIndex, "video classification", toText(resource.video_classification));
  setCell(row, headerIndex, "quiz", extractHasQuizFromDescription(resource.description));
  setCell(row, headerIndex, "time required", toHoursMinutesFromMinutes(resource.minutes_required));

  const resourceAuthors = toAuthorsList(resource.authors);
  const resourceAuthorKeys = new Set(resourceAuthors.map(normalizeName));

  for (const author of authorColumns) {
    if (resourceAuthorKeys.has(normalizeName(author))) {
      const idx = headerIndex.get(normalizeName(author));
      if (idx !== undefined) row[idx] = toAuthorHyperlinkFormula(author);
    }
  }

  return row;
}

function buildLiveRows(resource, headers, authorColumns) {
  const events = toEventsArray(resource.events);
  if (!events.length) return [];

  const useEventTitle = events.length > 1;
  const rows = [];

  for (const event of events) {
    const eventId = toText(event.event_id);
    if (!eventId) continue;

    const row = new Array(headers.length).fill("");
    const headerIndex = new Map(headers.map((h, i) => [normalizeName(h), i]));

    const resourceTitle = toText(resource.title);
    const eventTitle = toText(event.title);
    const title = useEventTitle ? (eventTitle || resourceTitle) : resourceTitle;

    const webUrl = toText(resource.web_url);
    const fallbackUrl = toText(event.on24_url);
    const fullUrl = webUrl ? `https://learning.oreilly.com${webUrl}` : fallbackUrl;

    setCell(row, headerIndex, "id", `'${eventId}`);
    setCell(row, headerIndex, "select", "");
    setCell(row, headerIndex, "publisher", toPublisher(resource.publishers));
    setCell(row, headerIndex, "title", title);
    setCell(row, headerIndex, "url", toHyperlinkFormulaWithLabel(fullUrl, OPEN_LABEL));
    setCell(row, headerIndex, "start_datetime", toLocalTimeLabel(event.start_datetime));
    setCell(row, headerIndex, "end_datetime", toLocalTimeLabel(event.end_datetime));
    setCell(row, headerIndex, "format", toText(resource.format));

    const resourceAuthors = toAuthorsList(resource.authors);
    const resourceAuthorKeys = new Set(resourceAuthors.map(normalizeName));
    for (const author of authorColumns) {
      if (resourceAuthorKeys.has(normalizeName(author))) {
        const idx = headerIndex.get(normalizeName(author));
        if (idx !== undefined) row[idx] = toAuthorHyperlinkFormula(author);
      }
    }

    rows.push(row);
  }

  return rows;
}

function toEventsArray(value) {
  if (Array.isArray(value)) return value;

  if (typeof value === "string") {
    const text = value.trim();
    if (!text) return [];
    try {
      const parsed = JSON.parse(text);
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      Logger.log(`Unable to parse events JSON for resource: ${error}`);
      return [];
    }
  }

  return [];
}

function setCell(row, headerIndex, headerName, value) {
  const idx = headerIndex.get(normalizeName(headerName));
  if (idx !== undefined) row[idx] = value;
}

function toPublisher(value) {
  if (Array.isArray(value)) {
    const cleaned = value.map(toText).map(s => s.trim()).filter(Boolean);
    return cleaned.length ? cleaned[0] : "";
  }
  return toText(value);
}

function toAuthorsList(value) {
  if (!Array.isArray(value)) return [];
  return value
    .map(toText)
    .map(s => s.trim().replace(/\s+/g, " "))
    .filter(Boolean);
}

function extractEditionFromTitle(title) {
  const text = toText(title);
  if (!text) return "";

  let m = text.match(/(\d+)(?:st|nd|rd|th)?\s+edition/i);
  if (m) return m[1];

  const words = {
    first: "1",
    second: "2",
    third: "3",
    fourth: "4",
    fifth: "5",
    sixth: "6",
    seventh: "7",
    eighth: "8",
    ninth: "9",
    tenth: "10",
  };

  for (const [word, num] of Object.entries(words)) {
    if (new RegExp(`\\b${word}\\b\\s+edition`, "i").test(text)) return num;
  }

  return "";
}

function extractHasQuizFromDescription(description) {
  const text = toText(description).toLowerCase();
  return text.includes("with quizzes") ? "quiz" : "";
}

function toHoursMinutesFromMinutes(value) {
  if (value === null || value === undefined || value === "") return "";
  const n = Number(value);
  if (Number.isNaN(n)) return toText(value);

  const totalMinutes = Math.round(n);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

function toLocalTimeLabel(value) {
  const text = toText(value).trim();
  if (!text) return "";

  const dt = new Date(text);
  if (isNaN(dt.getTime())) return text;

  const tz = Session.getScriptTimeZone();
  return Utilities.formatDate(dt, tz, "yyyy-MM-dd HH:mm:ss");
}

function toHyperlinkFormulaWithLabel(url, label) {
  const safeLabel = escapeFormulaString(toText(label));
  if (!url) return safeLabel;

  const safeUrl = escapeFormulaString(toText(url));
  return `=HYPERLINK("${safeUrl}", "${safeLabel}")`;
}

function toAuthorHyperlinkFormula(name) {
  const query = encodeURIComponent(`author:"${name}"`);
  const url = `https://learning.oreilly.com/search/?q=${query}`;
  const safeUrl = escapeFormulaString(url);
  const safeName = escapeFormulaString(name);
  return `=HYPERLINK("${safeUrl}", "${safeName}")`;
}

function normalizeName(value) {
  return toText(value).trim().replace(/\s+/g, " ").toLowerCase();
}

function normalizeId(value) {
  return toText(value).trim().replace(/^'+/, "");
}

function normalizeIdForComparison(value) {
  const raw = normalizeId(value);
  if (!raw) return "";

  if (/^\d+$/.test(raw)) {
    const normalizedNumeric = raw.replace(/^0+/, "");
    return normalizedNumeric || "0";
  }

  return raw;
}

function toText(value) {
  if (value === null || value === undefined) return "";
  return String(value);
}

function escapeFormulaString(value) {
  return toText(value).replace(/"/g, '""');
}

function toQueryString(params) {
  const parts = [];

  for (const [key, val] of Object.entries(params)) {
    if (Array.isArray(val)) {
      for (const item of val) {
        parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(toText(item))}`);
      }
    } else if (val !== null && val !== undefined && val !== "") {
      parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(toText(val))}`);
    }
  }

  return parts.join("&");
}