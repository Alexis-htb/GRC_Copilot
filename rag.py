import re
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
import qdrant_client


print("[Initialisation] Chargement du traducteur sémantique...")
# On utilise un modèle open-source standard pour la GRC locale
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
_qdrant_db_cache = None
'''
qdrant_db = Qdrant(
    client=mon_client_qdrant,
    collection_name="grc_documents",
    embeddings=embeddings,
)
'''


def get_qdrant_db():
    """Renvoie l'instance unique de QdrantVectorStore en mode Lazy Loading."""
    global _qdrant_db_cache
    
    # Si le cache est vide, c'est qu'on appelle la fonction pour la toute première fois !
    if _qdrant_db_cache is None:
        print("[Réseau] Première sollicitation : Connexion à l'instance locale Qdrant...")
        try:
            # A) Crée ton instance de client Qdrant local
            client = qdrant_client.QdrantClient(url="http://localhost:6333")
            
            # B) Instancie ton QdrantVectorStore et stocke-le dans la variable de cache
            _qdrant_db_cache = QdrantVectorStore(
                client=client,
                collection_name="grc_documents",
                embeddings=embeddings
            )
            print("[Réseau] Connexion à Qdrant établie avec succès et mise en cache !")
            
        except Exception as e:
            print(f"[Erreur Critique] Impossible de joindre Qdrant : {e}")
            # Si ça échoue, on peut lever une exception propre ou renvoyer None
            raise e
            
    # Si la connexion existait déjà (ou vient d'être créée), on la retourne simplement !
    return _qdrant_db_cache


