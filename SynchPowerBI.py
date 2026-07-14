import requests
from requests.exceptions import RequestException, HTTPError
import msal
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
TENANT_ID = os.environ.get("TENANT_ID")
SITE_ID = os.environ.get("SITE_ID")
LIST_ID = os.environ.get("LIST_ID")

def get_post_data():
    app = msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}"
    )
    url = f"https://graph.microsoft.com/v1.0/sites/{SITE_ID}/lists/{LIST_ID}/items"
    
    # 1. Configuration du scope applicatif statique
    graphe_scopes = ["https://graph.microsoft.com/.default"]

    # 2. Acquisition autonome du jeton applicatif
    resultat = app.acquire_token_for_client(scopes=graphe_scopes)

    # 3. Extraction & Validation

    if "access_token" in resultat:
        token_pour_sharepoint = resultat["access_token"]
        print("[Succès] Nouveau jeton délégué obtenu pour SharePoint !")
        # Préparation des droits d'accès pour Microsoft Graph
        headers = {
            "Authorization": f"Bearer {token_pour_sharepoint}",
            "Content-Type": "application/json"
        }
    else:
        print(f"[Erreur] Échec de l'échange: {resultat.get('error_description')}")
        headers = None

    
    return url,headers


#def envoyer_metriques_sharepoint_defensif(url, payload, headers):
def envoyer_metriques_sharepoint_defensif(payload,profil_entreprise):

    try:
        print("[Réseau] Récupération du token...")
        url,headers = get_post_data()
        if headers == None:
            return -1
        
        print("[Réseau] Tentative d'insertion des métriques dans SharePoint...")
        # 1. On interroge SharePoint avec le filtre OData
        profil_echappe = profil_entreprise.replace("'", "''")
        url_recherche = url + f"?$filter=fields/Title eq 'Audit PSSI - {profil_echappe}'"
        response = requests.get(url_recherche, headers=headers)
        response.raise_for_status()
        donnees = response.json()

        # 2. Récupération de la liste des résultats
        elements_trouves = donnees.get("value", [])

        # 1. Envoi de la requête POST ou PATCH
        if elements_trouves == []:
            response = requests.post(url=url, json=payload, headers=headers)
        else:
            id = elements_trouves[0]["id"]
            response = requests.patch(url=f"{url}/{id}", json=payload, headers=headers)
        # 2. Déclenchement automatique de l'exception si le code n'est pas un succès (ex: pas 201)
        response.raise_for_status()
            
        print("[Succès] Payload inséré proprement ! Status :", response.status_code)
        return response.status_code
            
    except HTTPError as http_err:
        # Interception spécifique des erreurs de statuts HTTP (401, 403, 404, etc.)
        print(f"[Erreur Sécurité/HTTP] La passerelle a rejeté la requête : {http_err}")
        # Ici, on pourrait inspecter http_err.response.status_code pour réagir finement
        return http_err.response.status_code
        
    except requests.exceptions.RequestException as net_err:
        print(f"[Erreur Réseau] Impossible d'atteindre le serveur Microsoft : {net_err}")
        return -1  
    

def envoyer_notification_teams(profil_entreprise):

    try:
        print("[Réseau] Envoie de notifications Teams")
        # URL secrète fournie par Power Automate lors de la création du flux
        url_webhook_teams = os.environ.get("URL_WEBHOOK_TEAMS")
        if url_webhook_teams is None:
            return -1
        # Préparation d'un dictionnaire d'alerte contextualisé pour les équipes
        payload_teams = {
            "text": f"ALERTE CONFORMITÉ - Un audit vient d'être généré pour {profil_entreprise}.",
            "details": "Plusieurs anomalies critiques ou moyennes ont été détectées. Veuillez consulter le rapport SharePoint."
        }
        
        response = requests.post(url=url_webhook_teams, json=payload_teams)
        
        response.raise_for_status()
            
        print("[Succès] Payload inséré proprement ! Status :", response.status_code)
        return response.status_code
            
    except HTTPError as http_err:
        # Interception spécifique des erreurs de statuts HTTP (401, 403, 404, etc.)
        print(f"[Erreur Sécurité/HTTP] La passerelle a rejeté la requête : {http_err}")
        # Ici, on pourrait inspecter http_err.response.status_code pour réagir finement
        return http_err.response.status_code
        
    except requests.exceptions.RequestException as net_err:
        print(f"[Erreur Réseau] Impossible d'atteindre le serveur Microsoft : {net_err}")
        return -1   