# 🚀 GRC Copilot - Feuille de Route vers la Production (Phases 8+)

Ce document détaille les prochaines étapes de développement pour transformer l'orchestrateur LangGraph actuel en un produit logiciel complet, robuste et déployable.

## 1. Déploiement du Backend (FastAPI)

L'exposition du moteur agentique via une API REST est la priorité absolue pour découpler la logique métier de l'interface utilisateur. Python sera utilisé pour sa synergie native avec l'écosystème IA actuel.

* **Conception des routes :** Création d'un endpoint `POST /audit/start` pour initier l'analyse avec la PSSI en charge utile, et un endpoint `POST /audit/resume` pour injecter la décision humaine et lever la pause du nœud tampon.
* **Gestion de la concurrence :** Implémentation des requêtes asynchrones (`async def`) pour permettre au serveur de traiter plusieurs audits simultanément sans bloquer le thread principal.
* **Sécurisation de l'API :** Intégration de schémas de validation Pydantic pour assainir les entrées et configuration stricte des middlewares CORS.

## 2. Développement de l'Interface Humaine (Dashboard)

L'objectif est de fournir un environnement visuel interactif permettant à l'auditeur humain d'examiner le rapport brut généré par l'IA et de prendre une décision.

* **MVP Rapide :** Utilisation de Streamlit pour générer instantanément une interface web en Python, idéale pour visualiser les JSON de conformité et prototyper les boutons de validation sans friction.
* **Frontend Avancé :** Étant donné la grande synergie entre ces technologies, développement ultérieur d'une interface cliente dédiée en JavaScript (React ou Vue) communiquant de manière asynchrone avec l'API FastAPI pour une expérience utilisateur sur-mesure.

## 3. DevOps & Conteneurisation (Docker)

L'isolation de l'environnement garantira que l'application s'exécute de manière identique et prévisible sur n'importe quelle infrastructure serveur.

* **Création du Dockerfile :** Packaging de l'application Python, des dépendances LangChain et de la configuration système dans un conteneur allégé.
* **Orchestration globale :** Rédaction d'un fichier `docker-compose.yml` pour instancier et faire communiquer simultanément le conteneur du backend, le frontend, et la base vectorielle locale Qdrant.


* **Gestion des volumes :** Configuration de la persistance externe pour le fichier SQLite (`grc_copilot_persistance.db`) et le dossier `backup_reports` afin de garantir l'intégrité des audits lors du redémarrage des conteneurs.



## 4. Tests de Charge & Évolution Analytique (EBIOS RM)

Avant d'ajouter de nouveaux référentiels, le moteur doit prouver sa résilience sous des conditions de stress en entreprise.

* **Stress Test d'Ingestion :** Soumission de politiques de sécurité massives (dizaines de pages) pour observer le comportement de la fenêtre de contexte du modèle local et ajuster les stratégies de découpage (Chunking).
* **Intégration EBIOS RM :** Une fois l'infrastructure stabilisée, réouverture du pipeline d'ingestion initial pour modéliser et implémenter la méthode d'analyse de risques de l'ANSSI.

## 5. Implémentation d'une solution d'agent 100% local 
possibilité de réaliser cela avec un agent local pour une confidentialité absolue !
* **Agent IA Local Based :** Agent IA Local Based avec l'option native de LangChain
## 6. Création d'une Version Compacte (all in one file)
Simple fichier .py executable et fonctionnel
* **Méchanisme 'Everything in one file' et supression du 'superflu' :** Base de données Qdrant stocké dans la RAM, pas de 'Human-in-the-Loop' asynchrone, pas de notification Teams ni d'upload sur un SharePoint. Une version très simplifiée qui conviendra à beaucoup de gens !
