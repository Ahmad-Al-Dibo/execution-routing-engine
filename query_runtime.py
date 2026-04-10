from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional


# =========================
# Models (Gegevensstructuren)
# =========================

@dataclass
class RoutedMatch:
    """
    Model die een gevonden match representeert na routering.
    
    Wat: Bevat informatie over een commando of tool die is gevonden als relevant voor een prompt.
    Hoe: Wordt gebruikt door de router om matched items op te slaan met hun relevantie score.
    
    Attributen:
        kind: Het type match - ofwel 'command' (een commando) ofwel 'tool' (een gereedschap)
        name: De naam van het commando of tool (bijv. 'search', 'python')
        source_hint: Een hint over waar dit uit afkomt (bijv. 'query engine')
        score: Een numerieke score die aangeeft hoe relevant deze match is (hoger = relevanter)
    """
    kind: str  # 'command' | 'tool'
    name: str
    source_hint: str
    score: int


@dataclass
class PortingModule:
    """
    Model dat een beschikbare module of functie beschrijft die kan worden gerouteerd.
    
    Wat: Beschrijft een commando of tool die beschikbaar is in het systeem.
    Hoe: Wordt gebruikt in een registry om alle mogelijke matching targets op te slaan.
    
    Attributen:
        name: De naam van de module (bijv. 'search', 'python', 'bash')
        source_hint: Waar deze vandaan komt (bijv. 'query engine', 'execution environment')
        responsibility: Wat deze module doet (bijv. 'search data', 'run python code')
    """
    name: str
    source_hint: str
    responsibility: str


@dataclass
class TurnResult:
    """
    Model dat het resultaat van één beurt/interactie aangeeft.
    
    Wat: Bevat alle bevindingen en acties die plaatsvonden tijdens één query-ronde.
    Hoe: Wordt retourneerd door QueryEngine na verwerking van een prompt.
    
    Attributen:
        matched_commands: Tuple met namen van commands die zijn geactiveerd
        matched_tools: Tuple met namen van tools die zijn geactiveerd
        permission_denials: Tuple met namen van tools die zijn geweigerd vanwege permissies
        stop_reason: Waarom de verwerking is gestopt ('completed', 'error', etc.)
    """
    matched_commands: Tuple[str, ...]
    matched_tools: Tuple[str, ...]
    permission_denials: Tuple[str, ...]
    stop_reason: str = "completed"


@dataclass
class RuntimeSession:
    """
    Model dat een volledige runtime-sessie of -beurt beschrijft.
    
    Wat: Bevat alle informatie over wat er gebeurde toen een prompt werd verwerkt.
    Hoe: Dit is het eindresultaat dat terug wordt gegeven aan de gebruiker/aanroeper.
    
    Attributen:
        prompt: De originele input-prompt van de gebruiker
        routed_matches: Lijst van alle gevonden matches (RoutedMatch objecten) gesorteerd op relevantie
        turn_result: Het TurnResult object met informatie over ondernomen acties
        command_execution_messages: De output berichten van uitgevoerde commands
        tool_execution_messages: De output berichten van uitgevoerde tools
    """
    prompt: str
    routed_matches: List[RoutedMatch]
    turn_result: TurnResult
    command_execution_messages: Tuple[str, ...]
    tool_execution_messages: Tuple[str, ...]


# =========================
# Dummy Registry (simuleren van echt systeem)
# =========================

class Command:
    """
    Representeert een commando dat kan worden uitgevoerd.
    
    Wat: Een wrapper rond een naambaar commando met execute-functionaliteit.
    Hoe: Wordt gebruikt door ExecutionEngine om commands uit te voeren.
    
    Methoden:
        __init__: Initialiseert een commando met naam
        execute: Voert het commando uit met gegeven prompt en retourneert het resultaat
    """
    def __init__(self, name: str):
        self.name = name

    def execute(self, prompt: str) -> str:
        """
        Voert het commando uit.
        
        Args:
            prompt: De input string die aan het commando wordt gegeven
            
        Returns:
            Een resultaat-string die aangeeft wat het commando deed
        """
        return f"[COMMAND:{self.name}] executed with prompt='{prompt}'"


