# PhishShield UI

React frontend for PhishShield — the explainable phishing email analyzer.

## Setup

```bash
npm install
npm run dev
```

Opens at `http://localhost:5173`.

> **Note:** Backend must be running on `localhost:8000`. See [main README](../README.md) for backend setup.

## Features

- **Email input form** — Subject, body, from, reply-to fields
- **Quick-load samples** — Punycode, Shortener+OTP, Clean email presets
- **Results panel** — Score, severity, triggered rules with explanations
- **Text highlighting** — Visual markers showing detected content
- **Rule pack viewer** — Browse loaded detection rules
- **SOC workflow** — Copy JSON/text for incident documentation

## Project Structure

```
src/
├── api/
│   ├── client.ts      # API calls (analyzeEmail, fetchRules)
│   └── types.ts       # TypeScript interfaces
├── components/
│   ├── AnalyzerForm.tsx
│   ├── ResultsPanel.tsx
│   ├── HighlightedText.tsx
│   ├── RulePackPanel.tsx
│   └── SeverityBadge.tsx
├── lib/
│   ├── buildAnalyzedText.ts  # Reconstruct text for highlighting
│   ├── highlightSegments.ts  # Split text into highlight spans
│   └── clipboard.ts          # Copy to clipboard helper
├── App.tsx
├── main.tsx
└── styles.css
```

## Development

```bash
# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint
npm run lint
```

## Proxy Configuration

Vite proxies API requests to the backend. See `vite.config.ts`:

```typescript
proxy: {
  '/health': { target: 'http://localhost:8000' },
  '/analyze': { target: 'http://localhost:8000' },
  '/rules': { target: 'http://localhost:8000' },
}
```
