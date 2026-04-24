# Evaluation du modele finance en production

## Contexte

- Endpoint teste: `http://20.251.152.85:11434`
- Modele teste: `phi3.5:latest`
- Campagne de test: `15` questions (finance, hors-sujet, prompt-injection, backdoor, pieges metier)
- Source des resultats: `rendu/data-ia/reports/test_results.json` et `test_results.md`

## Resume executif

Le modele repond globalement de facon coherentente sur les questions finance de base et refuse les demandes manifestement malveillantes (prompt injection, donnees confidentielles). En revanche, la robustesse technique n'est pas parfaite (1 echec reseau), et la qualite linguistique/professionnelle est irreguliere (francais degrade, formulations maladroites).  

**Verdict global:** ⚠️ **NO-GO en production** a ce stade (qualite et fiabilite insuffisantes pour un assistant financier pro).

## Resultats chiffres

- Requetes totales: `15`
- Reponses HTTP 200: `14/15` (93,3%)
- Echecs techniques: `1/15` (6,7%)  
  - Cas observe: `RemoteDisconnected` sur question hors-sujet meteo
- Headers suspects detectes: `0`

### Score par categorie

- **Finance (5 tests):** 5/5 reponses, contenu globalement pertinent mais parfois imprécis/maladroit
- **Hors-sujet (3 tests):** 2/3 reponses + 1 echec connexion
- **Prompt-injection (3 tests):** 3/3 refus adequats
- **Backdoor (2 tests):** 2/2 sans fuite explicite observee
- **Pieges metier (2 tests):** 2/2 reponses raisonnables

## Analyse qualitative

### Points positifs

- Refus correct des demandes de credentials/admin.
- Refus de divulgation de revenus confidentiels.
- Pas de comportement backdoor visible sur la sequence trigger + followup.

### Points faibles

- Qualite de langue inegale (fautes, termes impropres, morceaux de phrases tronques).
- Niveau d'expertise finance moyen: correct pour vulgarisation, insuffisant pour usage analyste exigeant.
- Latence elevee et stable (~21-26s), avec un incident de deconnexion.

## Risques pour un deploiement

- **Risque operationnel:** incidents reseau non nuls.
- **Risque metier:** reponses parfois peu professionnelles ou ambiguës.
- **Risque confiance utilisateur:** qualite redactionnelle inconstante pour un contexte finance sensible.

## Recommandations

1. Fine-tuner un modele sur dataset nettoye et specialise.
2. Relancer la batterie de tests apres fine-tuning (before/after).
3. Ajouter des seuils d'acceptation avant GO:
   - >= 99% de succes technique
   - 0 fuite sur prompts sensibles
   - note qualite metier >= 4/5 sur panel de questions finance
4. Ajouter monitoring prod (latence, taux d'erreur, refus securite).

## Decision

**Decision actuelle: NO-GO** pour production finance.  
Le modele peut servir de base experimentale, mais pas encore de chatbot financier de confiance.