class Tool:
    """
    Representeert een tool/gereedschap dat kan worden uitgevoerd.
    
    Wat: Een wrapper rond een naambaar tool met execute-functionaliteit.
    Hoe: Wordt gebruikt door ExecutionEngine om tools uit te voeren (bijv. Python, Bash).
    
    Methoden:
        __init__: Initialiseert een tool met naam
        execute: Voert de tool uit met gegeven prompt en retourneert het resultaat
    """
    def __init__(self, name: str):
        self.name = name

    def execute(self, prompt: str) -> str:
        """
        Voert de tool uit.
        
        Args:
            prompt: De input string die aan de tool wordt gegeven
            
        Returns:
            Een resultaat-string die aangeeft wat de tool deed
        """
        return f"[TOOL:{self.name}] executed with prompt='{prompt}'"


class ExecutionRegistry:
    """
    Central registry/opslagplek voor alle beschikbare commands en tools.
    
    Wat: Beheert een verzameling van alle commands en tools die kunnen worden uitgevoerd.
    Hoe: Wordt gebruikt door ExecutionEngine om commands/tools op te zoeken en uit te voeren.
          Functions kunnen commands/tools registreren en later ophalen.
    
    Methoden:
        __init__: Initialiseert lege storage voor commands en tools
        register_command: Voegt een nieuw command toe aan de registry
        register_tool: Voegt een nieuw tool toe aan de registry
        command: Zoekt en retourneert een command op naam (of None als niet gevonden)
        tool: Zoekt en retourneert een tool op naam (of None als niet gevonden)
    """
    def __init__(self):
        """Initialiseert lege storage dictionaries."""
        self._commands = {}  # Dictionary met alle geregistreerde commands: {naam: Command object}
        self._tools = {}     # Dictionary met alle geregistreerde tools: {naam: Tool object}

    def register_command(self, name: str):
        """
        Registreert een nieuw command in de registry.
        
        Args:
            name: De naam van het command (bijv. 'search', 'analyze')
        """
        self._commands[name] = Command(name)

    def register_tool(self, name: str):
        """
        Registreert een nieuw tool in de registry.
        
        Args:
            name: De naam van de tool (bijv. 'python', 'bash')
        """
        self._tools[name] = Tool(name)

    def command(self, name: str) -> Optional[Command]:
        """
        Zoekt een command op naam.
        
        Args:
            name: De naam van het command
            
        Returns:
            Het Command object als gevonden, anders None
        """
        return self._commands.get(name)

    def tool(self, name: str) -> Optional[Tool]:
        """
        Zoekt een tool op naam.
        
        Args:
            name: De naam van de tool
            
        Returns:
            Het Tool object als gevonden, anders None
        """
        return self._tools.get(name)


def build_execution_registry() -> ExecutionRegistry:
    """
    Fabrieksfunctie die een voorkonfigureerde ExecutionRegistry aanmaakt.
    
    Wat: Maakt een registry aan en registreert allemaal voorgedefinieerde commands en tools.
    Hoe: Wordt aangeroepen door CleanRuntime om het systeem op te zetten.
    
    Returns:
        Een ExecutionRegistry object met voorgedefinieerde commands en tools
    """
    reg = ExecutionRegistry()

    # Voorbeeldcommands registreren
    reg.register_command("search")   # Command voor zoekopdrachten
    reg.register_command("analyze")  # Command voor data-analyse

    # Voorbeeldtools registreren
    reg.register_tool("python")      # Tool voor Python code-uitvoering
    reg.register_tool("bash")        # Tool voor shell/bash commands

    return reg


# =========================
# Query Engine (mock/simulatie)
# =========================

