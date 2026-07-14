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

# 📑 GRC Copilot - Journal de Bord R&D (Phase 2 : Structuration Sémantique & Filtrage Vectoriel)

Ce document complète la phase 1 et consigne les verrous algorithmiques levés lors de la généralisation du pipeline d'ingestion ainsi que les choix d'architecture arrêtés pour l'indexation vectorielle dans **Qdrant**.



## 🎯 Objectifs de la Phase 2

1. Généraliser le parser sémantique HTML à l'ensemble du corpus réglementaire (**NIS2** et **DORA**).


2. Concevoir une stratégie de découpage textuelle (*chunking*) adaptée à la granularité du droit de la cybersécurité.
3. Implémenter un système de requêtage sémantique infaillible, excluant tout risque d'angle mort ou de faux positifs lors de l'audit.



## 🗺️ Les Verrous Techniques Levés & Correctifs

### 1. Le Nettoyage des Exposants Typographiques (Balises `span`)

* **Problème :** Le code HTML natif d'EUR-Lex utilise des balises intrusives pour gérer l'affichage des exposants (ex: `n<span class="oj-super">o</span> 910/2014` pour "n°"). Lors du parsing, ces balises polluaient à la fois le corps des articles et les titres sémantiques.
* **Solution :** Implémentation d'un pré-nettoyage chirurgical par chaînes de caractères avant la phase d'extraction, remplaçant ces structures par de vrais caractères normalisés (`°`, `er`).

### 2. Le Piège du Saut de Ligne Invisible (L'anomalie de l'Article 47 de DORA)

* **Problème :** Lors du passage de DORA au crible de l'expression régulière standard, le parser ignorait systématiquement l'Article 47, faisant chuter le compteur à 63 articles au lieu de 64. L'analyse a révélé que les développeurs d'EUR-Lex avaient inséré un retour à la ligne (`\n`) inédit juste après la balise ouvrante du titre. Le caractère point (`.`) de la regex standard s'arrêtant aux sauts de ligne, la capture échouait.
* **Solution :** Activation du drapeau de compilation **`re.DOTALL`** (ou `re.S`). Ce commutateur force le moteur de regex à traiter les sauts de ligne comme des caractères normaux, sécurisant l'extraction complète des 64 articles de DORA.



## 💡 Choix d'Architecture RAG Validés

### 1. Stratégie du "Hierarchical Chunking" (Parent / Enfant)

