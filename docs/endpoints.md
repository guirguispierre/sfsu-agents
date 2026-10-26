# SFSU public endpoint notes (reverse-engineered 2026-10-12)

Everything below is reachable without login. Verified live with `sfsu-agents doctor`.

## Class schedule — `webapps.sfsu.edu`

The schedule app is a Symfony server-rendered app. The search form POSTs with a
CSRF token, but only to **build a clean GET URL** — you can skip the POST
entirely and call the results URL directly.

### 1. Bind a search (cookie session)

```
GET /public/classservices/classsearch/results?<params>
```

Stores the search in the session cookie and renders the results page.
Params:

| Param | Notes |
|---|---|
| `searchFor` | quick search: `CSC`, `CSC 413`, keyword. Ignores all advanced filters. |
| `subject` | advanced search anchor: `CSC`. Filters apply. |
| `categoryNumber` | catalog number filter, e.g. `413` |
| `term` | term code like `2267` (see below). When omitted the site default applies. |
| `classCategory` | `REG` academic regular, `CEL` CPaGE, `R1`-`R4` summer sub-sessions |
| `openUniversity` | `y`/`n` |
| `remainingSeats` | `y` |
| `meetingDays[i]` | `m tu w th f sa su` — repeat with index |
| `startTime`, `endTime` | 2-digit hour `08`–`21` |
| `location` | building code (`TH`, `BUS`, ...) |
| `instructorLastName` | substring |
| `courseAttributes` | GE attribute code (`3UD`, `1A`, ...) |
| `hybridClass`, `inPersonClass`, `onlineAsynchronous`, `onlineSynchronous`, `onlineBichronous` | `y` |

### 2. Fetch rows as JSON

```
GET /public/classservices/searchresultsjson   (same cookie jar; X-Requested-With optional)
→ {"aaData": [[cell0, cell1, ...], ...]}
```

Each cell is an HTML fragment. Column layout (from the site's own field comment):

```
course | type | title | units | class_number | attributes | meetings |
[date — summer only] | instruction_mode | instructors | [fee — CEL only] |
seats | waitlist | section | enroll_total
```

- cell 0 embeds the detail link `/classservices/classsearch/detail/{term}/{cat}/{classNumber}` and shows `SUBJ NUM [SECTION]` e.g. `CSC 413 [05]`.
- Optional summer Date and CEL Fee columns shift the tail; `parsers.parse_aa_row` detects them.

### 3. Section detail

```
GET /public/classservices/classsearch/detail/{term}/{category}/{classNumber}
```

Server-rendered: description, prerequisites, class notes, course attributes,
meeting table (type/days/times/location/dates/instructor), textbooks, seats/waitlist.

### Term codes

PeopleSoft-style: `2` + 2-digit year + term digit. `1`=Winter, `3`=Spring,
`5`=Summer, `7`=Fall. `2267`=Fall 2026, `2265`=Summer 2026, `2263`=Spring 2026.

The search form's session radio list enumerates every `term:category` pair
(e.g. `2267:REG`) with labels incl. date ranges for summer sessions — `terms`
scrapes that into a machine-readable map.

## Bulletin catalog — `bulletin.sfsu.edu` (CourseLeaf)

- `GET /courses/` — subject index (`/courses/{slug}/` links)
- `GET /courses/{slug}/` — all dept courses as `div.courseblock`
  (`.courseblocktitle` = `SUBJ NUM  Title (Units)`, `.courseblockextra` =
  prerequisites, `.courseblockdesc` = description)
- Slugs are lowercase dept codes (`csc`, `a_u`, `bccie`...). No JSON endpoint —
  server-rendered only.

## People directory — Algolia

`webapps.sfsu.edu/public/directorysearch/` is a React InstantSearch app. The
bundle embeds the public search-only credentials:

```
POST https://05XYDC2NJE-dsn.algolia.net/1/indexes/prod_DIRECTORYSEARCH/query
X-Algolia-Application-Id: 05XYDC2NJE
X-Algolia-API-Key: ab22c79867e4fa9ccede09f3c14cc3e0
{"query": "smith", "hitsPerPage": 20, "page": 0}
```

Hit fields: `first_name`, `middle_name`, `last_name`, `name_suffix`,
`email_addr`, `phone`, `sfo_office_locatn`, `positions[]` (`sfo_divcoll_name`,
`dept_title`, `sfo_classificatn` = FACULTY/STAFF/..., `csu_working_title`),
`objectID` (employee id). Facets allow `filters: "sfo_classificatn:FACULTY"`.

## Events calendar — `webapps.sfsu.edu/public/webcalendar`

A bootstrap-calendar widget fed by JSON:

```
GET /public/webcalendar/{slug}/listjson?from={ms}&to={ms}
→ {"success":1,"result":[{"id","title","url","class","start","end"}]}

GET /public/webcalendar/event/{id}.modal   → detail HTML fragment
GET /public/webcalendar/{slug}/ics/{start}/{period}/events.ics  → ICS feed
```

Calendar slugs (numeric ids; `all` = union): `14` General Interest,
`15` Lectures & Conferences, `16` Arts & Culture, `4` Alumni, `6` Athletics,
`acad` Academic (returns 0 upstream — academic dates flow through `all`/`14`).

## Not covered (auth-gated, out of scope)

mySFSU / PeopleSoft student center (enrollment cart, grades, transcripts,
degree progress), iLearn/Canvas, `cmsweb.sfsu.edu` HRMS pages.
