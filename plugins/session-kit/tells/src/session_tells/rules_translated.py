"""The tells of the translated trees: Spanish (``es-419``) and Portuguese (``pt-BR``).

A translation of a clean page can still read as English wearing another language's
words, or carry the stock phrases a model reaches for in that language. These rules
look for both. They are written in the language's own words, so each reads only the
trees of its language (``rules.Language``), and the English table reads neither. The
rule names end in the language's code. A rule that needs no words (the dash, the
emoji, a history code) is the English table's, marked for every language.

Each rule carries text it must find and a near miss it must leave alone, and the
tests run both, as for the English table.
"""

from __future__ import annotations

from session_tells.rules import Language, Rule, rx

SPANISH: frozenset[Language] = frozenset({"es"})
PORTUGUESE: frozenset[Language] = frozenset({"pt"})
BOTH: frozenset[Language] = SPANISH | PORTUGUESE

SPANISH_BANNED: tuple[Rule, ...] = (
    Rule(
        "signposting-es",
        "banned",
        rx(
            r"\b(?:cabe (?:destacar|mencionar|señalar|resaltar|notar)"
            r"|es (?:importante|fundamental|esencial|crucial) "
            r"(?:destacar|señalar|notar|mencionar|resaltar|recordar|tener en cuenta)"
            r"|vale la pena (?:destacar|mencionar|señalar|notar|resaltar)"
            r"|en resumen|en conclusi[oó]n|en pocas palabras|al fin y al cabo"
            r"|sin m[aá]s pre[aá]mbulos|como podemos ver)\b"
        ),
        "start with the fact",
        fires=(
            "Cabe destacar que el job se detiene.",
            "Es importante señalar el límite.",
            "En resumen, el límite se aplica.",
        ),
        misses=("El resumen del job.", "La conclusión del turno.", "Es importante el límite."),
        languages=SPANISH,
    ),
    Rule(
        "inflated-vocabulary-es",
        "banned",
        rx(
            r"\b(?:robust[oa]s?|sin fisuras|sin fricci[oó]n|hol[ií]stic[oa]s?"
            r"|potenci(?:ar|ando|an)\w*|sum[ée]rge(?:te|se)|sumergirse|de vanguardia"
            r"|de [uú]ltima generaci[oó]n|de clase mundial|innovador\w*|revolucion\w+"
            r"|transformador\w*|crucial(?:es)?)\b"
        ),
        "use the plain word",
        fires=(
            "una arquitectura robusta y sin fisuras",
            "Sumérgete en los jobs.",
            "una función crucial",
        ),
        misses=("El potencial del agente.", "La clave de API", "la potencia del modelo"),
        languages=SPANISH,
    ),
    Rule(
        "copula-avoidance-es",
        "banned",
        rx(
            r"\b(?:sirve como|juega un papel|desempeña (?:un|el) (?:papel|rol)"
            r"|representa (?:un|una))\b"
        ),
        "say *es*",
        fires=(
            "La tabla sirve como registro.",
            "Cada fila representa un job.",
            "juega un papel clave",
        ),
        misses=("Sirve la página.", "La fila representa el job 4711."),
        languages=SPANISH,
    ),
    Rule(
        "intensifier-es",
        "banned",
        rx(
            r"\b(?:verdaderamente|realmente|genuinamente|profundamente|incre[ií]blemente"
            r"|fundamentalmente|esencialmente|en [uú]ltima instancia|notablemente"
            r"|simplemente|sencillamente|b[aá]sicamente|literalmente)\b"
        ),
        "drop it",
        fires=("Esto es realmente importante.", "simplemente haz clic"),
        misses=("La realidad del job.", "El valor real"),
        languages=SPANISH,
    ),
    Rule(
        "hollow-closer-es",
        "banned",
        rx(
            r"\b(?:habla por s[ií] mism[oa]|ni m[aá]s ni menos|desde el primer d[ií]a"
            r"|desde el d[ií]a uno)\b"
        ),
        "stop at the last fact",
        fires=("Habla por sí mismo.", "desde el primer día"),
        misses=("el primer día hábil", "habla con el agente"),
        languages=SPANISH,
    ),
    Rule(
        "assistant-voice-es",
        "banned",
        rx(
            r"\b(?:espero que (?:esto |eso )?(?:te )?(?:ayude|sirva)|no dudes en|con gusto"
            r"|excelente pregunta|buena pregunta|por favor|claro que s[ií])\b"
        ),
        "delete it",
        fires=("Espero que esto te ayude.", "No dudes en preguntar.", "Por favor, espera."),
        misses=("Dudas sobre un job: ver la página 21.", "Con el límite activo"),
        languages=SPANISH,
    ),
    Rule(
        "register-es",
        "banned",
        rx(r"\b(?:usted(?:es)?|vosotros|vosotras|vuestr[oa]s?|vos|tenés|podés|querés|elegí)\b"),
        "the glossary sets the register: implied *tú*, no voseo, no *usted*",
        fires=("Usted puede elegir.", "Si querés, elegí.", "vuestro agente"),
        misses=("Tú puedes elegir.", "El uso del límite"),
        languages=SPANISH,
    ),
    Rule(
        "calque-es",
        "banned",
        rx(
            r"\b(?:de acuerdo a|en orden (?:de|a) \w+(?:ar|er|ir)|hace(?:r|n)? sentido"
            r"|toma(?:r|n)? lugar"
            r"|soport(?:a|an|ar|ando|ado|ada|ados|adas)"
            r"|remov(?:er|erse|ido|ida|idos|idas|erá|erán)|remuev\w+)\b"
        ),
        "say it the Spanish way: *de acuerdo con*, *para*, *tener sentido*, *ocurrir*, *admitir*",
        fires=(
            "de acuerdo a la regla",
            "en orden de detener el job",
            "no hace sentido",
            "el evento toma lugar",
            "El agente soporta streaming.",
            "se remueve el campo",
        ),
        misses=(
            "de acuerdo con la regla",
            "el soporte técnico",
            "tiene sentido",
            "en orden de prioridad",
        ),
        languages=SPANISH,
    ),
)