def initialiser_et_peupler_base():
    # 1. Chargement et découpage préventif des annexes
    chemin_html = "laws/NIS2.html"
    with open(chemin_html, "r", encoding="utf-8") as f:
        html_brut = f.read()

    # On coupe le document juste avant le tableau de correspondance pour éviter le bruit
    limite = html_brut.find("TABLEAU DE CORRESPONDANCE")
    if limite == -1:
        limite = html_brut.find("T ABLEA U DE C")

    html_loi = html_brut[:limite] if limite != -1 else html_brut

    # 2. Détection des positions de chaque entête d'article
    pattern_articles = r'<p\s+[^>]*class="oj-ti-art"[^>]*>(.*?)</p>\s*<div\s+[^>]*class="eli-title"[^>]*>\s*<p\s+[^>]*class="oj-sti-art"[^>]*>(.*?)</p>'

    # finditer nous donne les coordonnées de début et de fin de chaque match
    matches = list(re.finditer(pattern_articles, html_loi, re.DOTALL))
    articles_complets = []

    # 3. Boucle d'extraction du contenu entre les articles
    for i in range(len(matches)):
        match_actuel = matches[i]
        
        # Extraction propre du numéro et du titre
        numero = match_actuel.group(1).replace("\xa0", " ").strip()
        titre = match_actuel.group(2).replace("\xa0", " ").strip()
        
        # Le texte commence juste après la fin de l'entête actuel
        debut_texte = match_actuel.end()
        
        # Et se termine juste avant le début de l'article suivant
        if i + 1 < len(matches):
            fin_texte = matches[i+1].start()
        else:
            fin_texte = len(html_loi) # Pour le dernier article, on va jusqu'au bout
            
        # On isole le bloc HTML brut contenant le texte de l'article
        html_bloc = html_loi[debut_texte:fin_texte]
        
        # 4. NETTOYAGE CHIRURGICAL DU HTML (Corps ET Titre)
        # On nettoie le titre des balises d'exposants
        titre_propre = titre.replace('<span class="oj-super">o</span>', '°')
        titre_propre = titre_propre.replace('<span class="oj-super">er</span>', 'er')
        titre_propre = re.sub(r'<[^>]+>', '', titre_propre).strip() # Au cas où il reste d'autres balises
        
        # On nettoie le bloc de texte
        html_bloc = html_bloc.replace('<span class="oj-super">o</span>', '°')
        html_bloc = html_bloc.replace('<span class="oj-super">er</span>', 'er')
        
        texte_propre = re.sub(r'<[^>]+>', ' ', html_bloc)
        texte_propre = texte_propre.replace("\xa0", " ")
        texte_propre = re.sub(r'\s+', ' ', texte_propre).strip()
        
        # On ajoute l'article structuré avec le titre propre !
        articles_complets.append({
            "loi": "NIS2",
            "numero": numero,
            "titre": titre_propre, 
            "contexte": texte_propre
        })

    print(f"[Succès] {len(articles_complets)} articles complets ont été extraits et nettoyés !")

    # 1. Chargement du fichier HTML officiel de DORA
    chemin_dora = "laws/DORA.html"
    with open(chemin_dora, "r", encoding="utf-8") as f:
        html_dora = f.read()

    print("Analyse du fichier DORA HTML en cours...")

    # 2. Détection des positions de chaque entête d'article (Même formule magique !)
    pattern_articles = r'<p\s+[^>]*class="oj-ti-art"[^>]*>(.*?)</p>\s*<div\s+[^>]*class="eli-title"[^>]*>\s*<p\s+[^>]*class="oj-sti-art"[^>]*>(.*?)</p>'

    matches_dora = list(re.finditer(pattern_articles, html_dora, re.DOTALL))
    articles_dora_complets = []

    # 3. Boucle d'extraction du contenu entre les articles
    for i in range(len(matches_dora)):
        match_actuel = matches_dora[i]
        
        # Nettoyage des numéros et titres
        numero = match_actuel.group(1).replace("\xa0", " ").strip()
        titre = match_actuel.group(2).replace("\xa0", " ").strip()
        
        # Calcul des zones de texte
        debut_texte = match_actuel.end()
        if i + 1 < len(matches_dora):
            fin_texte = matches_dora[i+1].start()
        else:
            fin_texte = len(html_dora)
            
        html_bloc = html_dora[debut_texte:fin_texte]
        
        # 4. Nettoyage chirurgical (Titre ET Corps)
        titre_propre = titre.replace('<span class="oj-super">o</span>', '°')
        titre_propre = titre_propre.replace('<span class="oj-super">er</span>', 'er')
        titre_propre = re.sub(r'<[^>]+>', '', titre_propre).strip()
        
        html_bloc = html_bloc.replace('<span class="oj-super">o</span>', '°')
        html_bloc = html_bloc.replace('<span class="oj-super">er</span>', 'er')
        
        texte_propre = re.sub(r'<[^>]+>', ' ', html_bloc)
        texte_propre = texte_propre.replace("\xa0", " ")
        texte_propre = re.sub(r'\s+', ' ', texte_propre).strip()
        
        # On ajoute l'article DORA à notre liste
        articles_complets.append({
            "loi": "DORA",
            "numero": numero,
            "titre": titre_propre,
            "contexte": texte_propre
        })

    print(f"[Succès] {len(articles_complets)} articles complets de DORA ont été extraits et nettoyés !")

    # [Structure Logique du Chunking Hiérarchique]

    # On prépare le découpeur de caractères LangChain
    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)

    liste_documents_finals = []

    # Boucle 1 : On parcourt nos articles isolés (NIS2 ou DORA)
    for art in articles_complets:
        
        # 1. On prépare la carte d'identité unique de l'article PARENT
        metadata_parent = {
            "loi": art["loi"],
            "numero": art["numero"],
            "titre": art["titre"]
        }
        
        # 2. On découpe le texte de l'article EN COURS en morceaux ENFANTS
        morceaux_de_texte = splitter.split_text(art["contexte"])
        
        # Boucle 2 : On encapsule chaque morceau dans un Document LangChain
        for morceau in morceaux_de_texte:
            
            doc_fragment = Document(
                page_content = morceau,
                metadata = metadata_parent
            )
            
            liste_documents_finals.append(doc_fragment)

    try:
        global _qdrant_db_cache
        # A) Crée ton instance de client Qdrant local
        client = qdrant_client.QdrantClient(url="http://localhost:6333")
        _qdrant_db_cache = QdrantVectorStore.from_documents(
            client=client,
            documents= liste_documents_finals,
            collection_name="grc_documents",
            embedding=embeddings,
        )
    except Exception as e:
        print("impossible de joindre le client qdrant !")
        raise e
    

if __name__ == "__main__":
    initialiser_et_peupler_base()