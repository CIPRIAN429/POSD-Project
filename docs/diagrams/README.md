# Diagram sources

The [visual guide](../visual-guide.md) embeds the SVG files in this directory. SVG works on GitHub and opens locally in a browser without starting the application. Each matching `.mmd` file is the editable Mermaid source. Labels and captions are in English, like the application documentation.

| Source and matching SVG | Purpose |
|---|---|
| `01-architecture` | Containers, HTTP boundary, database and private media |
| `02-navigation` | Roles, shared pages and administration |
| `03-data-model` | Core entities, cardinality and important constraints |
| `04-authorization` | PDF request, allow/deny/outage outcomes and audit |
| `05-enrollment-states` | Enrollment, waiting, promotion, withdrawal and completion |
| `06-last-seat` | PostgreSQL course-row locking across two requests |
| `07-course-lifecycle` | Draft, published and archived courses |

## Regenerate from WSL or Linux

Editing documentation does not require changes to the Docker application. Regeneration is an optional development task and requires Node.js 20 or later, npm and a Chromium-compatible browser supported by Puppeteer. The first run downloads the pinned renderer and may download Chromium; viewing the committed images needs neither Node nor internet.

From the project root:

```bash
bash docs/diagrams/render.sh
```

The script runs `@mermaid-js/mermaid-cli@11.12.0` with the shared `mermaid-config.json`. It updates SVG files only. Check every generated image, its labels and its arrows before committing; parser success alone does not establish that a diagram matches the code.

If Puppeteer cannot launch the browser, use an installed compatible browser through its standard `PUPPETEER_EXECUTABLE_PATH` environment variable or pass a Puppeteer JSON config as the script's first argument:

```bash
PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium bash docs/diagrams/render.sh
bash docs/diagrams/render.sh /absolute/path/to/puppeteer-config.json
```

## Keep the diagrams aligned with code

1. Change the `.mmd` source and the corresponding explanation in `docs/visual-guide.md`.
2. Regenerate the SVG and inspect it at normal size. Open a large diagram in a separate browser tab to zoom.
3. Check linked behavior against `learning/models.py`, `learning/forms.py`, `learning/services.py`, `learning/views.py`, `learning/authorization.py` and `policy_service/app/policies.py`.
4. Update the architecture notes, permissions or presentation outline if the behavior changed.

The diagrams omit routine framework tables and fields for readability. They describe implementation behavior, not measured performance or a formal security proof.