SPANISH_RATIONED: tuple[Rule, ...] = (
    Rule(
        "gerund-tail-es",
        "rationed",
        rx(r",\s+(?!cu[aá]ndo\b)\w+(?:ando|iendo|yendo)\b"),
        "a relative clause (*lo que permite*) or two sentences",
        fires=("El job se guarda, permitiendo reanudarlo.", "Se valida, asegurando el formato."),
        misses=("El job se guarda, lo que permite reanudarlo.", "Se detiene, cuando termina."),
        languages=SPANISH,
    ),
    Rule(
        "passive-agent-es",
        "rationed",
        rx(r"\b(?:es|son|fue|fueron|será|serán)\s+\w+(?:ad|id)[oa]s?\s+por\b"),
        "active voice, or *se*",
        fires=("El job es creado por el agente.", "Fueron enviados por la plataforma."),
        misses=("El job se crea por el agente.", "Está bloqueado por el límite."),
        languages=SPANISH,
    ),
)

PORTUGUESE_BANNED: tuple[Rule, ...] = (
    Rule(
        "signposting-pt",
        "banned",
        rx(
            r"\b(?:é importante (?:destacar|ressaltar|salientar|notar|observar|mencionar"
            r"|lembrar|ter em mente)"
            r"|vale (?:a pena )?(?:destacar|ressaltar|salientar|mencionar|notar|lembrar)"
            r"|cabe (?:destacar|ressaltar|salientar|mencionar|notar)"
            r"|em resumo|em suma|em conclus[aã]o|em poucas palavras|no fim das contas"
            r"|sem mais delongas|como podemos ver)\b"
        ),
        "start with the fact",
        fires=(
            "É importante ressaltar que o job para.",
            "Vale destacar o limite.",
            "Em resumo, o limite vale.",
        ),
        misses=("O resumo do job.", "A conclusão do turno.", "É importante o limite."),
        languages=PORTUGUESE,
    ),
    Rule(
        "inflated-vocabulary-pt",
        "banned",
        rx(
            r"\b(?:robust[oa]s?|sem costura|sem atrito|hol[ií]stic[oa]s?|potencializ\w+"
            r"|alavanc(?:ar|am|ando|ado)\w*|mergulh(?:e|ar|ando|a) (?:em|no|na|nos|nas)"
            r"|de ponta|de [uú]ltima gera[cç][aã]o|de classe mundial|inovador\w*"
            r"|revoluci\w+|transformador\w*|crucial|cruciais)\b"
        ),
        "use the plain word",
        fires=(
            "um fluxo robusto e sem costura",
            "Mergulhe no job.",
            "uma função crucial",
            "potencializar o agente",
        ),
        misses=("A chave de API", "A costura do tecido", "o robô", "a alavanca"),
        languages=PORTUGUESE,
    ),
    Rule(
        "copula-avoidance-pt",
        "banned",
        rx(
            r"\b(?:serve como|desempenha (?:um|o) papel|desempenha uma função"
            r"|representa (?:um|uma))\b"
        ),
        "say *é*",
        fires=("A tabela serve como registro.", "Cada linha representa um job."),
        misses=("Serve a página.", "A linha representa o job 4711."),
        languages=PORTUGUESE,
    ),
    Rule(
        "intensifier-pt",
        "banned",
        rx(
            r"\b(?:verdadeiramente|realmente|genuinamente|profundamente|incrivelmente"
            r"|fundamentalmente|essencialmente|em [uú]ltima an[aá]lise|notavelmente"
            r"|simplesmente|basicamente|literalmente|obviamente)\b"
        ),
        "drop it",
        fires=("É realmente importante.", "simplesmente clique"),
        misses=("A realidade do job.", "O valor real"),
        languages=PORTUGUESE,
    ),
    Rule(
        "hollow-closer-pt",
        "banned",
        rx(
            r"\b(?:fala por si(?: mesm[oa])?|nem mais nem menos|desde o primeiro dia"
            r"|desde o dia um)\b"
        ),
        "stop at the last fact",
        fires=("Fala por si mesmo.", "desde o primeiro dia"),
        misses=("o primeiro dia útil", "fala com o agente"),
        languages=PORTUGUESE,
    ),
    Rule(
        "assistant-voice-pt",
        "banned",
        rx(
            r"\b(?:espero que (?:isso |isto )?ajude|fique [àa] vontade|n[aã]o hesite em"
            r"|com prazer|[óo]tima pergunta|boa pergunta|por favor)\b"
        ),
        "delete it",
        fires=("Espero que isso ajude.", "Não hesite em perguntar.", "Por favor, aguarde."),
        misses=("A vontade do usuário", "Fique no job"),
        languages=PORTUGUESE,
    ),
    Rule(
        "register-pt",
        "banned",
        rx(
            r"\b(?:utilizador(?:es)?|ecr[aã]s?|ficheiros?|equipas?|registar|vós|tu|teu|tua|teus"
            r"|tuas|tens|podes|queres)\b"
        ),
        "the glossary sets the register: *você*, no Portugal forms",
        fires=("O utilizador abre o ficheiro.", "Tu podes escolher.", "a tua equipa"),
        misses=("O usuário abre o arquivo.", "Você pode escolher.", "a equipe"),
        languages=PORTUGUESE,
    ),
    Rule(
        "calque-pt",
        "banned",
        rx(r"\b(?:de acordo a|em ordem (?:de|para) \w+(?:ar|er|ir|or)|toma(?:r|m)? lugar)\b"),
        "say it the Portuguese way: *de acordo com*, *para*, *ocorrer*",
        fires=(
            "de acordo a regra",
            "em ordem para parar o job",
            "o evento toma lugar",
        ),
        misses=("de acordo com a regra", "para parar o job", "em ordem de prioridade", "ocorre"),
        languages=PORTUGUESE,
    ),
)

