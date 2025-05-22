import requests
import json

# ----------- CONFIGURATION ------------

KONNECT_HOST = "https://<KONNECT_REGION>.api.konghq.com"
KONNECT_PAT = "<KONNECT_PERSONAL_ACCESS_TOKEN>"

PORT_API_URL       = "https://api.getport.io/v1"
PORT_CLIENT_ID     = "<PORT_CLIENT_ID>"
PORT_CLIENT_SECRET = "<PORT_CLIENT_SECRET>"

KONG_API_ID = "<KONG_API_UNIQUE_IDENTIFIER>"

# ----------- MAPPING: Konnect Type → Port Blueprint ------------

TYPE_TO_BLUEPRINT = {
    "api_product": "kongApiProduct",
    "api_product_version": "kongApiVersion",
    "service": "kongApi",
    "route": "kongApiRoute",
    "consumer": "consumer"  # ✅ Now treated like other types
}

# ----------- AUTHENTICATION ------------

def generate_port_access_token():
    resp = requests.post(
        f"{PORT_API_URL}/auth/access_token",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        json={"clientId": PORT_CLIENT_ID, "clientSecret": PORT_CLIENT_SECRET}
    )
    if resp.status_code == 200:
        print("✅ Authenticated with Port")
        return resp.json()["accessToken"]
    else:
        raise SystemExit(f"❌ Port auth failed: {resp.status_code} {resp.text}")

# ----------- KONG KONNECT DATA FETCHING ------------

def fetch_entities_by_type(entity_type):
    url = f"{KONNECT_HOST}/v1/search?q=type%3A{entity_type}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {KONNECT_PAT}",
        "Content-Type": "application/json"
    }
    res = requests.get(url, headers=headers)
    if res.ok:
        return res.json().get("data", [])
    print(f"❌ Failed to fetch {entity_type}: {res.status_code} {res.text}")
    return []

# ----------- CONVERSION FUNCTIONS BY TYPE ------------

def transform_api_product(e):
    return {
        "identifier": e["name"],
        "title": e.get("name"),
        "properties": {
            "name": e.get("name"),
            "description": e.get("description"),
            "visibility": e.get("attributes", {}).get("visibility"),
            "createdAt": e.get("attributes", {}).get("created_at"),
            "updatedAt": e.get("attributes", {}).get("updated_at"),
            "labels": e.get("labels", {})
        }
    }

def transform_api_product_version(e):
    labels = e.get("labels", {})
    service_name = labels.get("service")
    service_identifier = None
    if service_name:
        service_identifier = next((s["id"] for s in services_cache if s.get("name") == service_name), None)

    return {
        "identifier": e["id"],
        "title": e.get("name"),
        "properties": {
            "version": e.get("name"),
            "status": e.get("attributes", {}).get("publish_status"),
            "createdAt": e.get("attributes", {}).get("created_at"),
            "deprecated": e.get("attributes", {}).get("deprecated"),
            "updatedAt": e.get("attributes", {}).get("updated_at")
        },
        "relations": {
            "api": service_identifier,
            "product": "Integrations"
        }
    }

def transform_service(e):
    a = e.get("attributes", {})
    return {
        "identifier": e["id"].split(":")[1],
        "title": e.get("name"),
        "properties": {
            "name": e.get("name"),
            "description": e.get("description"),
            "enabled": a.get("enabled"),
            "host": a.get("host"),
            "port": a.get("port"),
            "protocol": a.get("protocol"),
            "path": a.get("path"),
            "url": a.get("url"),
            "tags": a.get("tags"),
            "createdAt": a.get("created_at"),
            "updatedAt": a.get("updated_at")
        },
        "relations": {
            "product": a["tags"][0]
        } if a["tags"] else {}
    }

def transform_route(e):
    attributes = e.get("attributes", {})
    return {
        "identifier": e["name"],
        "title": e.get("name"),
        "properties": {
            "path": attributes.get("paths", [None])[0],
            "methods": attributes.get("methods", []),
            "host": attributes.get("hosts", [None])[0] if attributes.get("hosts") else None,
            "stripPath": attributes.get("strip_path"),
            "preserveHost": attributes.get("preserve_host"),
            "createdAt": attributes.get("created_at"),
            "updatedAt": attributes.get("updated_at")
        },
        "relations": {
            "api": attributes.get("service_id")
        }
    }

def transform_consumer(e):
    a = e.get("attributes", {})
    return {
        "identifier": e["id"],
        "title": a.get("username") or e.get("name"),
        "properties": {
            "username": a.get("username"),
            "custom_id": a.get("custom_id"),
            "tags": a.get("tags", []),
            "created_at": a.get("created_at"),
            "updated_at": a.get("updated_at")
        },
        "relations": {
            "control_plane_id": KONG_API_ID
        }
    }

# ----------- TRANSFORMATION MAPPING ------------

TRANSFORM_BY_TYPE = {
    "api_product": transform_api_product,
    "api_product_version": transform_api_product_version,
    "service": transform_service,
    "route": transform_route,
    "consumer": transform_consumer
}

# ----------- PORT INGESTION ------------

def push_entities_to_port(blueprint_id, entities, token):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    for e in entities:
        res = requests.post(
            f"{PORT_API_URL}/blueprints/{blueprint_id}/entities"
            "?upsert=true&create_missing_related_entities=true",
            headers=headers,
            json=e
        )
        if 200 <= res.status_code < 300:
            print(f"✅ Pushed to {blueprint_id}: {e['identifier']}")
        else:
            print(f"❌ {blueprint_id} error {res.status_code}: {res.text}")

# ----------- MAIN EXECUTION ------------

if __name__ == "__main__":
    port_token = generate_port_access_token()

    # Service first because version relations depend on it
    services_cache = fetch_entities_by_type("service")
    service_entities = [transform_service(s) for s in services_cache]
    push_entities_to_port("kongApi", service_entities, port_token)

    # Process all other types (including consumer)
    for konnect_type, blueprint_id in TYPE_TO_BLUEPRINT.items():
        if konnect_type == "service":
            continue  # already handled above
        print(f"\n--- Syncing type: {konnect_type} → blueprint: {blueprint_id} ---")
        data = fetch_entities_by_type(konnect_type)
        transform_fn = TRANSFORM_BY_TYPE.get(konnect_type, lambda e: e)
        entities = [transform_fn(e) for e in data]
        push_entities_to_port(blueprint_id, entities, port_token)
