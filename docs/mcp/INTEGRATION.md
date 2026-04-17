# BrainCell MCP Integration Guide

## Overview

This guide shows how to integrate the BrainCell MCP Server with different agent frameworks and AI models.

## Table of Contents

- [Claude (Anthropic)](#claude-anthropic)
- [Custom Python Agents](#custom-python-agents)
- [Azure AI Agents](#azure-ai-agents)
- [Model Context Protocol (MCP) Standard](#model-context-protocol)
- [Docker Deployment](#docker-deployment)

---

## Claude (Anthropic)

### Standard Integration

```python
from anthropic import Anthropic

client = Anthropic()

# Define BrainCell tools for Claude
braincell_tools = [
    {
        "name": "search_braincell_memory",
        "description": "Search BrainCell memory for relevant information",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for in BrainCell"
                },
                "memory_type": {
                    "type": "string",
                    "enum": ["conversations", "decisions", "snippets", "architecture"],
                    "description": "Type of memory to search"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "save_decision_to_braincell",
        "description": "Save a design decision to BrainCell memory",
        "input_schema": {
            "type": "object",
            "properties": {
                "decision": {"type": "string"},
                "rationale": {"type": "string"},
                "impact": {"type": "string"}
            },
            "required": ["decision"]
        }
    }
]

# System prompt with BrainCell awareness
system_prompt = """You are an AI assistant with access to BrainCell, 
a persistent memory system. Before making decisions:
1. Search BrainCell for relevant previous decisions and patterns
2. Consider architectural decisions already made
3. Save important new decisions to BrainCell for future reference
Use the BrainCell tools to access and update organizational knowledge."""

# Conversation with Claude using BrainCell
messages = [
    {"role": "user", "content": "How should we design our API gateway?"}
]

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system=system_prompt,
    tools=braincell_tools,
    messages=messages
)

# Process tool calls from Claude
if response.stop_reason == "tool_use":
    for content_block in response.content:
        if content_block.type == "tool_use":
            tool_name = content_block.name
            tool_input = content_block.input
            
            # Call BrainCell based on tool used
            if tool_name == "search_braincell_memory":
                # Implement search call
                pass
            elif tool_name == "save_decision_to_braincell":
                # Implement save call
                pass
```

### With Tool Use Streaming

```python
from anthropic import Anthropic
import requests
import json

client = Anthropic()

def handle_braincell_tool(tool_name: str, tool_input: dict) -> str:
    """Handle BrainCell tool calls"""
    base_url = "http://localhost:9506"
    
    if tool_name == "search_braincell_memory":
        response = requests.post(
            f"{base_url}/tools/search_memory",
            json={
                "query": tool_input["query"],
                "memory_type": tool_input.get("memory_type"),
                "limit": 10
            }
        )
        return json.dumps(response.json())
    
    elif tool_name == "save_decision_to_braincell":
        response = requests.post(
            f"{base_url}/tools/save_decision",
            json={
                "decision": tool_input["decision"],
                "rationale": tool_input.get("rationale"),
                "impact": tool_input.get("impact")
            }
        )
        return json.dumps(response.json())
    
    return json.dumps({"error": "Unknown tool"})

def chat_with_braincell(user_message: str) -> str:
    """Chat with Claude while accessing BrainCell"""
    
    tools = [
        {
            "name": "search_braincell_memory",
            "description": "Search BrainCell for architectural patterns and decisions",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "memory_type": {
                        "type": "string",
                        "enum": ["conversations", "decisions", "snippets", "architecture"]
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "save_decision_to_braincell",
            "description": "Save important decisions to BrainCell",
            "input_schema": {
                "type": "object",
                "properties": {
                    "decision": {"type": "string"},
                    "rationale": {"type": "string"},
                    "impact": {"type": "string"}
                },
                "required": ["decision"]
            }
        }
    ]
    
    messages = [{"role": "user", "content": user_message}]
    
    while True:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            tools=tools,
            messages=messages
        )
        
        # Check if we're done
        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, 'text'):
                    return block.text
            return "Response generated"
        
        # Handle tool use
        if response.stop_reason == "tool_use":
            # Add assistant response to messages
            messages.append({"role": "assistant", "content": response.content})
            
            # Process each tool use
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = handle_braincell_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })
            
            # Add tool results to messages
            messages.append({"role": "user", "content": tool_results})
        else:
            break
    
    return "Conversation complete"

# Example usage
if __name__ == "__main__":
    response = chat_with_braincell(
        "Search our memory for API gateway patterns, then design a new API gateway"
    )
    print(response)
```

---

## Custom Python Agents

### Simple Agent

```python
import logging
from braincell_mcp_client import BrainCellMCPClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAgent:
    """A simple agent that uses BrainCell for decision support"""
    
    def __init__(self):
        self.braincell = BrainCellMCPClient()
        self.decision_log = []
    
    def plan_task(self, task_description: str) -> dict:
        """Plan a task using BrainCell context"""
        
        # Get relevant context from BrainCell
        context = self.braincell.get_relevant_context(task_description, limit=10)
        
        plan = {
            "task": task_description,
            "context": context,
            "steps": [],
            "estimated_complexity": "medium"
        }
        
        # Use context to inform plan
        if context.get('success'):
            decisions = context['data'].get('recent_decisions', [])
            plan['estimated_complexity'] = "high" if len(decisions) > 3 else "medium"
            plan['relevant_decisions'] = decisions
        
        logger.info(f"Planned {task_description} with {len(plan.get('relevant_decisions', []))} relevant decisions")
        return plan
    
    def execute_and_learn(self, plan: dict) -> dict:
        """Execute plan and save learnings to BrainCell"""
        
        execution_result = {
            "status": "completed",
            "decisions_made": [],
            "code_patterns": [],
            "lessons_learned": []
        }
        
        # After execution, save decisions and patterns
        for decision in execution_result['decisions_made']:
            self.braincell.save_decision(
                decision=decision['what'],
                rationale=decision['why'],
                impact=decision['impact']
            )
        
        # Save code patterns
        for pattern in execution_result['code_patterns']:
            self.braincell.save_code_snippet(
                title=pattern['name'],
                code_content=pattern['code'],
                language=pattern['language'],
                description=pattern['description'],
                tags=pattern.get('tags', [])
            )
        
        logger.info(f"Saved {len(execution_result['decisions_made'])} decisions and "
                   f"{len(execution_result['code_patterns'])} code patterns")
        
        return execution_result

# Usage
agent = SimpleAgent()
plan = agent.plan_task("Implement user authentication")
# ... execute plan ...
result = agent.execute_and_learn(plan)
```

### Advanced Agent with Reasoning

```python
from typing import List, Dict, Any
from braincell_mcp_client import BrainCellMCPClient
import json

class ReasoningAgent:
    """Agent that reasons through problems using BrainCell memory"""
    
    def __init__(self, braincell_url: str = "http://localhost:9506"):
        self.braincell = BrainCellMCPClient(braincell_url)
        self.reasoning_trace = []
    
    def reason_about_problem(self, problem: str) -> Dict[str, Any]:
        """Multi-step reasoning with BrainCell context"""
        
        trace = {
            "problem": problem,
            "steps": []
        }
        
        # Step 1: Search for similar problems
        step1 = {
            "name": "search_similar_problems",
            "query": f"Similar to: {problem}"
        }
        similar = self.braincell.search_memory(step1['query'], limit=5)
        step1['results'] = similar.get('data', {}).get('results', [])
        trace['steps'].append(step1)
        
        # Step 2: Find relevant architectural decisions
        step2 = {
            "name": "find_architecture_decisions",
            "query": f"Architecture for: {problem}"
        }
        arch = self.braincell.search_architecture(step2['query'], limit=5)
        step2['results'] = arch.get('data', {}).get('results', [])
        trace['steps'].append(step2)
        
        # Step 3: Look for code patterns
        step3 = {
            "name": "find_code_patterns",
            "query": f"Code pattern for: {problem}"
        }
        patterns = self.braincell.search_code_snippets(step3['query'], limit=5)
        step3['results'] = patterns.get('data', {}).get('results', [])
        trace['steps'].append(step3)
        
        # Step 4: Synthesis - make recommendations
        step4 = {
            "name": "synthesize_solution",
            "recommendation": self._synthesize(trace['steps']),
            "confidence": 0.85
        }
        trace['steps'].append(step4)
        
        self.reasoning_trace.append(trace)
        return trace
    
    def _synthesize(self, steps: List[Dict]) -> str:
        """Synthesize solution from reasoning steps"""
        
        total_relevant = sum(
            len(step.get('results', [])) for step in steps[:-1]
        )
        
        if total_relevant > 10:
            return "Strong precedent for this solution - follow existing patterns"
        elif total_relevant > 5:
            return "Moderate precedent - combine existing patterns with new approach"
        else:
            return "Limited precedent - consider documenting this as new pattern"

# Usage
agent = ReasoningAgent()
trace = agent.reason_about_problem("Design rate limiting for microservices")
print(json.dumps(trace, indent=2))
```

---

## Azure AI Agents

### Azure AI Toolkit Integration

```python
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ToolDefinition
from azure.identity import DefaultAzureCredential
import os

# Initialize Azure AI Project
credential = DefaultAzureCredential()
client = AIProjectClient.from_connection_string(
    credential=credential,
    conn_str=os.getenv("AIPROJECT_CONNECTION_STRING")
)

# Define BrainCell tools
braincell_tools = [
    ToolDefinition(
        name="search_braincell",
        description="Search BrainCell persistent memory for information",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "memory_type": {
                    "type": "string",
                    "enum": ["conversations", "decisions", "snippets", "architecture"],
                    "description": "Type of memory to search"
                }
            },
            "required": ["query"]
        }
    ),
    ToolDefinition(
        name="save_braincell_decision",
        description="Save a decision to BrainCell memory",
        parameters={
            "type": "object",
            "properties": {
                "decision": {"type": "string"},
                "rationale": {"type": "string"},
                "impact": {"type": "string"}
            },
            "required": ["decision"]
        }
    )
]

# Create agent with BrainCell tools
agent = client.agents.create_agent(
    name="BrainCellAwareAgent",
    description="Agent with access to persistent memory via BrainCell",
    instructions="""You are an AI agent with access to organizational memory via BrainCell.
Before making decisions:
1. Search BrainCell for relevant architectural decisions
2. Check for similar past implementations
3. Save important new decisions to BrainCell
Always leverage organizational knowledge and contribute back to it.""",
    tools=braincell_tools,
    model="gpt-4o",
)

# Use the agent
response = client.agents.run(
    agent_id=agent.id,
    user_message="Design a caching strategy for our API"
)

print(response.messages[-1].content)
```

---

## Model Context Protocol

### Standard MCP Implementation

The BrainCell MCP Server implements the Model Context Protocol standard, which allows:

1. **Tool Discovery**: Agents can discover available tools
2. **Tool Invocation**: Agents can call tools by name and parameters
3. **Tool Results**: Tools return structured results to agents
4. **Streaming**: Support for long-running operations

### Connecting via MCP

Any MCP-compatible agent can connect:

```bash
# MCP Server runs on port 9506
# Agents connect via HTTP to discover and invoke tools

curl http://localhost:9506/tools
curl http://localhost:9506/health
```

---

## Testing Integration

### Test with curl

```bash
# Start MCP server
docker-compose up -d braincell-mcp

# Test health
curl http://localhost:9506/health

# Test search
curl -X POST http://localhost:9506/tools/search_memory \
  -H "Content-Type: application/json" \
  -d '{"query": "caching patterns"}'

# Test save decision
curl -X POST http://localhost:9506/tools/save_decision \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "Use Redis for distributed caching",
    "rationale": "High performance, widely supported",
    "impact": "Requires Redis cluster setup"
  }'
```

### Test with Python

```python
from braincell_mcp_client import BrainCellMCPClient

# Create client
client = BrainCellMCPClient()

# Test all operations
print("✓ Health:", client.health_check()['data']['status'])
print("✓ Tools:", len(client.list_tools()))
print("✓ Search:", client.search_memory("test")['data']['count'])
print("✓ Save:", client.save_decision("test decision")['success'])
```

---

## Best Practices

### 1. Error Handling
```python
try:
    result = client.search_memory("query")
    if not result.get('success'):
        logger.error(f"Search failed: {result.get('error')}")
except Exception as e:
    logger.error(f"Connection error: {e}")
```

### 2. Caching Responses
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_architecture_context(query: str):
    return client.get_relevant_context(query)
```

### 3. Rate Limiting
```python
from time import sleep
from functools import wraps

def rate_limit(calls_per_minute=10):
    min_interval = 60 / calls_per_minute
    
    def decorator(func):
        last_called = [0.0]
        
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                sleep(min_interval - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator
```

### 4. Batching Operations
```python
def batch_save_decisions(decisions):
    """Save multiple decisions efficiently"""
    saved = []
    for decision in decisions:
        result = client.save_decision(
            decision=decision['text'],
            rationale=decision['why']
        )
        if result['success']:
            saved.append(result['data']['id'])
    return saved
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Agent can't find tools | Verify MCP server running: `curl http://localhost:9506/health` |
| Search returns empty | Check memories exist: `curl http://localhost:9506/tools/list_memories` |
| Connection timeout | Ensure all services healthy: `docker-compose ps` |
| Slow performance | Check Redis/Weaviate status in health endpoint |

---

## Next Steps

1. **Choose Integration**: Pick your agent framework above
2. **Test Connection**: Run health check endpoint
3. **Start Storing**: Save decisions and code patterns
4. **Query Memory**: Use search to retrieve context
5. **Build Workflow**: Integrate into your agent pipeline

For more details, see [GUIDE.md](GUIDE.md)
