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