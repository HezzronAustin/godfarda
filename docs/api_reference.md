# API Reference

This document details the REST API endpoints provided by the AI Tools Ecosystem.

## Base URL

All API endpoints are prefixed with `/api/v1/`

## Authentication

All endpoints require an API key passed in the `X-API-Key` header:

```bash
X-API-Key: your-api-key
```

## Endpoints

### Tools

#### List Tools

```
GET /api/v1/tools
```

Lists all available tools and their descriptions.

**Response**
```json
{
    "tools": {
        "TextAnalyzer": "Analyzes text for various metrics including word count and sentiment",
        "ImageProcessor": "Processes and analyzes images"
    }
}
```

#### Execute Tool

```
POST /api/v1/tools/{tool_name}
```

Executes a specific tool with the provided parameters.

**Request Body**
```json
{
    "parameters": {
        "param1": "value1",
        "param2": "value2"
    }
}
```

**Response**
```json
{
    "success": true,
    "data": {
        "result": "tool_specific_result"
    }
}
```

**Error Response**
```json
{
    "success": false,
    "error": "Error message"
}
```

### Agents

#### List Agents

```
GET /api/v1/agents
```

Lists all available agents and their descriptions.

**Response**
```json
{
    "agents": {
        "TextProcessor": "Processes text using various analysis tools",
        "ImageAnalyzer": "Analyzes images using multiple tools"
    }
}
```

#### Process with Agent

```
POST /api/v1/agents/{agent_name}
```

Processes input data using a specific agent.

**Request Body**
```json
{
    "input_data": {
        "key1": "value1",
        "key2": "value2"
    }
}
```

**Response**
```json
{
    "success": true,
    "result": {
        "processed_data": "agent_specific_result"
    }
}
```

**Error Response**
```json
{
    "success": false,
    "error": "Error message"
}
```

## Error Codes

- `400`: Bad Request - Invalid parameters or input data
- `401`: Unauthorized - Missing or invalid API key
- `404`: Not Found - Tool or agent not found
- `500`: Internal Server Error - Server-side error

## Rate Limiting

The API implements rate limiting based on the API key:
- 100 requests per minute for tools
- 50 requests per minute for agents

## Example Usage

### Using curl

#### Execute a Tool
```bash
curl -X POST "http://localhost:8000/api/v1/tools/TextAnalyzer" \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
           "parameters": {
             "text": "This is a test message",
             "analysis_type": "sentiment"
           }
         }'
```

#### Use an Agent
```bash
curl -X POST "http://localhost:8000/api/v1/agents/TextProcessor" \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
           "input_data": {
             "text": "This is a test message",
             "max_length": 50
           }
         }'
```

### Using Python

```python
import requests
import json

API_BASE = "http://localhost:8000/api/v1"
API_KEY = "your-api-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Execute a tool
response = requests.post(
    f"{API_BASE}/tools/TextAnalyzer",
    headers=headers,
    json={
        "parameters": {
            "text": "This is a test message",
            "analysis_type": "sentiment"
        }
    }
)
print(response.json())

# Use an agent
response = requests.post(
    f"{API_BASE}/agents/TextProcessor",
    headers=headers,
    json={
        "input_data": {
            "text": "This is a test message",
            "max_length": 50
        }
    }
)
print(response.json())
```
