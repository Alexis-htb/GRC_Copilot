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