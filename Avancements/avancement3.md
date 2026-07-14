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