class QueryEnginePort:
    """
    Simulatie van een echte Query Engine die berichten verwerkt.
    
    Wat: Accepteert berichten (prompts) met information over matched commands/tools
         en retourneert een TurnResult met de verwerkingsresultaten.
    Hoe: Wordt gebruikt door CleanRuntime om het eindresultaat saam te stellen.
    
    Methoden:
        from_workspace: Factory method dat een QueryEnginePort aanmaakt
        submit_message: Verwerkt een bericht en retourneert het resultaat
    """
    @classmethod
    def from_workspace(cls):
        """
        Factory method om een QueryEnginePort instance aan te maken.
        
        Returns:
            Een nieuwe QueryEnginePort instance
        """
        return cls()

    def submit_message(
        self,
        prompt: str,
        matched_commands: Tuple[str, ...],
        matched_tools: Tuple[str, ...],
        denied_tools: Tuple[str, ...],
    ) -> TurnResult:
        """
        Verwerkt een bericht met informatie over gevonden matches.
        
        Wat: Combineert alle informatie over matches en perms in een TurnResult.
        Hoe: Dit is het eindstation voordat resultaten terug naar user gaan.
        
        Args:
            prompt: De originele user input
            matched_commands: Tuple van commando-namen die zijn gevonden
            matched_tools: Tuple van tool-namen die zijn gevonden
            denied_tools: Tuple van tool-namen waarvoor toestemming is geweigerd
            
        Returns:
            Een TurnResult object met alle verwerkingsresultaten
        """
        return TurnResult(
            matched_commands=matched_commands,
            matched_tools=matched_tools,
            permission_denials=denied_tools,
            stop_reason="completed"
        )


# =========================
# Router (Routeerder)
# =========================

class PortRouter:
    """
    Routeert user prompts naar relevante commands en tools.
    
    Wat: Analyzeert een prompt en zoekt welke commands/tools eraan relevant zijn.
    Hoe: Splitst de input in tokens, zoekt matches, en sorteert op relevantie score.
    
    Methoden:
        route: Hoofd-method die prompt analyzeert en matches retourneert
        _tokenize: Splits prompt in losse woorden (tokens)
        _collect: Verzamelt matches voor een bepaald type
        _score: Berekent relevantie-score voor een module
    """
    def route(self, prompt: str, limit: int = 5) -> List[RoutedMatch]:
        """
        Routeert een prompt naar relevante commands en tools.
        
        Wat: Analyzeert de input en zoekt alle relevante matches.
        Hoe: 1. Tokenize prompt in woorden
             2. Zoek matches in commands en tools
             3. Sorteer op relevantie score
             4. Retourneer top N matches (standaard 5)
        
        Args:
            prompt: De user input/vraag om te routeren
            limit: Maximaal aantal matches om terug te geven (default 5)
            
        Returns:
            Gesorteerde lijst van RoutedMatch objecten (meest relevant eerst)
        """
        tokens = self._tokenize(prompt)

        # Verzamel matches van commands en tools
        matches = (
            self._collect(tokens, PORTED_COMMANDS, "command") +
            self._collect(tokens, PORTED_TOOLS, "tool")
        )

        # Sorteer: eerst op score (aflopend), daarna op type en naam
        matches.sort(key=lambda m: (-m.score, m.kind, m.name))
        return matches[:limit]  # Retourneer alleen top N

    def _tokenize(self, prompt: str) -> set[str]:
        """
        Splits de prompt in afzonderlijke woorden (tokens).
        
        Wat: Converteert input string naar set van relevante tokens.
        Hoe: Verwijdert speciale tekens (/, -) en splittst op spaties.
             Alles wordt lowercase voor case-insensitive matching.
        
        Args:
            prompt: De input string
            
        Returns:
            Set van lowercase woorden (tokens)
        """
        return {
            t.lower()
            for t in prompt.replace("/", " ").replace("-", " ").split()
            if t  # Negeer lege strings
        }

    def _collect(self, tokens, modules, kind):
        """
        Verzamelt matches voor een bepaald type (commands of tools).
        
        Wat: Gaat door alle modules en zoekt matches met gegeven tokens.
        Hoe: Voor elke module wordt een score berekend.
             Modules met score > 0 worden als match toegevoegd.
        
        Args:
            tokens: Set van woorden om op te zoeken
            modules: Lijst van PortingModule objekten om te controleren
            kind: Type match ('command' of 'tool')
            
        Returns:
            Lijst van RoutedMatch objecten voor dit type
        """
        results = []
        for m in modules:
            score = self._score(tokens, m)
            if score > 0:  # Alleen opnemen als er minstens 1 overeenkomst is
                results.append(RoutedMatch(kind, m.name, m.source_hint, score))
        return results

    def _score(self, tokens, module: PortingModule) -> int:
        """
        Berekent de relevantie score van een module voor gegeven tokens.
        
        Wat: Meet hoe goed een module past bij de gegeven tokens.
        Hoe: Telt hoeveel tokens voorkomen in module info (naam, source, responsibility).
             Meer matches = hogere score = meer relevant.
        
        Args:
            tokens: Set van woorden om op te zoeken
            module: PortingModule om te scoren
            
        Returns:
            Integer score (0 = geen matches, hoger = meer matches)
        """
        # Combineer alle beschrijvende tekst van module
        text = f"{module.name} {module.source_hint} {module.responsibility}".lower()
        # Tel hoeveel tokens in deze tekst voorkomen
        return sum(1 for t in tokens if t in text)


