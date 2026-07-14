# 📑 GRC Copilot - Journal de Bord R&D (Phase 1 : Ingestion)

Ce document retrace les recherches exploratoires, les verrous techniques rencontrés et les choix d'architecture arrêtés lors de la phase de collecte et de préparation de la matière première réglementaire (**NIS2** / **DORA**).

---

## 🎯 Objectif de la Phase

L'objectif était d'extraire de manière **100 % fiable et structurée** les articles des directives européennes afin de nourrir une base vectorielle Qdrant. Un découpage sémantique parfait est indispensable pour éviter que le futur système multi-agents (`LangGraph`) ne souffre d'hallucinations par manque de contexte juridique.

---

## 🗺️ Les Pistes Creusées & Problèmes Rencontrés

### Piste 1 : Le Parsing des PDF officiels via `pypdf` (Abandonnée)

Nous avons initialement tenté d'extraire le texte brut directement depuis les PDF officiels d'EUR-Lex à l'aide de la bibliothèque Python `pypdf`.

* **Problème des Ligatures & Justification :** Le format PDF est conçu pour l'affichage visuel. Lors de l'extraction brute, des micro-espaces invisibles ont corrompu les mots (ex: `cybersécur ité`, `modif iant`, `ar ticle 114`).
* **Le Piège du "Ctrl + F" :** Une recherche textuelle naïve du mot "Article" renvoie toutes les citations internes aux phrases (plus de 410 occurrences pour NIS2), alors que le document ne contient que 46 articles réels.
* **Le Bruit des En-têtes :** Les titres de chapitres étaient parfois fusionnés avec les métadonnées de bas de page (ex: `Journal officiel... CHAPITRE III`), brisant les filtres de positionnement standard (`.startswith()`).
* **Le Fléau du "Tableau de Correspondance" :** À la fin du document, les colonnes des annexes ont été lues horizontalement par `pypdf`, fusionnant les anciens et les nouveaux articles sur une même ligne, créant d'importants doublons impossibles à filtrer proprement sans règles complexes.

---

## 💡 Le Pivot Stratégique : La Révolution HTML (Retenue)

> **Note d'architecture :** Face à la complexité et au manque de propreté du format PDF, nous avons opté pour un pivot vers le format **HTML source officiel** d'EUR-Lex. Ce choix transforme radicalement la qualité des données.

### Pourquoi le format HTML change tout ?

Le fichier HTML officiel de l'Union Européenne utilise le standard d'encodage **ELI (European Legislation Identifier)**. Ce format fournit une structure sémantique et native pensée pour les machines :

* **Zéro bug de texte :** Plus aucun problème d'espaces brisés au milieu des mots.
* **Balises de classes explicites :** Le document utilise des classes CSS strictes pour identifier la nature juridique du texte :
* `<p class="oj-ti-art">` : Cible uniquement le numéro des **vrais articles**.
* `<p class="oj-sti-art">` : Cible uniquement le **titre de l'article**.
* `<p class="oj-ti-section-1">` : Cible uniquement les **Chapitres**.



### Résultat du pivot

En appliquant un script basé sur les Expressions Régulières (`re`) ciblant ces classes spécifiques, le bruit a été réduit à **0 %**. Nous extrayons instantanément les **46 articles réels** de NIS2 avec une précision chirurgicale, sans aucune pollution issue des tableaux d'annexes.

---

## 🛠️ Stack Technique Validée (Notebook `research.ipynb`)

* **Environnement :** VS Code + Jupyter Notebook Extension (Python 3.13).
* **Extraction de données :** Module natif `re` (Expressions régulières) appliqué sur le code source HTML d'EUR-Lex.
* **Stockage Vectoriel ciblé :** Qdrant (pour sa gestion avancée des filtres stricts sur les *payloads* de métadonnées).

---

## 🚀 Prochaines Étapes du Projet

1. **Industrialisation du Parser HTML :** Finaliser le script pour encapsuler le texte complet rattaché à chaque couple `(Article, Titre)`.
2. **Généralisation à DORA :** Télécharger et appliquer le même pipeline sémantique HTML sur le règlement DORA.
3. **Chunking & Embedding :** Configurer `LangChain` pour découper les corps d'articles volumineux et générer les vecteurs sémantiques.
4. **Ingestion Qdrant :** Initialiser la collection locale Qdrant et injecter les points enrichis de leurs métadonnées (Document, Chapitre, Article).