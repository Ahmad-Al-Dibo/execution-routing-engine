# Query Runtime Documentation 📚

This document describes the `query_runtime.py` system — a query routing and execution engine that analyzes user prompts and routes them to relevant commands and tools.

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Models & Data Structures](#models--data-structures)
4. [Components in Detail](#components-in-detail)
5. [Workflows & Flows](#workflows--flows)
6. [Example Usage](#example-usage)
7. [Configuration & Customization](#configuration--customization)

---

## System Overview

### What does this system do?

The `query_runtime.py` system analyzes a **user prompt** (e.g. `"Search how data processing using python?"`) and:

1. **Routes** the prompt to relevant **commands** and **tools**
2. **Executes** those commands/tools in order of relevance
3. **Collects** all results and execution messages
4. **Returns** a complete `RuntimeSession` containing all findings

### Core Idea

Instead of having every user request execute everything directly, the system:

- Analyzes what the user wants
- Determines which functionality is needed
- Executes only the relevant components
- Returns structured results

---

## Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INPUT (PROMPT)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. ROUTING                                                 │
│     ┌─────────────────────────────────────────────┐         │
│     │  PortRouter analyzes the prompt            │         │
│     │  - Tokenize input                          │         │
│     │  - Match against PORTED_COMMANDS & TOOLS   │         │
│     │  - Score & sort by relevance               │         │
│     └─────────────────────────────────────────────┘         │
│                          ↓                                  │
│  2. EXECUTION                                               │
│     ┌─────────────────────────────────────────────┐         │
│     │  ExecutionEngine executes matches          │         │
│     │  - Finds commands in ExecutionRegistry     │         │
│     │  - Finds tools in ExecutionRegistry        │         │
│     │  - Checks permissions                      │         │
│     │  - Collects output messages                │         │
│     └─────────────────────────────────────────────┘         │
│                          ↓                                  │
│  3. RESULT COMPILATION                                      │
│     ┌─────────────────────────────────────────────┐         │
│     │  QueryEngine collects everything           │         │
│     │  CleanRuntime packages into RuntimeSession │         │
│     └─────────────────────────────────────────────┘         │
│                          ↓                                  │
├─────────────────────────────────────────────────────────────┤
│                  OUTPUT: RuntimeSession                     │
│  - matched_commands, matched_tools, permission_denials     │
│  - execution_messages, routed_matches                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Models & Data Structures

### 1. RoutedMatch

**Purpose**: Represents a matched command or tool after routing.

```python
@dataclass
class RoutedMatch:
    kind: str           # "command" or "tool"
    name: str           # Name: "search", "python", etc.
    source_hint: str    # Where it comes from
    score: int          # Relevance score (higher = more relevant)
```

**Example**:

```python
RoutedMatch(
    kind="command",
    name="search",
    source_hint="query engine",
    score=3
)
```

---

### 2. PortingModule

**Purpose**: Describes an available command or tool in the system.

```python
@dataclass
class PortingModule:
    name: str
    source_hint: str
    responsibility: str
```

**Example**:

```python
PortingModule(
    name="python",
    source_hint="execution environment",
    responsibility="run python code"
)
```

---

### 3. TurnResult

**Purpose**: Contains the result of a single request processing cycle.

```python
@dataclass
class TurnResult:
    matched_commands: Tuple[str, ...]
    matched_tools: Tuple[str, ...]
    permission_denials: Tuple[str, ...]
    stop_reason: str
```

---

### 4. RuntimeSession

**Purpose**: Complete session information — the final result.

```python
@dataclass
class RuntimeSession:
    prompt: str
    routed_matches: List[RoutedMatch]
    turn_result: TurnResult
    command_execution_messages: Tuple[str, ...]
    tool_execution_messages: Tuple[str, ...]
```

**This is what gets returned to the user.**

---

## Components in Detail

### 1. Command & Tool Classes

**Command** and **Tool** are very similar — both are executable components.

```python
class Command:
    """Represents an executable command"""
    def __init__(self, name: str):
        self.name = name
    
    def execute(self, prompt: str) -> str:
        return f"[COMMAND:{self.name}] executed with prompt='{prompt}'"

class Tool:
    """Represents an executable tool (Python, Bash, etc.)"""
    def __init__(self, name: str):
        self.name = name
    
    def execute(self, prompt: str) -> str:
        return f"[TOOL:{self.name}] executed with prompt='{prompt}'"
```

### Difference

- **Commands** → Actions/verbs (`search`, `analyze`, `filter`)
- **Tools** → Execution environments (`python`, `bash`)

---

### 2. ExecutionRegistry

**Purpose**: Central storage for all available commands and tools.

```python
class ExecutionRegistry:
    def __init__(self):
        self._commands = {}
        self._tools = {}
    
    def register_command(self, name: str):
        self._commands[name] = Command(name)
    
    def register_tool(self, name: str):
        self._tools[name] = Tool(name)
    
    def command(self, name: str) -> Optional[Command]:
        return self._commands.get(name)
    
    def tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)
```

**Analogy**: Think of it as a directory where executable components can be looked up.

---

### 3. QueryEnginePort

**Purpose**: Simulates a real query engine and aggregates processing results.

```python
class QueryEnginePort:
    @classmethod
    def from_workspace(cls):
        return cls()
    
    def submit_message(
        self,
        prompt,
        matched_commands,
        matched_tools,
        denied_tools
    ) -> TurnResult:
        
        return TurnResult(
            matched_commands=matched_commands,
            matched_tools=matched_tools,
            permission_denials=denied_tools,
            stop_reason="completed"
        )
```

---

### 4. PortRouter

**Purpose**: Routes prompts to relevant matches.

### How routing works

#### Step 1: Tokenization

```python
def _tokenize(self, prompt: str) -> set[str]:
    # "Search how data processing using python?"
    # ↓
    # {"search", "how", "data", "processing", "using", "python"}
```

#### Step 2: Scoring

```python
def _score(self, tokens, module: PortingModule) -> int:
    # For module "python":
    #
    # Combined text:
    # "python execution environment run python code"
    #
    # Matches:
    # "python" ✓
    #
    # Return: 1
```

#### Step 3: Collection & Sorting

```python
def route(self, prompt: str, limit: int = 5) -> List[RoutedMatch]:
    tokens = self._tokenize(prompt)
    
    matches = (
        self._collect(tokens, PORTED_COMMANDS, "command") +
        self._collect(tokens, PORTED_TOOLS, "tool")
    )
    
    matches.sort(
        key=lambda m: (-m.score, m.kind, m.name)
    )
    
    return matches[:limit]
```

---

### 5. ExecutionEngine

**Purpose**: Executes all matched components.

```python
class ExecutionEngine:
    def __init__(self, registry):
        self.registry = registry
    
    def execute(self, prompt, matches):
        command_execs = []
        tool_execs = []
        denials = []
        
        for m in matches:
            
            if m.kind == "command":
                cmd = self.registry.command(m.name)
                if cmd:
                    command_execs.append(
                        cmd.execute(prompt)
                    )
            
            elif m.kind == "tool":
                
                if "bash" in m.name.lower():
                    denials.append(m.name)
                    continue
                
                tool = self.registry.tool(m.name)
                if tool:
                    tool_execs.append(
                        tool.execute(prompt)
                    )
        
        return (
            command_execs,
            tool_execs,
            denials
        )
```

### Functionality

- Executes commands → collects output
- Executes tools → collects output
- Denies restricted tools (e.g. Bash)

---

### 6. CleanRuntime

**Purpose**: Main orchestrator that coordinates everything.

```python
class CleanRuntime:
    def __init__(self):
        self.router = PortRouter()
        self.engine = QueryEnginePort.from_workspace()
        self.registry = build_execution_registry()
        self.executor = ExecutionEngine(
            self.registry
        )
    
    def run(
        self,
        prompt: str,
        limit: int = 5
    ) -> RuntimeSession:
        
        # STEP 1: Route
        matches = self.router.route(
            prompt,
            limit
        )
        
        # STEP 2: Execute
        command_execs, tool_execs, denials = (
            self.executor.execute(
                prompt,
                matches
            )
        )
        
        # STEP 3: Compile
        result = self.engine.submit_message(
            prompt,
            matched_commands=tuple(
                m.name for m in matches
                if m.kind == "command"
            ),
            matched_tools=tuple(
                m.name for m in matches
                if m.kind == "tool"
            ),
            denied_tools=denials
        )
        
        # STEP 4: Return
        return RuntimeSession(
            prompt=prompt,
            routed_matches=matches,
            turn_result=result,
            command_execution_messages=command_execs,
            tool_execution_messages=tool_execs,
        )
```

**This is the main entry point.**

---

## Workflows & Flows

### Complete Request Flow

```
1. User input:
   "Search how data processing using python?"
   ↓

2. CleanRuntime.run()
   ↓

3. PortRouter.route()
   ↓

4. ExecutionEngine.execute()
   ↓

5. QueryEnginePort.submit_message()
   ↓

6. RuntimeSession created
   ↓

7. Returned to user
```

---

### Permission Check Flow

```
ExecutionEngine.execute()

For "bash":

Is "bash" in name.lower()? → YES
↓
Add to denials
↓
Skip execution


For "python":

Is "bash" in name.lower()? → NO
↓
Execute tool
↓
Collect output
```

---

## Example Usage

### Basic Example

```python
from query_runtime import CleanRuntime

runtime = CleanRuntime()

session = runtime.run(
    "Search how data processing using python?"
)
```

---

### Prompt containing Bash

```python
session = runtime.run(
    "Execute bash commands and search data"
)

print(
    session.turn_result.permission_denials
)

# Output:
# ('bash',)
```

---

### Custom Registry

```python
registry = ExecutionRegistry()

registry.register_command(
    "my_command"
)

registry.register_tool(
    "my_tool"
)

executor = ExecutionEngine(
    registry
)
```

---

## Configuration & Customization

### Available Commands & Tools

```python
PORTED_COMMANDS = (
    PortingModule(
        "search",
        "query engine",
        "search data"
    ),
    
    PortingModule(
        "analyze",
        "data processing",
        "analyze results"
    ),
)
```

```python
PORTED_TOOLS = (
    PortingModule(
        "python",
        "execution environment",
        "run python code"
    ),
    
    PortingModule(
        "bash",
        "shell access",
        "execute shell commands"
    ),
)
```

---

### Adjusting Permission Rules

```python
if "bash" in m.name.lower():
    denials.append(
        m.name
    )
    continue
```

---

### Adjusting Scoring Logic

```python
def _score(
    self,
    tokens,
    module
):
    
    text = (
        f"{module.name} "
        f"{module.source_hint}"
    )
    
    return sum(
        1 for t in tokens
        if t in text
    )
```

---

### Adjusting Routing Limit

```python
session = runtime.run(
    prompt,
    limit=10
)
```

---

## FAQ & Troubleshooting

### Q: Why are my tools or commands not being routed?

**A:** Check:

1. Is it included in `PORTED_TOOLS` or `PORTED_COMMANDS`?
2. Do the prompt tokens match `name`, `source_hint`, or `responsibility`?
3. Is the routing limit high enough?

---

### Q: How do I add my own tool?

**A:**

```python
PORTED_TOOLS = (
    PortingModule(
        "my_tool",
        "my_source",
        "what it does"
    ),
)
```

Then register it:

```python
reg.register_tool(
    "my_tool"
)
```

---

### Q: How do I modify permission rules?

**A:**

```python
if (
    "bash" in m.name.lower()
    or "dangerous_tool" in m.name
):
    denials.append(
        m.name
    )
    continue
```

---

## Summary

| Component | Role |
|-----------|------|
| **PortRouter** | Analyzes input and finds relevant matches |
| **ExecutionEngine** | Executes matches and enforces permissions |
| **ExecutionRegistry** | Stores all commands and tools |
| **QueryEnginePort** | Aggregates results into `TurnResult` |
| **CleanRuntime** | Binds everything together |

### Flow

`Input → Router → Executor → QueryEngine → Output`

---

**Version**: 1.0  
**Date**: April 2026  
**Language**: English  
**Author**: Ahmad Al Dibo