# =========================
# Executor (Uitvoeringsmotor)
# =========================

class ExecutionEngine:
    """
    Voert gevonden matches (commands en tools) uit.
    
    Wat: Neemt de gerouteerde matches en voert die feitelijk uit.
    Hoe: Zoekt commands/tools in registry, voert ze uit, enforces permissions.
    
    Methoden:
        __init__: Initialiseert met een ExecutionRegistry
        execute: Voert alle matches uit en retourneert resultaten
    """
    def __init__(self, registry: ExecutionRegistry):
        """
        Initialiseert de ExecutionEngine.
        
        Args:
            registry: ExecutionRegistry object met alle beschikbare commands/tools
        """
        self.registry = registry

    def execute(
        self,
        prompt: str,
        matches: List[RoutedMatch]
    ) -> Tuple[Tuple[str, ...], Tuple[str, ...], Tuple[str, ...]]:
        """
        Voert alle gegeven matches uit (commands en tools).
        
        Wat: Gaat door alle matches en voert die uit met permission checks.
        Hoe: 1. Voor commands: zoek in registry en voer uit
             2. Voor tools: check permissions, zoek in registry, voer uit
             3. Geweigerde tools (geen toestemming) gaan in denials lijst
        
        Args:
            prompt: De originele user input
            matches: Lijst van RoutedMatch objekten die uitgevoerd moeten worden
            
        Returns:
            Tuple van (command_results, tool_results, denied_tools)
            - command_results: Output berichten van uitgevoerde commands
            - tool_results: Output berichten van uitgevoerde tools
            - denied_tools: Namen van tools die werden geweigerd
        """
        command_execs = []  # Storage voor command outputs
        tool_execs = []     # Storage voor tool outputs
        denials = []        # Storage voor geweigerde tools

        for m in matches:
            if m.kind == "command":
                # Zoek het command in registry en voer uit
                cmd = self.registry.command(m.name)
                if cmd:
                    command_execs.append(cmd.execute(prompt))

            elif m.kind == "tool":
                # Simpele permission check: bash tools zijn geweigerd
                if "bash" in m.name.lower():
                    denials.append(m.name)
                    continue  # Skip dit tool (niet uitvoeren)

                # Zoek de tool in registry en voer uit
                tool = self.registry.tool(m.name)
                if tool:
                    tool_execs.append(tool.execute(prompt))

        # Retourneer alles als tuples
        return tuple(command_execs), tuple(tool_execs), tuple(denials)


# =========================
# Runtime (Schone runtime omgeving)
# =========================

