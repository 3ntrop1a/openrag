# OpenRAG Frontend (Next.js + ShadcnUI)

Interface de chat moderne et sobre pour OpenRAG.

## Démarrage

```bash
cd frontend-nextjs
npm install
npm run dev
```

L'interface sera accessible sur http://localhost:3001 (port 3000 utilisé par Mintlify)

## Fonctionnalités

- Interface de chat responsive
- Affichage des sources avec scores de pertinence
- Design sobre avec ShadcnUI
- Support des requêtes en direct vers l'API OpenRAG

## API

L'application se connecte à `http://localhost:8000/query` (API Gateway OpenRAG).

Configuration dans `app/page.tsx`:
```typescript
fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: input,
    max_results: 5,
    use_llm: false
  })
});
```

## Composants

- **ShadcnUI**: Interface components (button, input, card, scroll-area, badge)
- **Lucide React**: Icons (Send, Loader2)
- **Tailwind CSS**: Styling

## Production

```bash
npm run build
npm start
```