Pour éviter le phénomène de **dilution sémantique** (perte de précision des vecteurs sur les articles fleuves comme l'Article 21 de NIS2), nous avons banni le découpage barbare au kilomètre.

* **Le Parent :** L'article de loi isolé forme une frontière étanche. Aucun chunk ne peut chevaucher deux articles différents.
* **L'Enfant :** Chaque article est découpé de manière isolée en sous-blocs d'une taille cible de **1200 caractères** avec un recouvrement (*chunk_overlap*) de **150 caractères**. Ce recouvrement garantit le maintien de la continuité logique et prévient la rupture de contexte entre deux phrases. Chaque enfant hérite strictement des métadonnées de son parent.

### 2. Impératif du "Pre-filtering" sur le Payload (Qdrant)

Dans un contexte de conformité réglementaire stricte, le *post-filtering* (chercher puis trier) est proscrit car il engendre une chute catastrophique du rappel (risque d'obtenir 0 résultat utile si une loi est surreprésentée en base).

* **Choix arrêté :** Utilisation du **Pre-filtering** natif de Qdrant. La base vectorielle utilise les métadonnées stockées dans son *Payload* pour isoler la loi applicable (ex: `loi = DORA`) sous forme de requête logique *avant* de calculer la similarité géométrique des vecteurs.


## 🛠️ Modélisation Technique Validée (LangChain / Qdrant)

* **Encapsulation sémantique :** Utilisation de l'objet `Document` de LangChain. Le texte brut nettoyé est assigné à `page_content` tandis que la carte d'identité de l'article est injectée pure dans `metadata`.
* **Configuration du Retriever de l'Agent Auditeur :**

```python
retriever = qdrant_db.as_retriever(
    search_type="similarity",
    search_kwargs={
        "filter": {"loi": "DORA"},
        "k": 4
    }
)

```

### 📑 GRC Copilot - Journal de Bord R&D (Phase 3 : Architecture Agentique & Inférence Structurée)

Ce document complète les phases 1 et 2, et retrace la conception du moteur d'orchestration multi-agents ainsi que la transition d'un environnement de simulation vers un pipeline d'inférence réel et déterministe.

---

### 🎯 Objectifs de la Phase 3

1. **Orchestrer le Workflow Cyber :** Modéliser un graphe d'état cyclique ou linéaire (`LangGraph`) séparant les rôles du Spécificateur et de l'Auditeur.
2. **Brider l'Inférence Logique :** Forcer un grand modèle de langage à raisonner exclusivement sous des contraintes de schémas stricts Pydantic pour éliminer le bavardage et les hallucinations.
3. **Passer à l'Échelle "Prod-Ready" :** Raccorder le système à une infrastructure Qdrant physique persistante et instancier un modèle de pensée (*Thinking Model*) adapté aux exigences du droit de la cybersécurité.

---

### 🗺️ Les Verrous Techniques Levés & Correctifs

#### 1. Le Chassé-Croisé des Douaniers de Typage (Pydantic vs LangGraph)

* **Problème :** Lors de la première exécution du graphe, le système a levé des exceptions de validation de type (`ValidationError`). Deux erreurs de structure s'opposaient : d'un côté, un objet Pydantic unique était envoyé là où une `List` était contractuellement attendue ; de l'autre, des crochets superflus transformaient un schéma d'état en liste brute dans le dictionnaire de mise à jour.
* **Solution :** Alignement chirurgical des structures de données. L'anomalie unique a été encapsulée dans une liste pour satisfaire le schéma `SchemaRapportAudit`, et l'objet final a été transmis épuré de ses crochets pour correspondre exactement à la définition de l'`AuditState`.

#### 2. Matérialisation du Client Qdrant Persistant

* **Problème :** L'usage d'un RAG éphémère en mémoire vive (`:memory:`) imposait un coût d'ingestion et de parsing HTML inacceptable à chaque itération d'audit.
* **Solution :** Dissociation complète entre le pipeline d'ingestion (écriture) et le pipeline d'inférence (lecture). Le script final s'appuie désormais sur une connexion réseau persistante via `qdrant_client.QdrantClient` sur le port `6333`. Le conteneur conserve les vecteurs, permettant à l'agent d'exécuter des recherches sémantiques instantanées via la méthode `.invoke()`.

#### 3. Activation du Moteur de Raisonnement Déterministe

* **Problème :** Les modèles de langage standards ont tendance à générer des analyses de risques informelles, verbeuses ou déconnectées du référentiel juridique fourni.
* **Solution :** Implémentation du modèle spécialisé `Qwen3-4B-Thinking` pour exploiter ses capacités natives de déploiement de chaîne de pensée (*Chain of Thought*). Ce cerveau a été bridé à l'aide de la méthode de haut niveau **`.with_structured_output()`** de LangChain, forçant le modèle à couler son raisonnement cyber directement dans l'architecture JSON dictée par Pydantic.

---

### 🛠️ Modélisation Technique Validée (Runtime Final)

* **Contrat d'état global :** `AuditState` gérant le texte brut, les exigences extraites et le rapport final.
* **Moteur d'exécution :** Graphe compilé via `StateGraph` initié par un point d'entrée explicite et se terminant de manière déterministe sur le nœud `END`.

### 1. Le syndrome du `__repr__` Python (Incompatibilité API)

Ce que ton terminal affiche sous la forme `anomalies=[AnomalieConformite(...)]` n'est pas de la donnée échangeable. C'est la représentation textuelle brute interne de Python. Si tu tentes d'envoyer ce bloc de texte brut à ton Webhook Power Automate pour l'Étape 3, la passerelle cloud de Microsoft va te rejeter instantanément avec une erreur HTTP 400 (*Bad Request*). Les systèmes d'entreprise ont besoin d'un flux standardisé, universel et nettoyé : du **JSON pur**.

### 2. Le manque de contextualisation métier

Les remédiations proposées par l'IA (*"Implémenter obligatoirement une MFA..."*) sont pertinentes d'un point de vue théorique. Cependant, un bon auditeur GRC doit lier ces actions aux spécificités de l'entreprise auditée. Ici, le rapport manque de contextualisation par rapport au profil d'accès de l'infrastructure ou à la typologie des utilisateurs.

### 3. La structure de données pour Power BI

Pour alimenter proprement une liste SharePoint lue par **Power BI** (Étape 3), chaque anomalie doit être aplatie sous forme de variables primitives (chaînes de caractères, entiers, booléens) et isolée de manière unitaire. Envoyer une liste d'objets complexes imbriqués rendra la création de tes graphiques de conformité impossible.

---

## 📑 GRC Copilot - Journal de Bord R&D (Phase 4 : Migration Multi-LLM & Résilience du Filtrage Vectoriel)

Voici la mise à jour officielle de ton avancée, rédigée dans le style strict de ton laboratoire de recherche :

---

### 🎯 Objectifs de la Phase 4

1. **Pivoter vers une infrastructure FinOps / Free Tier** pour s'affranchir des limitations de bande passante et des coûts d'inférence des endpoints privés.
2. **Résoudre la friction d'intégration du Function Calling** sur les wrappers de modèles open-source.
3. **Imposer un typage strict et natif** sur le moteur de recherche sémantique local pour éliminer les crashs de requêtes complexes.

---

### 🗺️ Les Verrous Techniques Levés & Correctifs

#### 1. Le blocage du `.with_structured_output()` Open-Source

* **Problème rencontré :** L'utilisation du wrapper `ChatHuggingFace` sur un endpoint d'inférence brut a levé une exception `NotImplementedError`, le framework LangChain ne disposant pas de la couche de traduction native pour convertir les schémas Pydantic en appels de fonctions pour ce modèle spécifique.
* **Solution trouvée :** Pivot stratégique vers la classe `ChatGoogleGenerativeAI` en exploitant le modèle `gemini-3.1-flash-lite`. Ce choix offre un support natif, robuste et instantané des structures Pydantic tout en bénéficiant des quotas gratuits de Google AI Studio.



#### 2. L'effondrement réseau pour cause de *Cold Start*

* **Problème rencontré :** L'interrogation de l'API Serverless générique de Hugging Face provoquait des coupures de connexion brutales (`APIConnectionError`), le client HTTP de LangChain abandonnant la requête pendant que les serveurs distants tentaient de charger les poids massifs du modèle en VRAM.
* **Solution trouvée :** La transition vers l'infrastructure managée de Gemini a totalement éradiqué le problème de latence au démarrage, garantissant un temps de réponse inférieur à la seconde.

#### 3. Le crash de l'évaluation du filtre Qdrant (`AttributeError`)

* **Problème rencontré :** Le passage d'un dictionnaire Python imbriqué contenant l'opérateur logique `"any"` a fait planter le moteur local de Qdrant en mémoire vive (`AttributeError: 'dict' object has no attribute 'must'`), ce dernier exigeant des structures de requêtes strictement typées.
* **Solution trouvée :** Refactorisation complète du constructeur de filtres de l'Agent Auditeur. Remplacement des dictionnaires bruts par les classes natives du SDK officiel de Qdrant (`models.Filter`, `models.FieldCondition`, `models.MatchAny`, `models.MatchValue`).



---

### 🛠️ État d'Avancement du Runtime

* **Moteur RAG :** Opérationnel en filtrage chirurgical pré-similarité géométrique.


* **Orchestration Multi-Agents :** Le graphe LangGraph transmet avec succès les états validés du nœud spécificateur au nœud auditeur.

### 📑 GRC Copilot - Journal de Bord R&D (Phase 5 : Idempotence Réseau & Architecture Découplée)

Ce document complète les phases précédentes et consigne la refactorisation de l'infrastructure de persistance ainsi que la mise en conformité du pipeline d'expédition Microsoft 365.

#### 🎯 Objectifs de la Phase 5

1. **Implémenter le Principe de Responsabilité Unique (SRP) :** Isoler les entrées/sorties techniques (fichiers, appels API) de la logique de réflexion des agents IA.


2. **Garantir l'Idempotence du Pipeline :** Empêcher la duplication de données et la pollution des métriques managériales lors de l'exécution récurrente de l'audit.


3. **Sécuriser le Contrat d'Interface M365 :** Adapter dynamiquement les objets complexes Python aux exigences structurelles strictes de Microsoft Graph et SharePoint.



#### 🗺️ Les Verrous Techniques Levés & Correctifs

##### 1. L'Isolateur de Flux (Extraction du Nœud de Sauvegarde)

* **Problème rencontré :** L'intégration directe des requêtes réseau au sein de l'agent auditeur transformait ce dernier en "nœud mammouth", mêlant traitement sémantique et appels HTTP, ce qui brisait la maintenabilité du code.


* **Solution trouvée :** Création d'un nœud d'infrastructure dédié (`agent_sauvegarde_node`) agissant comme une barrière étanche. Ce nœud consomme le rapport final, gère l'écriture asynchrone des backups locaux et délègue les opérations cloud à un sous-module spécialisé.



##### 2. Le Piège de l'Accumulation Aveugle (Aiguillage POST vs PATCH)

* **Problème rencontré :** L'usage exclusif de requêtes `POST` générait une nouvelle ligne SharePoint à chaque lancement de l'audit, provoquant un empilement de données historiques corrompant les tableaux de bord Power BI.


* **Solution trouvée :** Conception d'un mécanisme de reconnaissance sémantique préalable via le verbe `GET` associé au paramètre de filtrage OData `$filter=fields/Title eq '...'`. Le système analyse la réponse : si la liste est vide, il initialise la ressource via un `POST`. Si la ligne existe, il extrait chirurgicalement l'identifiant primitif de l'élément (`elements_trouves[0]["id"]`) pour exécuter un `PATCH` ciblé et idempotent.



##### 3. La Rigidité du Contrat SharePoint (Type & Typographie)

* **Problème rencontré :** Rejet systématique des payloads par la passerelle Azure (Erreur HTTP 400) à cause d'une coquille de clé (`Annomalies`) et risque imminent de troncature des chaînes JSON complexes à cause de la limite standard des colonnes de texte simples (255 caractères).


* **Solution trouvée :** Alignement strict du dictionnaire de traduction (`ToSharePointFormat`) avec le schéma exposé par l'API. Côté infrastructure Microsoft, bascule impérative de la colonne cible vers le type de données **"Plusieurs lignes de texte"** afin de lever toute barrière d'allocation mémoire et préserver l'intégrité syntaxique des rapports volumineux.



#### 🛠️ État d'Avancement du Runtime

* **Orchestration LangGraph :** Graphe linéaire épuré (`Spécificateur -> Auditeur -> Sauvegarde -> END`).


* **Minimisation de l'État :** Élimination des variables temporaires réseau (comme le code de statut HTTP) de l'`AuditState` global, confinant les données d'infrastructure à une portée strictement locale à leur nœud d'exécution.

## 📑 GRC Copilot - Journal de Bord R&D (Phase 6 : Autonomie d'Inférence, Authentification Applicative & Notification Modulaire)

Ce document complète les phases précédentes et consigne la sécurisation des secrets, l'automatisation du cycle d'authentification machine et l'isolation du flux d'alerte critique au sein de l'orchestrateur.

### 🎯 Objectifs de la Phase 6

1. **Garantir l'autonomie complète (Mode Daemon / Service de fond) :** Dissocier totalement l'agent des sessions utilisateurs éphémères pour permettre une exécution planifiée et automatisée sans interaction humaine.


2. **Modulariser le flux d'alerte critique :** Isoler la logique de notification Teams au sein d'un nœud indépendant dans `LangGraph` pour respecter le principe de responsabilité unique (SRP).


3. **Blinder la tolérance aux pannes réseau :** Éliminer les risques d'exceptions de variables non allouées (`UnboundLocalError`) et normaliser les retours d'erreurs d'infrastructure.



---

### 🗺️ Les Verrous Techniques Levés & Correctifs

#### 1. Le Pivot de l'Authentification Machine (Bascule OBO / Auth Code $\rightarrow$ Client Credentials)

* **Problème rencontré :** Les flux initiaux envisagés (On-Behalf-Of ou Authorization Code Flow) exigeaient la présence d'un jeton utilisateur initial ou une interaction de connexion dans un navigateur web, interdisant toute exécution asynchrone nocturne ou conteneurisée (Docker).


* **Solution trouvée :** Transition radicale vers le flux applicatif pur (*Client Credentials Flow*) via la méthode MSAL `acquire_token_for_client()`. Couplé à l'utilisation du scope statique universel `["[https://graph.microsoft.com/.default](https://graph.microsoft.com/.default)"]`, ce mécanisme permet à l'agent de s'authentifier de manière souveraine auprès de Microsoft Entra ID en utilisant uniquement ses secrets d'infrastructure (`CLIENT_ID`, `CLIENT_SECRET`, `TENANT_ID`) extraits de son environnement sécurisé `.env`.



#### 2. L'Isolateur d'Alertes Tactiques (Le Nœud Notificateur)

* **Problème rencontré :** L'évaluation des risques et la communication avec la passerelle Power Automate venaient alourdir le nœud de persistance, mélangeant la sauvegarde brute et la notification d'urgence.


* **Solution trouvée :** Extraction de la logique d'alerte dans un nœud dédié (`agent_notificateur_node`). Ce composant utilise une expression génératrice optimisée couplée à la fonction native `any()` pour inspecter le schéma Pydantic et déclencher instantanément le webhook Teams si un seuil de criticité majeur ("Moyen" ou "Critique") est franchi, consignant le code de retour dans `app.log`.



#### 3. L'Immunisation des Blocs d'Exceptions et Fin des Variables Fantômes

* **Problème rencontré :** En cas d'effondrement réseau physique (coupure de câble, échec DNS), l'absence d'instanciation de l'objet `response` provoquait des crashs secondaires de type `NameError` ou `UnboundLocalError` lors de la lecture de `.status_code` dans les blocs `except`. De même, l'absence de répertoire local de backup bloquait l'écriture.


* **Solution trouvée :**
* Implémentation d'une création de répertoire idempotente via `os.makedirs("backup_reports", exist_ok=True)` juste avant la sérialisation locale.


* Injection d'une clause de garde rigoureuse évaluant si `headers == None` pour interrompre proprement le flux en amont de toute manipulation.


* Restructuration des blocs de capture : les anomalies HTTP exploitent désormais la propriété native de l'objet d'exception (`http_err.response.status_code`), tandis que les pannes d'infrastructure pure retournent une valeur sentinelle sémantique (`-1`) pour préserver la stabilité du graphe d'état.





---

### 🛠️ État d'Avancement du Runtime Final

* **Orchestration LangGraph :** Graphe modulaire compilé et opérationnel impliquant une chaîne de traitement séquentielle et sécurisée :
`spécificateur` $\rightarrow$ `auditeur` $\rightarrow$ `sauvegarde` $\rightarrow$ `notificateur` $\rightarrow$ `END`.


* **Ingestion Business Intelligence :** Le stockage du rapport d'anomalies sous forme de chaîne JSON dans une colonne SharePoint de type "Plusieurs lignes de texte" est validé. Le modèle de données Power BI est configuré pour opérer un changement de granularité via Power Query (opération d'expansion), éclatant le bloc JSON pour isoler chaque anomalie sur sa propre ligne de calcul analytique.

### 📑 GRC Copilot - Journal de Bord R&D (Phase 7 : Persistance Résiliente, Contrôle Humain Alterné (HITL) & Sécurisation des Routeurs)

#### 🎯 Objectifs de la Phase 7

1. **Garantir la durabilité de l'état étendu :** Remplacer le stockage volatil en mémoire vive par une persistance transactionnelle sur disque pour immuniser l'architecture contre les redémarrages de conteneurs.
2. **Implémenter une isolation de staging (Human-in-the-loop) :** Concevoir une barrière d'interruption étanche empêchant l'évaluation précoce des arêtes conditionnelles avant l'intervention de l'auditeur humain.
3. **Verrouiller la dynamique d'aiguillage :** Bannir les structures de capture génériques au profit d'un routage explicite et d'un repli sécurisé (*Fail-Secure*).

#### 🗺️ Les Verrous Techniques Levés & Correctifs

##### 1. Le Piège de l'Aiguillage Précoce (Introduction du Nœud Tampon)

* **Problème rencontré :** L'application d'une barrière `interrupt_before` directement positionnée sur un nœud d'infrastructure distribué provoquait le contournement de l'interruption. Le routeur conditionnel, évalué immédiatement à la sortie de l'agent, lisait une variable d'état vide (`None`) et orientait prématurément le flux vers l'impasse `END`.
* **Solution trouvée :** Création d'un nœud neutre de passage (`agent_tampon_node`) intercalé stratégiquement comme zone de staging. La barrière d'interruption sécurise l'entrée de ce nœud tampon, figeant l'état complet du rapport d'audit *avant* que la fonction de routage ne soit sollicitée par l'orchestrateur.

##### 2. La Transition vers l'Infrastructure Durable (Migration SQLite)

* **Problème rencontré :** L'utilisation du `MemorySaver` limitait la persistance à la durée de vie éphémère du processus Python, exposant le système à une perte totale des analyses en attente de validation lors des phases de maintenance cloud.
* **Solution trouvée :** Migration vers la classe `SqliteSaver` connectée à une base de données relationnelle locale sur disque. Maîtrise du cycle de vie de la ressource par l'encapsulation de l'intégralité du pipeline opérationnel de test (`invoke`, `get_state`, `update_state`) au sein du bloc d'indentation du gestionnaire de contexte (`with`).

##### 3. L'Éradication des Comportements Implicites (Routage Fail-Secure)

* **Problème rencontré :** L'usage d'une clause `else` générique dans le routeur traitait implicitement toutes les anomalies de données, les chaînes vides ou les bugs d'interface de la même manière qu'un refus volontaire de l'utilisateur (`END`), masquant ainsi des dysfonctionnements critiques du système.
* **Solution trouvée :** Refactorisation de la logique décisionnelle par l'application d'un embranchement strict `if / elif` limitant les sorties autorisées aux jetons explicites (`'continuer'` ou `'annuler'`). Tout état alternatif provoque désormais la levée immédiate et contrôlée d'une exception `raise ValueError`, figeant l'exécution pour inspection technique.

#### 🛠️ État d'Avancement du Runtime Final

* **Architecture Découplée Certifiée :** Validation du script de production autonome `reprise_audit.py`. Le système réhydrate de manière souveraine l'arborescence des variables à partir du `thread_id` unique de l'entreprise et applique de manière atomique la charge utile dynamique contenant la décision humaine transmise par l'application hôte.