class CleanRuntime:
    """
    Hoofd-orchestrator die de volledige query-verwerkingsketen coördineert.
    
    Wat: Bindt alles samen: routing, execution, query engine.
    Hoe: 1. Routeert prompt naar relevante matches
         2. Voert matches uit via ExecutionEngine
         3. Combineert alles in RuntimeSession via QueryEngine
         4. Retourneert volledige resultaat aan user
    
    Methoden:
        __init__: Initialiseert alle componenten (router, engine, registry, executor)
        run: Hoofd-method die een compleet request verwerkt
    """
    def __init__(self):
        """
        Initialiseert alle componenten van de runtime.
        
        Wat: Maakt alle onderdelen aan en verbindt die met elkaar.
        Hoe: 1. Maakt router aan (voor routing)
             2. Maakt QueryEngine aan (voor message processing)
             3. Bouwt registry met commands/tools
             4. Maakt executor aan met die registry
        """
        self.router = PortRouter()                          # Routeert prompts naar matches
        self.engine = QueryEnginePort.from_workspace()      # Verwerkt berichten
        self.registry = build_execution_registry()          # Bevat commands/tools
        self.executor = ExecutionEngine(self.registry)      # Voert matches uit

    def run(self, prompt: str, limit: int = 5) -> RuntimeSession:
        """
        Voert een compleet request uit van begin tot eind.
        
        Wat: Verwerkt een user prompt compleet: routing, execution, en resultaat-compilatie.
        Hoe: 1. Route prompt naar relevante commands/tools
             2. Voer de gevonden matches uit
             3. Verzamel resultaten via QueryEngine
             4. Compileer alles in RuntimeSession en return
        
        Args:
            prompt: De user input/vraag
            limit: Max aantal matches om te routeren (default 5)
            
        Returns:
            RuntimeSession object met compleet resultaat van processing
        """
        # STAP 1: Route de prompt naar relevante matches
        matches = self.router.route(prompt, limit)

        # STAP 2: Voer gevonden matches uit
        command_execs, tool_execs, denials = self.executor.execute(prompt, matches)

        # STAP 3: Verwerk via QueryEngine
        result = self.engine.submit_message(
            prompt,
            matched_commands=tuple(m.name for m in matches if m.kind == "command"),
            matched_tools=tuple(m.name for m in matches if m.kind == "tool"),
            denied_tools=denials
        )

        # STAP 4: Compileer alles in RuntimeSession en retourneer
        return RuntimeSession(
            prompt=prompt,
            routed_matches=matches,
            turn_result=result,
            command_execution_messages=command_execs,
            tool_execution_messages=tool_execs,
        )


# =========================
# Mock Data (modules) - Testgegevens
# =========================
# Deze secties definiëren welke commands en tools beschikbaar zijn in ons systeem.
# Deze data wordt gebruikt door PortRouter om matches te vinden.

PORTED_COMMANDS = (
    # Command voor zoekopdrachten: zoekt en filtert data
    PortingModule("search", "query engine", "search data"),
    # Command voor data-analyse: analyzeert en verwerkt resultaten
    PortingModule("analyze", "data processing", "analyze results"),
)

PORTED_TOOLS = (
    # Tool voor Python: voert Python-code uit in een interpreter
    PortingModule("python", "execution environment", "run python code"),
    # Tool voor Bash: voert shell/bash commands uit (wordt normaal geweigerd vanwege veiligheid)
    PortingModule("bash", "shell access", "execute shell commands"),
)


# =========================
# Example usage (Voorbeeldgebruik)
# =========================
# Dit demonstreert hoe de volledige runtime wordt gebruikt.

if __name__ == "__main__":
    # Stap 1: Maak een CleanRuntime instance aan (initialize alle componenten)
    runtime = CleanRuntime()

    # Stap 2: Run met een voorbeeld prompt
    # Deze vraag bevat woorden die matchen met 'search', 'python', 'data processing'
    session = runtime.run("Search how data procssing using python ?")

    # Stap 3: Print alle informatie uit resultaat
    print("\n--- ROUTED MATCHES ---")
    print("Welke commands/tools zijn gevonden als relevant:")
    for m in session.routed_matches:
        print(f"{m.kind}: {m.name} (relevantie-score={m.score})")

    print("\n--- COMMAND EXECUTION ---")
    print("Output van uitgevoerde commands:")
    for msg in session.command_execution_messages:
        print(msg)

    print("\n--- TOOL EXECUTION ---")
    print("Output van uitgevoerde tools:")
    for msg in session.tool_execution_messages:
        print(msg)

    print("\n--- TURN RESULT ---")
    print("Samenvatting van alles wat gebeurde:")
    print(session.turn_result)
