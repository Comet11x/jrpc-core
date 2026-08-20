# Qu'est-ce que jrpc-core ?

**jrpc-core** est une bibliothèque Python légère qui implémente la [spécification JSON-RPC 2.0](https://www.jsonrpc.org/specification) avec deux couches principales :

| Couche | Module | Objectif |
|---|---|---|
| **Messages** | `jrpc_core.messages` | Modèles Pydantic pour les requêtes, réponses, notifications et erreurs |
| **Dispatcher** | `jrpc_core.dispatcher` | Routage basé sur un registre des messages entrants vers les handlers |

## Principes de Conception

- **Type-safe** — chaque modèle est un `BaseModel` de Pydantic avec des types de champs et validateurs explicites.
- **Fonctionnel** — la gestion des erreurs utilise `Result` et `Option` de [pyfplib](https://pypi.org/project/pyfplib/) au lieu des exceptions.
- **Léger** — ne dépend que de `pydantic` et `pyfplib`, pas de runtime async requis.
- **Sérialisable** — aller-retour propre entre les objets Python et les chaînes JSON.

## Architecture

```
Chaîne JSON entrante
        │
        ▼
   try_parse()
        │
   ┌────┴────┐
   │         │
Requête  Notification
   │         │
   ▼         ▼
JsonRpcDispatcher.__call__()
   │
   ├──► recherche dans le registre des handlers
   │
   ▼
JsonRpcResponse
```

## Étapes Suivantes

- [Pour Commencer](/fr/guide/getting-started) — installation et première requête
- [API Messages](/fr/guide/messages) — référence complète pour tous les modèles de messages
- [API Dispatcher](/fr/guide/dispatcher) — référence complète pour le routage et l'enregistrement des handlers
