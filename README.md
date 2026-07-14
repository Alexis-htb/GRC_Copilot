# 🛡️ GRC Copilot - Assistant d'Audit Automatisé (NIS2 / DORA)

Ce projet est un moteur agentique de Gouvernance, Risque et Conformité (GRC) propulsé par l'IA. Il est conçu pour analyser automatiquement les Politiques de Sécurité des Systèmes d'Information (PSSI) des entreprises et détecter les écarts de conformité par rapport aux textes législatifs européens majeurs (**NIS2** et **DORA**). 

Il s'intègre nativement à l'infrastructure d'entreprise **Microsoft 365** pour la remontée d'alertes et la consolidation des rapports.

---

## 🎯 Finalité du Projet

Ce projet a été développé pour démontrer des compétences en ingénierie de la cybersécurité, en intégration d'infrastructures cloud, et en orchestration de grands modèles de langage (LLM). Il résout un problème métier réel : l'automatisation de l'analyse juridique et technique face à la complexité des nouvelles réglementations européennes.

**Principales fonctionnalités :**
*   **Analyse Juridique Autonome :** Extraction sémantique des exigences internes (PSSI) et détermination automatique du cadre légal applicable (NIS2, DORA, ou les deux).
*   **Recherche Vectorielle (RAG) Optimisée :** Interrogation chirurgicale d'une base de connaissances vectorielle locale (`Qdrant`) avec un système de pré-filtrage des métadonnées et une déduplication algorithmique pour préserver la fenêtre de contexte du modèle IA.
*   **Génération Déterministe :** Utilisation d'appels structurés (`Pydantic`) pour forcer le LLM à produire des rapports de conformité formatés en JSON pur, sans hallucination ni bavardage.
*   **Infrastructure *Human-in-the-Loop* (HITL) :** Le workflow d'audit se met en pause de manière persistante (`SQLite`) pour permettre à un auditeur humain de réviser et valider les écarts détectés avant toute transmission.
*   **Intégration Microsoft 365 Idempotente :** Connexion applicative sans interface (OBO/Client Credentials via `MSAL`) pour pousser les métriques vers **SharePoint** (pour l'analyse Power BI) et déclencher des webhooks **Teams** en cas de criticité majeure.

---

## 🛠️ Architecture Technique

Le projet repose sur un pipeline de données asynchrone et un graphe d'états :

1.  **Ingestion & Structuration :** Parsing HTML (ELI) des textes de lois officiels, découpage hiérarchique (*Parent/Child chunking*), et peuplement de la base locale Qdrant.
2.  **L'Orchestrateur LangGraph :**
    *   `Agent Spécificateur` : Extrait les règles de la PSSI.
    *   `Agent Auditeur` : Recherche les lois et rédige le rapport JSON.
    *   `Nœud Tampon` : Met le graphe en pause (HITL) et sauvegarde l'état dans SQLite.
    *   `Agent Sauvegarde` : Exporte le fichier JSON localement et vers SharePoint.
    *   `Agent Notificateur` : Alerte l'équipe Sécurité via Teams.

**Stack technologique :**
*   **Langage :** Python 3.x
*   **Orchestration LLM :** LangChain & LangGraph
*   **Modèles IA :** Google Gemini (`gemini-3.1-flash-lite`) pour l'inférence, HuggingFace (`all-MiniLM-L6-v2`) pour l'embedding.
*   **Base de données Vectorielle :** Qdrant (Conteneur local).
*   **Intégration Cloud :** API Microsoft Graph, Azure Entra ID (MSAL), SharePoint, Power Automate (Teams).

---

## ⚙️ Déploiement & Utilisation

### Prérequis
*   Python 3.10 ou supérieur.
*   Docker (pour lancer le conteneur Qdrant local).
*   Un tenant Microsoft 365 avec des droits d'administration pour configurer l'App Registration (Entra ID).

### 1. Installation de l'environnement

Clonez le dépôt et installez les dépendances :
```bash
git clone <votre-url-github>
cd GRC-Copilot
pip install -r requirements.txt
```

### 2. Configuration des secrets

Créez un fichier `.env` à la racine du projet et renseignez les variables suivantes :
```env
# Clés API IA
GEMINI_API_KEY="votre_cle_google"
HF_API_KEY="votre_cle_huggingface"

# Identifiants Application Microsoft Entra ID (Pour SharePoint)
CLIENT_ID="votre_client_id"
CLIENT_SECRET="votre_client_secret"
TENANT_ID="votre_tenant_id"
SITE_ID="votre_sharepoint_site_id"
LIST_ID="votre_sharepoint_list_id"

# Webhook Power Automate (Pour Teams)
URL_WEBHOOK_TEAMS="votre_url_webhook"
```

### 3. Lancement de la base vectorielle

Démarrez l'instance locale de Qdrant via Docker :
```bash
docker run -p 6333:6333 -p 6334:6334     -v $(pwd)/qdrant_storage:/qdrant/storage:z     qdrant/qdrant
```

### 4. Ingestion des textes de loi

La première étape consiste à transformer les textes réglementaires bruts en vecteurs mathématiques :
```bash
python rag.py
```
*Le script va nettoyer les balises HTML d'EUR-Lex, découper les articles, et populer la base Qdrant hébergée sur le port 6333.*

### 5. Exécution d'un Audit

L'exécution principale simule le traitement d'une PSSI. Le graphe se mettra en pause (nœud tampon) pour attendre la validation humaine.
```bash
python CopilotGRC.py
```

### 6. Reprise et Validation (Human-in-the-Loop)

Dans un environnement de production, l'humain interagit via une interface. Pour simuler cette reprise et relancer le graphe vers la persistance Microsoft 365, exécutez le module de reprise en lui passant la décision (`continuer` ou `annuler`) :
```bash
# Dans un terminal interactif ou via un appel externe
from reprise_audit import declencher_reprise_production
declencher_reprise_production("audit", "continuer")
```

---

## 🚀 Feuille de route (En cours)

Ce projet est activement développé. Les prochaines étapes architecturales sont :
1.  **Exposition via API :** Création d'un backend `FastAPI` pour découpler le moteur IA et gérer la concurrence des audits.
2.  **Interface Utilisateur :** Développement d'un dashboard interactif (`Streamlit` ou Vue.js) pour que l'auditeur humain puisse réviser visuellement les JSON avant approbation.
3.  **Conteneurisation totale :** Packaging du script et de l'API dans des conteneurs Docker orchestrés via `docker-compose`.
4.  **Intégration EBIOS RM :** Ajout des fiches méthodologiques de l'ANSSI pour la modélisation des risques.
5. **Version Compacte :** Création d'une version compacte fonctionnelle et exécutable en un seul bouton (pas de déploiement ou autre)
