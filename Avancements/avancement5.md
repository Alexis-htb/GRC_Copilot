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