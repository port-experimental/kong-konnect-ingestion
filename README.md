
# Kong Konnect to Port Integration

This script syncs data from Kong Konnect (API Products, Services, Routes, Consumers, etc.) into Port using defined blueprints.

---

## 📋 Prerequisites

Before running the script, ensure you have the following:

- ✅ **Port Client ID and Secret**  
  These are required to authenticate with the Port API.  
  [Documentation](https://docs.getport.io)

- ✅ **Kong Personal Access Token (PAT)**  
  Used to authenticate with the Kong Konnect API.  
  [Create PAT](https://docs.konghq.com/konnect/dev-portal/personal-access-tokens/)

- ✅ **Kong Control Plane ID**  
  This identifies the specific Kong API control plane being used.

---

## 🔧 Blueprints

### 🧩 Kong API Version

```json
{
  "identifier": "kongApiVersion",
  "title": "Kong API Version",
  "icon": "ApiDoc",
  "schema": {
    "properties": {
      "version": { "title": "Version", "type": "string" },
      "status": { "title": "Status", "type": "string" },
      "createdAt": { "title": "Created At", "type": "string", "format": "date-time" },
      "deprecated": { "type": "boolean", "title": "Deprecated" },
      "updatedAt": { "title": "Updated At", "type": "string", "format": "date-time" }
    },
    "required": ["version"]
  },
  "relations": {
    "product": {
      "title": "API Product",
      "target": "kongApiProduct",
      "required": false,
      "many": false
    }
  }
}
```

---

### 🧩 Kong API

```json
{
  "identifier": "kongApi",
  "title": "Kong API",
  "icon": "Service",
  "schema": {
    "properties": {
      "name": { "title": "Name", "type": "string" },
      "description": { "title": "Description", "type": "string" },
      "enabled": { "type": "boolean", "title": "Enabled" },
      "host": { "type": "string", "title": "Host" },
      "port": { "type": "number", "title": "Port" },
      "protocol": { "type": "string", "title": "Protocol" },
      "path": { "type": "string", "title": "Path" },
      "url": { "type": "string", "format": "url", "title": "Upstream URL" },
      "tags": { "type": "array", "items": { "type": "string" }, "title": "Tags" },
      "createdAt": { "type": "string", "format": "date-time", "title": "Created At" },
      "updatedAt": { "type": "string", "format": "date-time", "title": "Updated At" }
    },
    "required": ["name"]
  },
  "relations": {
    "product": {
      "title": "Product",
      "target": "kongApiProduct",
      "required": false,
      "many": false
    }
  }
}
```

---

### 🧩 Kong API Key

```json
{
  "identifier": "kong_api_key",
  "title": "Kong API Key",
  "icon": "Key",
  "schema": {
    "properties": {
      "link": { "type": "string", "title": "Link", "format": "url" },
      "ttl": { "type": "string", "title": "TTL", "format": "timer" }
    }
  },
  "relations": {
    "consumer": {
      "title": "Consumer",
      "target": "consumer",
      "required": false,
      "many": false
    }
  }
}
```

---

### 🧩 Kong API Product

```json
{
  "identifier": "kongApiProduct",
  "title": "Kong API Product",
  "icon": "Package",
  "schema": {
    "properties": {
      "name": { "type": "string", "title": "Name" },
      "description": { "type": "string", "title": "Description" },
      "visibility": { "type": "string", "title": "Visibility" },
      "createdAt": { "type": "string", "format": "date-time", "title": "Created At" },
      "updatedAt": { "type": "string", "format": "date-time", "title": "Updated At" },
      "labels": { "type": "object", "title": "Labels" }
    },
    "required": ["name"]
  }
}
```

---

### 🧩 Kong API Route

```json
{
  "identifier": "kongApiRoute",
  "title": "Kong API Route",
  "icon": "APIEndpoint",
  "schema": {
    "properties": {
      "path": { "type": "string", "title": "Path" },
      "methods": { "type": "array", "items": { "type": "string" }, "title": "Methods" },
      "host": { "type": "string", "title": "Host" },
      "stripPath": { "type": "boolean", "title": "Strip Path" },
      "preserveHost": { "type": "boolean", "title": "Preserve Host" },
      "createdAt": { "type": "string", "format": "date-time", "title": "Created At" },
      "updatedAt": { "type": "string", "format": "date-time", "title": "Updated At" }
    },
    "required": ["path"]
  },
  "relations": {
    "api": {
      "title": "API",
      "target": "kongApi",
      "required": false,
      "many": false
    }
  }
}
```

---

## 🚀 Running the Script

### 1. Update Credentials

Edit the script and update the following placeholders in the configuration section:

```python
KONNECT_HOST = "https://<KONNECT_REGION>.api.konghq.com"
KONNECT_PAT = "<KONNECT_PERSONAL_ACCESS_TOKEN>"

PORT_API_URL       = "https://api.getport.io/v1"
PORT_CLIENT_ID     = "<PORT_CLIENT_ID>"
PORT_CLIENT_SECRET = "<PORT_CLIENT_SECRET>"

KONG_API_ID = "<KONG_API_UNIQUE_IDENTIFIER>"
```

---

### 2. Run the Script

Once the credentials are set:

```bash
python konnect_to_port.py
```

This will:
- Authenticate with Port
- Fetch entities from Kong Konnect
- Transform them to Port schema
- Push them to the appropriate blueprints in Port

Make sure the Port blueprints are already defined before ingestion.

---

## 🧠 Notes

- Script uses `upsert=true` and `create_missing_related_entities=true` to avoid duplicates and auto-link related entities.
- Order of ingestion is important: services are processed first to ensure relations (like API versions) work correctly.

---

For more, visit [getport.io](https://www.getport.io) and [Kong Konnect Docs](https://docs.konghq.com/konnect/).
