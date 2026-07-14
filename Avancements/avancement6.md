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