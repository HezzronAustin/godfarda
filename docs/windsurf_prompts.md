# Windsurf Guided Prompts for AI Tools Ecosystem

This document provides a set of guided prompts and rules for interacting with the AI Tools Ecosystem through Windsurf.

## Agent Interaction Rules

1. **Message Format Validation**
```
Always validate that messages to agents follow the standard format:
{
    "message": str,
    "user_info": dict,
    "platform": str
}
Ensure all required fields are present and properly formatted.
```

2. **Agent Selection Guidelines**
```
When selecting an agent for delegation:
- Use GodFarda for general queries and orchestration
- Use @textagent for text processing and analysis
- Use @communicationsagent for platform-specific communication
Always respect agent capabilities and limitations.
```

3. **Error Handling Protocol**
```
When handling agent responses:
1. Check for "error" field in responses
2. Provide appropriate error messages to users
3. Suggest corrective actions when errors occur
4. Maintain error context for debugging
```

## Prompt Templates

### 1. General Queries (GodFarda)
```
Template: "I need help with [task]. Can you [specific request]?"
Example: "I need help with text analysis. Can you suggest which agent would be best for summarizing a long article?"
```

### 2. Text Processing (@textagent)
```
Template: "@textagent [specific text operation] the following: [content]"
Example: "@textagent summarize the following article: [article text]"
```

### 3. Communication Tasks (@communicationsagent)
```
Template: "@communicationsagent send [message type] to [platform]: [content]"
Example: "@communicationsagent send message to telegram: Hello World"
```

## Response Handling Rules

1. **Success Responses**
```
For successful responses:
1. Extract relevant information from "response" field
2. Format output according to platform requirements
3. Preserve agent attribution
4. Maintain conversation context
```

2. **Error Responses**
```
For error responses:
1. Parse error message from response
2. Provide user-friendly error explanation
3. Suggest alternative approaches
4. Log errors for system improvement
```

## Context Management

1. **User Context**
```
Maintain and pass through:
- User identification
- Platform information
- Session history
- Previous interactions
```

2. **Agent Context**
```
Track and manage:
- Current active agent
- Delegated tasks
- Cross-agent communication
- Task state
```

## Best Practice Prompts

1. **Task Clarity**
```
Before processing any request:
1. Ensure task requirements are clear
2. Validate input format
3. Check agent availability
4. Verify user permissions
```

2. **Agent Coordination**
```
When multiple agents are involved:
1. Define clear handoff points
2. Maintain task context
3. Track task progress
4. Ensure response consistency
```

3. **Platform Compatibility**
```
For cross-platform operations:
1. Validate platform support
2. Format messages appropriately
3. Handle platform-specific features
4. Manage rate limits
```

## System Integration Guidelines

1. **Tool Registration**
```
When registering new tools:
1. Verify tool compatibility
2. Update agent capabilities
3. Document new functionalities
4. Test integration points
```

2. **Agent Updates**
```
When updating agents:
1. Maintain backward compatibility
2. Update documentation
3. Verify existing functionality
4. Test new features
```

## Quality Assurance Prompts

1. **Input Validation**
```
Before processing:
1. Validate message format
2. Check required fields
3. Verify data types
4. Sanitize input
```

2. **Output Validation**
```
Before responding:
1. Verify response format
2. Check for sensitive information
3. Validate against schema
4. Format for readability
```

These prompts and rules ensure consistent, reliable interaction with the AI Tools Ecosystem through Windsurf.
