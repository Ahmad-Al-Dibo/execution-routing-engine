# Query Runtime Documentatie 📚

Dit document beschrijft het `query_runtime.py` systeem - een query-routering en execution engine die gebruiker-prompts analyzeert en deze naar relevante commands en tools routeert.

---

## 📋 Inhoudsopgave

1. [Systeem Overzicht](#systeem-overzicht)
2. [Architectuur](#architectuur)
3. [Models & Data Structures](#models--data-structures)
4. [Components in Detail](#components-in-detail)
5. [Workflows & Flows](#workflows--flows)
6. [Voorbeeld Gebruik](#voorbeeld-gebruik)
7. [Configuratie & Customisatie](#configuratie--customisatie)

---

## Systeem Overzicht

### Wat doet dit systeem?

Het `query_runtime.py` systeem analyzeert een **user prompt** (bijv. "Search how data processing using python?") en:

1. **Routeert** de prompt naar relevante **commands** en **tools**
2. **Voert** die commands/tools uit in volgorde van relevantie
3. **Verzamelt** alle resultaten en execution messages
4. **Retourneert** een volledige `RuntimeSession` met alle bevindingen

### Kernidee

In plaats van dat elke user request alles direct moet uitvoeren, het systeem:
- Analyzeert wat de user wil
- Bepaalt welke functionaliteit nodig is
- Voert alleen de relevante onderdelen uit
- Retourneert gestructureerde resultaten

---

## Architectuur

### Grote lijnen

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INPUT (PROMPT)                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. ROUTING                                                   │
│     ┌─────────────────────────────────────────────┐          │
│     │  PortRouter analyzeert prompt                │          │
│     │  - Tokenize input                           │          │
│     │  - Match tegen PORTED_COMMANDS & TOOLS      │          │
│     │  - Score & sort op relevantie               │          │
│     └─────────────────────────────────────────────┘          │
│                          ↓                                    │
│  2. EXECUTION                                                 │
│     ┌─────────────────────────────────────────────┐          │
│     │  ExecutionEngine voert matches uit          │          │
│     │  - Zoekt commands in ExecutionRegistry      │          │
│     │  - Zoekt tools in ExecutionRegistry         │          │
│     │  - Checks permissions                       │          │
│     │  - Verzamelt output messages                │          │
│     └─────────────────────────────────────────────┘          │
│                          ↓                                    │
│  3. RESULT COMPILATION                                        │
│     ┌─────────────────────────────────────────────┐          │
│     │  QueryEngine verzamelt alles                │          │
│     │  CleanRuntime past alles in RuntimeSession  │          │
│     └─────────────────────────────────────────────┘          │
│                          ↓                                    │
├─────────────────────────────────────────────────────────────┤
│                  OUTPUT: RuntimeSession                       │
│  - matched_commands, matched_tools, permission_denials       │
│  - execution_messages, routed_matches                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Models & Data Structures

### 1. RoutedMatch
**Doel**: Representeert een gevonden match (command of tool) na routering

```python
@dataclass
class RoutedMatch:
    kind: str           # "command" of "tool"
    name: str           # Naam: "search", "python", etc.
    source_hint: str    # Waar het vandaan komt
    score: int          # Relevantie score (hoger = relevanter)
```

**Voorbeeld**:
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
**Doel**: Beschrijft een beschikbare command of tool in het systeem

```python
@dataclass
class PortingModule:
    name: str           # Naam van module
    source_hint: str    # Bron/component waar het in zit
    responsibility: str # Wat het doet/verantwoordelijkheid
```

**Beispiel**:
```python
PortingModule(
    name="python",
    source_hint="execution environment",
    responsibility="run python code"
)
```

---

### 3. TurnResult
**Doel**: Bevat het resultaat van één request-verwerking

```python
@dataclass
class TurnResult:
    matched_commands: Tuple[str, ...]     # Commands die gerouteerd zijn
    matched_tools: Tuple[str, ...]        # Tools die gerouteerd zijn
    permission_denials: Tuple[str, ...]   # Tools die geweigerd zijn
    stop_reason: str                      # Waarom gestopt ("completed")
```

---

### 4. RuntimeSession
**Doel**: Volledige sessieinformatie - het eindresultaat

```python
@dataclass
class RuntimeSession:
    prompt: str                          # De originele input
    routed_matches: List[RoutedMatch]   # Alle gevonden matches (gesorteerd)
    turn_result: TurnResult             # Verwerkingsresultaat
    command_execution_messages: Tuple[str, ...] # Output van commands
    tool_execution_messages: Tuple[str, ...]    # Output van tools
```

**Dit is wat gets retourneerd aan de user!**

---

## Components in Detail

### 1. Command & Tool Classes

**Command** en **Tool** zijn zeer gelijk gelijk - beide zijn executeerbare items:

```python
class Command:
    """Representeert een executeerbaar commando"""
    def __init__(self, name: str):
        self.name = name
    
    def execute(self, prompt: str) -> str:
        # Voert uit en retourneert message
        return f"[COMMAND:{self.name}] executed with prompt='{prompt}'"

class Tool:
    """Representeert een executeerbaar tool (Python, Bash, etc.)"""
    def __init__(self, name: str):
        self.name = name
    
    def execute(self, prompt: str) -> str:
        return f"[TOOL:{self.name}] executed with prompt='{prompt}'"
```

**Verschil**:
- **Commands**: Zijn acties/verbs (search, analyze, filter)
- **Tools**: Zijn execution platforms (python interpreter, bash shell)

---

### 2. ExecutionRegistry

**Doel**: Central storage voor alle beschikbare commands en tools

```python
class ExecutionRegistry:
    def __init__(self):
        self._commands = {}  # Dict met Command objects
        self._tools = {}     # Dict met Tool objects
    
    def register_command(self, name: str):
        # Voegt command toe
        self._commands[name] = Command(name)
    
    def register_tool(self, name: str):
        # Voegt tool toe
        self._tools[name] = Tool(name)
    
    def command(self, name: str) -> Optional[Command]:
        # Zoekt command
        return self._commands.get(name)
    
    def tool(self, name: str) -> Optional[Tool]:
        # Zoekt tool
        return self._tools.get(name)
```

**Analogi**: Dit is zoals een telefonisch gids waar je nummers kan opzoeken.

---

### 3. QueryEnginePort

**Doel**: Simuleert een echte query engine - verzamelt informatie

```python
class QueryEnginePort:
    @classmethod
    def from_workspace(cls):
        # Factory method
        return cls()
    
    def submit_message(self, prompt, matched_commands, 
                      matched_tools, denied_tools) -> TurnResult:
        # Maakt TurnResult aan met alle info
        return TurnResult(
            matched_commands=matched_commands,
            matched_tools=matched_tools,
            permission_denials=denied_tools,
            stop_reason="completed"
        )
```

---

### 4. PortRouter

**Doel**: Routeert prompts naar relevante matches

#### Hoe werkt de routing?

**Stap 1: Tokenize**
```python
def _tokenize(self, prompt: str) -> set[str]:
    # "Search how data processing using python?"
    # ↓
    # {"search", "how", "data", "processing", "using", "python"}
```

**Stap 2: Score**
```python
def _score(self, tokens, module: PortingModule) -> int:
    # Voor module "python" met:
    #   name="python"
    #   source="execution environment"
    #   responsibility="run python code"
    # Combined text: "python execution environment run python code"
    #
    # Telt matches: "python" ✓, "processing" ✗
    # Return: 1
```

**Stap 3: Collect & Sort**
```python
def route(self, prompt: str, limit: int = 5) -> List[RoutedMatch]:
    tokens = self._tokenize(prompt)
    
    # Verzamel alle matches
    matches = (
        self._collect(tokens, PORTED_COMMANDS, "command") +
        self._collect(tokens, PORTED_TOOLS, "tool")
    )
    
    # Sorteer op relevantie (score aflopend)
    matches.sort(key=lambda m: (-m.score, m.kind, m.name))
    
    return matches[:limit]  # Return top N
```

---

### 5. ExecutionEngine

**Doel**: Voert all gevonden matches uit

```python
class ExecutionEngine:
    def __init__(self, registry: ExecutionRegistry):
        self.registry = registry
    
    def execute(self, prompt: str, 
                matches: List[RoutedMatch]) -> Tuple[...]:
        command_execs = []
        tool_execs = []
        denials = []
        
        for m in matches:
            if m.kind == "command":
                cmd = self.registry.command(m.name)
                if cmd:
                    command_execs.append(cmd.execute(prompt))
            
            elif m.kind == "tool":
                # Permission check: bash is geweigerd
                if "bash" in m.name.lower():
                    denials.append(m.name)
                    continue
                
                tool = self.registry.tool(m.name)
                if tool:
                    tool_execs.append(tool.execute(prompt))
        
        return (command_execs), (tool_execs), (denials)
```

**Functionaliteit**:
- Voert command uit → gets output
- Voert tool uit → gets output
- Weigert bepaalde tools (bijv. bash)

---

### 6. CleanRuntime

**Doel**: Hoofd-orchestrator die alles coördineert

```python
class CleanRuntime:
    def __init__(self):
        self.router = PortRouter()
        self.engine = QueryEnginePort.from_workspace()
        self.registry = build_execution_registry()
        self.executor = ExecutionEngine(self.registry)
    
    def run(self, prompt: str, limit: int = 5) -> RuntimeSession:
        # STAP 1: Route
        matches = self.router.route(prompt, limit)
        
        # STAP 2: Execute
        command_execs, tool_execs, denials = \
            self.executor.execute(prompt, matches)
        
        # STAP 3: Compile results
        result = self.engine.submit_message(
            prompt,
            matched_commands=tuple(m.name for m in matches 
                                   if m.kind == "command"),
            matched_tools=tuple(m.name for m in matches 
                               if m.kind == "tool"),
            denied_tools=denials
        )
        
        # STAP 4: Return
        return RuntimeSession(
            prompt=prompt,
            routed_matches=matches,
            turn_result=result,
            command_execution_messages=command_execs,
            tool_execution_messages=tool_execs,
        )
```

**Dit is de main entry point!**

---

## Workflows & Flows

### Complete Request Flow

```
1. User input: "Search how data processing using python?"
   ↓
2. CleanRuntime.run() called
   ↓
3. PortRouter.route()
   └─ Tokenize: {"search", "how", "data", "processing", "using", "python"}
   └─ Score each module:
      - search command: 1 match ("search")
      - analyze command: 0 matches
      - python tool: 1 match ("python")
      - bash tool: 0 matches
   └─ Return top matches: [
      RoutedMatch(command, search, ..., 1),
      RoutedMatch(tool, python, ..., 1),
   ]
   ↓
4. ExecutionEngine.execute()
   └─ For each match:
      - Command "search": Execute → "[COMMAND:search] executed..."
      - Tool "python": Check perms ✓, Execute → "[TOOL:python] executed..."
   └─ Return:
      - command_execs: ("...",)
      - tool_execs: ("...",)
      - denials: ()
   ↓
5. QueryEnginePort.submit_message()
   └─ Create TurnResult with all info
   ↓
6. RuntimeSession created with:
   - prompt: "Search how..."
   - routed_matches: [...]
   - turn_result: TurnResult(...)
   - command_execution_messages: ("...",)
   - tool_execution_messages: ("...",)
   ↓
7. Return to user
```

### Permission Check Flow

```
ExecutionEngine.execute() checks:

For "bash" tool:
┌─────────────────────────────────┐
│ Is "bash" in name.lower()? YES  │
├─────────────────────────────────┤
│ → Add to denials                │
│ → Continue to next match        │
│ → Skip tool execution           │
└─────────────────────────────────┘

For "python" tool:
┌─────────────────────────────────┐
│ Is "bash" in name.lower()? NO   │
├─────────────────────────────────┤
│ → Check passed                  │
│ → Execute tool                  │
│ → Add output to tool_execs      │
└─────────────────────────────────┘
```

---

## Voorbeeld Gebruik

### Basisch Voorbeeld

```python
from query_runtime import CleanRuntime

# Initialize
runtime = CleanRuntime()

# Run met prompt
session = runtime.run("Search how data processing using python?")

# Resultaten gebruiken
print("Gevonden matches:")
for match in session.routed_matches:
    print(f"- {match.kind}: {match.name} (score: {match.score})")
    # Output:
    # - command: search (score: 1)
    # - tool: python (score: 1)

print("\nCommand outputs:")
for msg in session.command_execution_messages:
    print(f"  {msg}")
    # Output:
    # [COMMAND:search] executed with prompt='Search how...'

print("\nTool outputs:")
for msg in session.tool_execution_messages:
    print(f"  {msg}")
    # Output:
    # [TOOL:python] executed with prompt='Search how...'

print("\nDenied tools:")
for denied in session.turn_result.permission_denials:
    print(f"  {denied}")
    # Output: (empty in this case)
```

### Prompt met bash (geweigerd)

```python
session = runtime.run("Execute bash commands and search data")

# bash wordt gerouted maar geweigerd:
print(session.turn_result.permission_denials)
# Output: ('bash',)

# python zou ook gerouted kunnen worden maar hier niet (geen "python" in prompt)
```

### Custom Registry

```python
# Eigen registry maken
from query_runtime import ExecutionRegistry, ExecutionEngine, CleanRuntime

registry = ExecutionRegistry()
registry.register_command("my_command")
registry.register_tool("my_tool")

executor = ExecutionEngine(registry)
# Gebruik met custom registry
```

---

## Configuratie & Customisatie

### Beschikbare Commands & Tools ändern

In `query_runtime.py`:

```python
PORTED_COMMANDS = (
    PortingModule("search", "query engine", "search data"),
    PortingModule("analyze", "data processing", "analyze results"),
    # Voeg hier eigen commands toe:
    # PortingModule("export", "data output", "export query results"),
)

PORTED_TOOLS = (
    PortingModule("python", "execution environment", "run python code"),
    PortingModule("bash", "shell access", "execute shell commands"),
    # Voeg hier eigen tools toe:
    # PortingModule("sql", "database", "execute sql queries"),
)
```

### Permission Rules aanpassen

In `ExecutionEngine.execute()`:

```python
# Huiding regel: bash is geweigerd
if "bash" in m.name.lower():
    denials.append(m.name)
    continue

# Aanpassen:
# - Voeg meer geweigerde tools toe
# - Maakt afhankelijk van user level
# - etc.
```

### Scoring Logic aanpassen

In `PortRouter._score()`:

```python
def _score(self, tokens, module: PortingModule) -> int:
    # Huidge logica: telt matches
    text = f"{module.name} {module.source_hint}..."
    return sum(1 for t in tokens if t in text)
    
    # Mogelijke aanpassingen:
    # - Gewichten verschillende onderdelen anders
    # - Gebruik fuzzy matching
    # - Voeg synoniemen toe
```

### Routing Limit aanpassen

```python
session = runtime.run(prompt, limit=10)  # Standaard 5, nu 10
```

---

## FAQ & Troubleshooting

### V: Waarom worden mijn tools/commands niet gerouteerd?

**A**: Controleer:
1. Is de naam in `PORTED_TOOLS` of `PORTED_COMMANDS`?
2. Matchen de tokens van je prompt met name/source_hint/responsibility?
3. Is de limit hoog genoeg?

### V: Hoe voeg ik mijn eigen tool toe?

**A**:
```python
# 1. Add to PORTED_TOOLS
PORTED_TOOLS = (
    # ... existing ...
    PortingModule("my_tool", "my_source", "what it does"),
)

# 2. Register in build_execution_registry()
def build_execution_registry():
    reg = ExecutionRegistry()
    # ... existing ...
    reg.register_tool("my_tool")
    return reg

# 3. Optionally handle permissions in ExecutionEngine.execute()
if "my_tool" in m.name.lower():
    # custom logic
    pass
```

### V: Hoe wijzig ik permission rules?

**A**: In `ExecutionEngine.execute()`, modify de check:

```python
# Voeg meer rules toe:
if "bash" in m.name.lower() or "dangerous_tool" in m.name:
    denials.append(m.name)
    continue
```

---

## Samenvatting

| Component | Rol |
|-----------|-----|
| **PortRouter** | Analyzeert input, vindt relevante matches |
| **ExecutionEngine** | Voert matches uit, enforces permissions |
| **ExecutionRegistry** | Slaat alle commands/tools op |
| **QueryEnginePort** | Verzamelt results in TurnResult |
| **CleanRuntime** | Bindt alles samen, main entry point |

**Flow**: `Input → Router → Executor → QueryEngine → Output`

---

**Versie**: 1.0  
**Datum**: April 2026  
**Taal**: Nederlands  
**Status**: Complete documentatie
**Auther**: Ahmad Al Dibo
