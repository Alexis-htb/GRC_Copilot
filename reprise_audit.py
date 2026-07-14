from langgraph.checkpoint.sqlite import SqliteSaver
from CopilotGRC import workflow  # On réimporte la structure du graphe

def declencher_reprise_production(cle_unique_audit, decision_human):
    
    # 1. On recrée la configuration de ciblage pour LangGraph
    config = {"configurable": {"thread_id": cle_unique_audit}}
    
    # 2. On rouvre la base de données persistante sur le disque
    with SqliteSaver.from_conn_string("grc_copilot_persistance.db") as memoire_disque:
        
        # On recompile le graphe avec sa mémoire sur disque
        app = workflow.compile(checkpointer=memoire_disque, interrupt_before=["tampon"])
        
        print(f"[Production] Récupération de l'audit en cours pour la clé : {cle_unique_audit}")
        
        # Étape A : On injecte la décision reçue depuis l'interface web
        app.update_state(
            config, 
            {"decision_validation": decision_human}, 
            as_node="auditeur"
        )
        
        print("[Production] Relance du moteur agentique...")
        # Étape B : On réveille le graphe pour qu'il termine sa course vers SharePoint/Teams
        app.invoke(None, config=config)