PORTUGUESE_RATIONED: tuple[Rule, ...] = (
    Rule(
        "gerund-tail-pt",
        "rationed",
        rx(r",\s+(?!qu?ando\b)\w+(?:ando|endo|indo)\b"),
        "a relative clause (*o que permite*) or two sentences",
        fires=("O job é salvo, permitindo retomá-lo.", "Valida, garantindo o formato."),
        misses=("O job é salvo, o que permite retomá-lo.", "Para, quando termina."),
        languages=PORTUGUESE,
    ),
    Rule(
        "false-friend-pt",
        "rationed",
        rx(r"\bsuport(?:a|am|ar|ando|ado|ada|ados|adas)\b"),
        "*suportar* is *to tolerate*: say *oferecer suporte a*, *aceitar*, *ser compatível com*",
        fires=("O agente suporta streaming.", "o construtor não suporta"),
        misses=("o suporte técnico", "oferece suporte a streaming"),
        languages=PORTUGUESE,
    ),
    Rule(
        "formal-connective-pt",
        "rationed",
        rx(r"\b(?:bem como|atrav[eé]s d[eo]s?|a n[ií]vel de)\b"),
        "use the plain word: *e*, *por*, *com*, *por meio de*",
        fires=("o limite bem como o prazo", "através do console", "a nível de agente"),
        misses=("bem feito", "a travessia"),
        languages=PORTUGUESE,
    ),
)

SHARED: tuple[Rule, ...] = (
    Rule(
        "exclamation",
        "banned",
        rx(r"[¡!]"),
        "use a full stop; the glossaries bar exclamation marks",
        fires=("¡Listo!", "Pronto!"),
        misses=("Listo.", "Pronto."),
        languages=BOTH,
    ),
)

BANNED: tuple[Rule, ...] = SHARED + SPANISH_BANNED + PORTUGUESE_BANNED
RATIONED: tuple[Rule, ...] = SPANISH_RATIONED + PORTUGUESE_RATIONED
