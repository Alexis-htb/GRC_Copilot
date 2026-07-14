# 🛡️ GRC Copilot - Assistant d'Audit Automatisé (NIS2 / DORA)

Ce projet implémente un agent IA d'audit de conformité capable d'analyser la documentation interne d'une entreprise par rapport aux réglementations européennes NIS2 et DORA, puis d'alerter les équipes via l'écosystème Microsoft 365.

## 🗺️ Feuille de Route de Développement

### Étape 1 : Collecte de la Matière Première (Données)
*   Télécharger les textes réglementaires officiels au format PDF/Texte :
    *   **NIS2 :** Directive (UE) 2022/2555 sur le site officiel *EUR-Lex*.
    *   **DORA :** Règlement (UE) 2022/2554 sur le site officiel *EUR-Lex*.
    *   **EBIOS RM :** Guides et fiches de la méthode disponibles gratuitement sur le site de l'*ANSSI*.
*   Placer ces fichiers dans un dossier local nommé `/knowledge_base`.

### Étape 2 : Initialisation du Pipeline RAG & Agents
*   Créer un environnement de recherche avec un **Jupyter Notebook** (`research.ipynb`) pour tester les prompts de qualification de risques.
*   Mettre en place un système de RAG (Retrieval-Augmented Generation) simple :
    *   Utiliser `LangChain` avec une base vectorielle locale (`Qdrant`).
    *   Découper (*chunking*) les textes de loi et générer des embeddings.
*   Développer l'architecture agentique avec `LangGraph` :
    *   **Agent Spécificateur :** Reçoit une politique interne de l'entreprise (ex: "Politique de gestion des mots de passe").
    *   **Agent Auditeur :** Interroge la base de connaissances NIS2/DORA pour trouver les articles correspondants et lever les écarts de conformité (*gap analysis*).

### Étape 3 : Connexion Microsoft 365 (Monde Corporate)
*   **Accès SharePoint :** Configurer un script Python utilisant la bibliothèque `Office365-REST-Python-Client` ou des requêtes HTTP directes via l'API Microsoft Graph (nécessite la création d'une application de test sur le portail Azure/Entra ID).
*   **Alerte Teams via Power Automate :**
    *   Sur Power Automate, créer un flux automatisé déclenché par une **requête HTTP reçue (Webhook)**.
    *   Ajouter une action dans le flux : "Publier un message dans un canal Teams".
    *   Dans ton code Python, configurer le script pour qu'il envoie un JSON contenant le rapport d'anomalie à l'URL du Webhook Power Automate dès qu'un risque majeur est détecté.
*   Pousser les métriques de conformité (ex: % de conformité par chapitre) vers une liste SharePoint lue par **Power BI** pour générer le rapport final pour le management.