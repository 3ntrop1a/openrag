# Guide de contribution à OpenRAG

Merci de votre intérêt pour contribuer à OpenRAG ! 🎉

## Comment contribuer

### 1. Signaler des bugs

Si vous trouvez un bug, ouvrez une issue avec :
- Description claire du problème
- Étapes pour reproduire
- Comportement attendu vs actuel
- Logs pertinents
- Version d'OpenRAG et environnement

### 2. Proposer des fonctionnalités

Pour proposer une nouvelle fonctionnalité :
1. Ouvrez une issue "Feature Request"
2. Décrivez le cas d'usage
3. Expliquez comment ça devrait fonctionner
4. Attendez les retours avant d'implémenter

### 3. Soumettre du code

#### Setup de développement

```bash
# Cloner le repo
git clone https://github.com/your-org/openrag.git
cd openrag

# Créer une branche
git checkout -b feature/ma-fonctionnalite

# Setup l'environnement
make install
```

#### Standards de code

**Python**
- Suivre PEP 8
- Type hints obligatoires
- Docstrings pour les fonctions publiques
- Tests pour les nouvelles fonctionnalités

**Commits**
```
type(scope): description courte

Description détaillée si nécessaire

Fixes #123
```

Types : `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

#### Process de Pull Request

1. Fork le projet
2. Créez votre branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'feat: Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

**Checklist PR**
- [ ] Code suit les conventions
- [ ] Tests ajoutés/mis à jour
- [ ] Documentation mise à jour
- [ ] Pas de warnings
- [ ] Tests passent (`make test`)

### 4. Améliorer la documentation

La documentation est dans `/docs` (Mintlify).

```bash
cd docs
npx mintlify dev
```

### 5. Tester

```bash
# Lancer tous les tests
make test

# Tests spécifiques
pytest backend/tests/test_api.py
```

## Structure du projet

```
openrag/
├── backend/          # Code Python
│   ├── api/         # API Gateway
│   ├── services/    # Services (orchestrator, embedding)
│   └── database/    # Scripts SQL
├── docs/            # Documentation Mintlify
├── scripts/         # Scripts utilitaires
└── tests/           # Tests
```

## Priorités de contribution

### High Priority
- 🔐 Authentification et autorisation
- 📊 Dashboard web front-end
- 🧪 Tests unitaires et d'intégration
- 🌍 Support multilingue
- 📝 Plus d'exemples et tutoriels

### Medium Priority
- 🔌 Webhooks
- 📦 SDK (Python, JS, Go)
- 🎨 Templates de prompts personnalisables
- 📈 Analytics et métriques
- 🔧 Interface d'administration

### Nice to Have
- 🎤 Support audio (transcription)
- 🖼️ Support images (multimodal)
- 🔄 Import depuis Google Drive, Notion, etc.
- 🤖 Agents et workflows complexes

## Code de conduite

### Nos engagements

- Environnement accueillant et respectueux
- Respect de toutes les personnes
- Feedback constructif
- Focus sur ce qui est bon pour la communauté

### Comportements attendus

- ✅ Langage professionnel et respectueux
- ✅ Accepter les critiques constructives
- ✅ Montrer de l'empathie
- ✅ Focus sur les solutions

### Comportements inacceptables

- ❌ Harcèlement ou discrimination
- ❌ Trolling ou commentaires insultants
- ❌ Attaques personnelles ou politiques
- ❌ Publication d'informations privées

## Questions ?

- 💬 Discord : https://discord.gg/openrag
- 📧 Email : contribute@openrag.io
- 📚 Docs : https://docs.openrag.io

## Licence

En contribuant, vous acceptez que vos contributions soient sous licence MIT.

---

Merci de contribuer à OpenRAG ! 🚀
