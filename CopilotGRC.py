from pydantic import BaseModel, Field
import typing
#from typing import List
from typing import TypedDict, List, Dict, Any, Literal
from langchain_core.documents import Document
from langgraph.graph import StateGraph, END
from langchain.agents import create_agent
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_google_genai import ChatGoogleGenerativeAI
from qdrant_client.http import models



import SynchPowerBI
from dotenv import load_dotenv
from datetime import datetime
import os
import rag

import logging

# Configuration du formatteur pour coller exactement à ce que tu faisais déjà
# %(asctime)s génère le timestamp, %(levelname)s le niveau, et %(message)s ton texte
logging.basicConfig(
    filename='app.log',
    level=logging.INFO, # Niveau minimum à enregistrer (INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s;%(levelname)s;%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

load_dotenv()

HF_API_KEY = os.environ.get("HF_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

mon_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite", # ou gemini-1.5-pro
    google_api_key=GEMINI_API_KEY
)






class ExigenceCyber(BaseModel):
    id: int = Field(description="Identifiant unique de l'exigence (ex: 1, 2, 3)")
    categorie: str = Field(description="La catégorie cyber (ex: Chiffrement, Contrôle d'accès)")
    description: str = Field(description="La règle de sécurité stricte extraite du texte")

class SchemaExtractionPSSI(BaseModel):
    liste_exigences: List[ExigenceCyber]

class AnomalieConformite(BaseModel):
    constat: str = Field(description="Description de l'écart entre la PSSI et la loi")
    loi_concernee: str = Field(description="Nom de la loi violée ou visée (NIS2 ou DORA)")
    article_associe: str = Field(description="Numéro de l'article de loi de référence")
    criticite: Literal["Faible","Moyen","Critique"] = Field(description="Niveau de risque : Faible, Moyen, Critique")
    remediation: str = Field(description="Action technique exacte à mettre en place pour corriger le tir")

class SchemaRapportAudit(BaseModel):
    anomalies: List[AnomalieConformite]

class DecisionRéglementaire(BaseModel):
    loi_cible: Literal["DORA","NIS2","BOTH"] = Field(description="Doit être STRICTEMENT 'DORA', 'NIS2' ou 'BOTH' après analyse")
    justification: str = Field(description="Explication juridique concise du choix de scope")

class AuditState(TypedDict):
    # 1. LE RÉEL : Les données de l'entreprise auditée
    politique_brute: str # Le texte brut de la PSSI fourni en entrée
    exigences_entreprise: SchemaExtractionPSSI # Chaque exigence extraite doit être un objet autonome

    # 2. LA RÉFÉRENCE : Ce qui est attendu par la loi (NIS2 / DORA)
    contexte_legal_recupere: List[Document] # La liste des objets renvoyés nativement par ton retriever Qdrant

    # 3. LE DELTA : Les livrables de l'audit
    rapport_conformite: SchemaRapportAudit # List[Dict[str, Any]]

    # 4. LE PROFILAGE : Carte d'identité de l'entreprise (secteur, nombre d'employés, CA) et Le cadre juridique adéquat
    profil_entreprise_brut: str   # "PME de 150 personnes dans le secteur des crypto-actifs"
    loi_applicable_determinee: DecisionRéglementaire # La loi qui s'applique à l'entreprise, 'NIS2' et 'DORA'

    # 5. RANDOM : toutes les autres valeures
    decision_validation: str


def agent_specificateur_node(state: AuditState) -> Dict[str, Any]:
    print("[Action] L'Agent Spécificateur analyse la PSSI brute avec l'IA...")
    texte_a_analyser = state["politique_brute"]
    
    # 1. On prépare le contexte pour le LLM
    messages = [
        ("system", "Tu es un expert en cybersécurité. Extraits les exigences de la politique fournie."),
        ("human", f"Voici la politique de l'entreprise : {texte_a_analyser}")
    ]
    
    # 2. On contraint le modèle à utiliser STRICTEMENT ton schéma Pydantic
    llm_structure = mon_llm.with_structured_output(SchemaExtractionPSSI)
    
    # 3. On déclenche l'analyse
    resultat_pssi_ia = llm_structure.invoke(messages)
    
    # 4. On définit le cadre législatif appliquable à l'entreprise audité
    profil = state["profil_entreprise_brut"]
    messages = [
        ("system", "Tu es un expert en Droit, ton unique but est de dire si l'entreprise est soumise au texte de loi 'DORA' ou au 'texte' 'NIS2'"),
        ("human", f"Voici le profil de l'entreprise : {profil}")
    ]
    llm_structure = mon_llm.with_structured_output(DecisionRéglementaire)
    resultat_loi_ia = llm_structure.invoke(messages)

    return {
        "exigences_entreprise": resultat_pssi_ia,
        "loi_applicable_determinee": resultat_loi_ia
    }

def agent_auditeur_node(state: AuditState) -> Dict[str, Any]:
    # 1. Extraction de la liste et création du retriever dynamique

    choix_loi = state["loi_applicable_determinee"].loi_cible

    # 2. Construction d'un objet Filtre Natif Qdrant
    if choix_loi == "BOTH":
        filtre_qdrant = models.Filter(
            must=[
                models.FieldCondition(
                    key="loi",
                    match=models.MatchAny(any=["NIS2", "DORA"])
                )
            ]
        )
    else:
        filtre_qdrant = models.Filter(
            must=[
                models.FieldCondition(
                    key="loi",
                    match=models.MatchValue(value=choix_loi)
                )
            ]
        )

    # 3. Instanciation épurée du retriever
    retriever = rag.get_qdrant_db(  ).as_retriever(
        search_type="similarity",
        search_kwargs={
            "filter": filtre_qdrant, 
            "k": 5
        }
    )
    
    conteneur_pssi = state["exigences_entreprise"]
    liste_a_auditer = conteneur_pssi.liste_exigences
    
    # On prépare une liste vide pour accumuler toutes nos preuves juridiques
    tous_les_documents_loi = []
    
    # 2. La boucle de recherche sémantique
    for exigence in liste_a_auditer:
        print(f"Recherche de conformité pour la règle : {exigence.description}")
        
        # Interrogation du retriever Qdrant
        # C'est ici qu'on appelle la méthode magique de LangChain
        docs_extraits = retriever.invoke(exigence.description)
        
        # On ajoute les documents trouvés à notre collection globale
        tous_les_documents_loi.extend(docs_extraits)

    print("[Action] L'Agent Auditeur rédige le rapport final avec l'IA...")
    PSSI = state["exigences_entreprise"]

    exigences_brutes = [f"- [{e.categorie}] {e.description}" for e in PSSI.liste_exigences]

    # Fusion de la liste en un bloc de texte propre pour le prompt
    pssi_formatee = "\n".join(exigences_brutes)

    # 1. Extraction sélective du texte juridique
    # On parcourt chaque objet 'doc' de notre liste globale, et on ne garde que son texte
    docs_uniques = list({doc.page_content: doc for doc in tous_les_documents_loi}.values())

    # 2. On extrait le texte pour le LLM
    textes_extraits = [doc.page_content for doc in docs_uniques]

    # 2. Fusion des textes en une seule chaîne propre
    # On utilise le double saut de ligne comme séparateur pour coudre notre liste de chaînes
    contexte_legal_propre = "\n\n".join(textes_extraits)

    # 3. Injection dans le prompt épuré de toute pollution technique
    messages = [
        ("system", "Tu es un auditeur GRC intraitable de niveau expert. Analyse les écarts..."),
        ("human", f"Voici la PSSI : {pssi_formatee} \n\n Voici les textes de lois applicables : {contexte_legal_propre}")
    ]

    llm_auditeur = mon_llm.with_structured_output(SchemaRapportAudit)

    # 3. Déclenchement de l'analyse
    rapport_ia = llm_auditeur.invoke(messages)

    # 4. Le retour d'état
    return {
        "contexte_legal_recupere": docs_uniques,
        "rapport_conformite": rapport_ia
    }

def agent_tampon_node(state: AuditState) -> Dict[str, Any]:
    return {}

def agent_sauvegarde_node(state: AuditState) -> Dict[str, Any]:
    # il doit sauvegarder le rapport et mettre à jour les logs

    # le rapport
    # charge le rappport
    rapport_brut = state["rapport_conformite"]
    # --- FIX SQLITE SAVER ---
    # Si le checkpointer a transformé notre objet Pydantic en dictionnaire, on le reconstruit
    if isinstance(rapport_brut, dict):
        rapport_brut = SchemaRapportAudit(**rapport_brut)
    # ------------------------

    # convertir en JSON
    rapport = rapport_brut.model_dump_json(indent=4)

    # ecrire le rapport dans le dossier 'backup_reports'
    # 1. Générer un nom de fichier unique avec la date actuelle
    dossier = "backup_reports"
    os.makedirs(dossier, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(dossier, f"audit_{timestamp}.json")

    # 2. Écrire le contenu dans le fichier
    with open(filename, "w", encoding="utf-8") as f:
        f.write(rapport)

    # Envoyer le rapport à PowerBI et récuperer le code http
    rapport_sharepoint = ToSharePointFormat(rapport,state['profil_entreprise_brut'],len(rapport_brut.anomalies))
    code_http = SynchPowerBI.envoyer_metriques_sharepoint_defensif(rapport_sharepoint,state["profil_entreprise_brut"])
    # les log PowerBI
    # récuperer le timestamp bien formatté et le code http
    if code_http in (200, 201):
        logging.info(f"{code_http};SharePoint;Succès")
    else:
        logging.error(f"{code_http};SharePoint;Échec d'insertion")

    # mets à jour l'état
    return {"rapport_conformite": rapport_brut}

def ToSharePointFormat(rapport,profil_entreprise,nbAnomalies):
    payload_pour_sharepoint = {
    "fields": {
        "Title": f"Audit PSSI - {profil_entreprise}",
        "NombreAnomalies": nbAnomalies,
        "StatusConformite": "À Réviser" if nbAnomalies > 0 else "Conforme",
        "Anomalies": rapport if nbAnomalies > 0 else "None"
        }
    }
    return payload_pour_sharepoint

def agent_notificateur_node(state: AuditState):
    # Extraction de la liste des anomalies issues de ton objet Pydantic
    liste_anomalies = state["rapport_conformite"].anomalies

    # Détermination des niveaux de risques nécessitant une alerte immédiate
    seuils_alerte = {"Critique", "Moyen"}

    declencher_alerte_teams = any(anomalie.criticite in seuils_alerte for anomalie in liste_anomalies)

    if declencher_alerte_teams:
        print("[Alerte] Risque majeur détecté ! Envoi de la notification Teams...")
    
        code_http = SynchPowerBI.envoyer_notification_teams(state["profil_entreprise_brut"])
        # récuperer le timestamp bien formatté et le code http
        if code_http in (200, 201, 202):
            logging.info(f"{code_http};Teams;Succès")
        else:
            logging.error(f"{code_http};Teams;Échec d'envoi")
    return {}

def routeur_validation_humaine(state: AuditState) -> str:
    # On récupère la décision de l'humain
    decision = state.get("decision_validation")
    if decision == 'continuer':
        return "sauvegarde"
    if decision == 'annuler':
        return END
    else:
        raise ValueError("Erreur critique : Décision de validation invalide ou corrompue !")

# 1. On initialise le workflow avec son contrat d'état
workflow = StateGraph(AuditState)

# 2. On enregistre nos agents sur le plateau de jeu
workflow.add_node("specificateur", agent_specificateur_node)
workflow.add_node("auditeur", agent_auditeur_node)
workflow.add_node("sauvegarde", agent_sauvegarde_node)
workflow.add_node("notificateur", agent_notificateur_node)
workflow.add_node("tampon", agent_tampon_node)

# 3. On trace les connexions logiques
# Quel est le point de départ de l'analyse ?
workflow.set_entry_point("specificateur")

# Comment relier la fin du spécificateur au début de l'auditeur ?
workflow.add_edge("specificateur", "auditeur")

workflow.add_edge("auditeur", "tampon")

# Comment indiquer que l'auditeur termine définitivement le programme ?
#workflow.add_edge("auditeur", "sauvegarde")

workflow.add_edge("sauvegarde","notificateur")

workflow.add_edge("notificateur", END)

workflow.add_conditional_edges("tampon", routeur_validation_humaine,{"sauvegarde": "sauvegarde", END: END})



if __name__ == "__main__":

    # 4. Compilation du graphe

    with SqliteSaver.from_conn_string("grc_copilot_persistance.db") as memoire_disque:
        app = workflow.compile(
            checkpointer=memoire_disque, 
            interrupt_before=["tampon"]
        )
        print("[Succès] L'architecture multi-agents est officiellement opérationnelle et compilée !")
        # Simulation d'une politique de sécurité d'entreprise récupérée dans ton pipeline
        ma_politique_test = "PSSI - Section Authentification : L'accès aux applications financières nécessite un mot de passe d'au moins 12 caractères."
        mon_profil_test = "établissement bancaire Société Générale"
        # Lancement du GRC Copilot !
        config = {"configurable": {"thread_id": "audit"}}
        etat_final = app.invoke({
            "politique_brute": ma_politique_test,
            "profil_entreprise_brut": mon_profil_test
        },config=config)



        # Affichage du résultat final généré par l'auditeur
        print("=== RAPPORT D'AUDIT DE CONFORMITÉ ===")
        #print(etat_final["rapport_conformite"])
        rapport_pydantic = etat_final["rapport_conformite"]
        rapport_json_pur = rapport_pydantic.model_dump_json(indent=4)
        print(rapport_json_pur)
        snapshot = app.get_state(config)

        # [ZONE DE PAUSE HUMAINE]
        print("Le graphe est en pause. L'humain examine les données...")
        rapport_corrige = snapshot.values["rapport_conformite"]

        app.update_state(
            config, 
            {"rapport_conformite": rapport_corrige, "decision_validation" : "continuer"}, 
            as_node="auditeur"
        )
        # 3. [À TOI DE JOUER] Reprise de l'exécution
        print("--- Approbation humaine reçue ! Reprise du graphe ---")
        # Quelle instruction et quels paramètres vas-tu passer à cette deuxième invocation 
        # pour dire au graphe de recharger l'état de ce thread précis et de finaliser 
        # sa course vers SharePoint et Teams sans lui ré-injecter les données de départ ?
        etat_final = app.invoke(None, config=config)