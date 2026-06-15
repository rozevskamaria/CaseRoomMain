# CaseRoom — IEI Clinical Case Simulator

**An AI-powered clinical case simulator for teaching Inborn Errors of Immunity to 5th-year medical students at Rīga Stradiņš University.**

Students take history from an AI parent, order investigations, submit differential diagnoses, and receive structured formative feedback — all in a realistic consultation format.

---

## What It Is

CaseRoom simulates the immunology outpatient consultation room. A clinical case opens with a brief description, a parent enters, and the student works through the case using four parallel tabs:

- 🗣 **History** — live conversation with the AI parent, who only reveals information when directly asked
- 🔬 **Investigations** — order any test in plain language; results appear instantly from a hardcoded case panel
- 📋 **Differentials** — submit and revise differential diagnoses; wrong paths trigger case-specific redirects
- ✅ **Final Answer** — structured submission covering diagnosis, management, genetic counselling, and explanation to the family

A contextual 💡 hint system tracks what the student has asked and ordered, and gives personalised guidance without revealing the diagnosis.

---

## Cases

| ID | Patient | Diagnosis | Difficulty |
|----|---------|-----------|------------|
| XLA | Mārtins, 2yo boy | X-linked Agammaglobulinaemia | Intermediate |
| CGD | Emils, 3yo boy | Chronic Granulomatous Disease | Advanced |
| PFAPA | Leila, 3yo girl | PFAPA Syndrome | Intermediate |
| HIES | Klāra, 13yo girl | Hyper-IgE Syndrome (STAT3 LOF) | Advanced |
| THI | Toms, 10mo boy | Transient Hypogammaglobulinaemia of Infancy | Beginner |
| SCID | Rihards, 2.5mo boy | Artemis SCID + maternal T-cell engraftment + BCGitis | Advanced |

Each case includes a full parent script with gated information, 10–20 investigation results with flagged abnormal values, case-specific wrong path redirects, model management, and model genetic counselling used for feedback generation.

---

## Tech Stack

- **React 18** (JSX, hooks)
- **Anthropic Claude API** (`claude-sonnet-4-20250514`) for parent voice, tutor feedback, and hint generation
- **Vite** for development and production build
- **Sucrase** for pre-compiling JSX to plain JavaScript for the standalone HTML build

Lab results, parent scripts, and model answers are entirely hardcoded in the source — the AI does not generate clinical content, only delivers and evaluates against it.

---

## Getting Started

### Prerequisites

- Node.js 18 or higher (`node --version` to check)
- An Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com)

### Setup with the script

Clone the repository and run the setup script:

```bash
git clone https://github.com/rozevskamaria/CaseRoom.git
cd CaseRoom
chmod +x setup.sh
./setup.sh
```

The script creates a Vite/React project, copies the source file in, and sets up the environment file.

Then add your API key to `.env`:

```
VITE_ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Start the development server:

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

### Manual setup

If you prefer to set up manually:

```bash
npm create vite@latest iei-simulator -- --template react
cd iei-simulator
npm install
cp ../IEI_Chatbot_v2.jsx src/App.jsx
```

Create `.env`:
```
VITE_ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Run:
```bash
npm run dev
```

---

## Standalone HTML File

A pre-compiled standalone HTML file (`IEI_Chatbot.html`) is included. It runs without a build step and without Node.js.

**Important:** the file must be served over HTTP, not opened directly from the filesystem. Safari and some other browsers block API calls from `file://` URLs.

To serve it locally:

```bash
cd /path/to/file
python3 -m http.server 8080
```

Then open [http://localhost:8080/IEI_Chatbot.html](http://localhost:8080/IEI_Chatbot.html).

To add your API key to the standalone file, open it in a text editor and find the `callClaude` function. Add the following to the headers object:

```javascript
"x-api-key": "sk-ant-your-key-here",
"anthropic-version": "2023-06-01",
"anthropic-dangerous-direct-browser-calls": "true"
```

---

## Rebuild the HTML after editing the JSX

After making changes to `IEI_Chatbot_v2.jsx`, rebuild the standalone file:

```bash
node -e "
const { transform } = require('/path/to/sucrase');
const fs = require('fs');
let src = fs.readFileSync('IEI_Chatbot_v2.jsx', 'utf8');
src = src.replace(/^import.*\n/, '').replace('export default function App()', 'function App()');
src = 'const { useState, useRef, useEffect } = React;\n' + src;
src += '\nReactDOM.createRoot(document.getElementById(\"root\")).render(React.createElement(App));\n';
const result = transform(src, { transforms: ['jsx'], jsxPragma: 'React.createElement', production: true });
const html = \`<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>CaseRoom — RSU</title><script src='https://cdnjs.cloudflare.com/ajax/libs/react/18.2.0/umd/react.production.min.js'></script><script src='https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.2.0/umd/react-dom.production.min.js'></script><style>*{box-sizing:border-box;margin:0;padding:0}body{background:#F8F6F0;font-family:'Segoe UI',Arial,sans-serif}#root{height:100vh}</style></head><body><div id='root'></div><script>\${result.code}</script></body></html>\`;
fs.writeFileSync('IEI_Chatbot.html', html);
console.log('Done');
"
```

---

## Deployment

Build for production:

```bash
npm run build
```

The output goes into the `dist/` folder. Upload it to any static web host (Netlify, Vercel, Azure Static Web Apps, university web server).

**Note:** when deploying, set `VITE_ANTHROPIC_API_KEY` as an environment variable in your hosting platform rather than committing it to the repository. The `.env` file is listed in `.gitignore` and should never be committed.

---

## Project Structure

```
CaseRoom/
├── IEI_Chatbot_v2.jsx     # Full source — all cases, logic, and UI
├── IEI_Chatbot.html        # Pre-compiled standalone HTML
├── setup.sh                # Setup script for Claude Code / Terminal
└── README.md
```

---

## Clinical Context

This project was developed as part of a clinical genetics residency and PhD research project at Rīga Stradiņš University, Faculty of Medicine. Cases are grounded in the Latvian clinical context — including the first genetically confirmed SCID case in Latvia and the national TREC/KREC-based newborn screening programme launched in April 2023.

All clinical content — lab values, parent scripts, model diagnoses, management plans, and genetic counselling points — was authored and reviewed by a clinical genetics specialist. The AI does not determine what is clinically correct; it delivers and evaluates against content written by the clinician-educator.

---

## Known Limitations

- Requires an Anthropic API key — the simulator makes direct browser-to-API calls
- Safari requires the file to be served over HTTP (localhost or hosted URL), not opened as a local file
- The AI parent voice may occasionally draw on general medical knowledge beyond the explicit case script
- No persistent student progress tracking across devices — progress is stored in the browser session only

---

## Author

**Marija Rozevska, MD**

---

*Created: March 2026*
