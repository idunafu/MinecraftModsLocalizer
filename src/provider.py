API_KEY = None
CHUNK_SIZE = 1
MODEL = 'gpt-4o-mini-2024-07-18'
API_BASE = None  # OpenAI互換APIのベースURL
TEMPERATURE = 1.0  # デフォルト値として1.0を設定
REQUEST_INTERVAL = 0.0  # APIリクエスト間隔（秒）- デフォルトは0秒（間隔なし）
PROMPT = """You are a professional translator. Please translate the following English text into Japanese.

## Important Translation Rules
- Translate line by line, strictly in order
- Ensure the number of lines before and after translation matches exactly (do not add or remove lines)
- Output only the translation result, without any greetings or explanations

## Input Text Information
- Number of lines: {line_count}

## Detailed Translation Instructions
- Treat sentences on different lines as separate, even if they seem contextually connected
- If multiple sentences appear on a single line, translate them as one line
- Use katakana for proper nouns when appropriate
- Preserve programming variables (e.g., %s, $1, \") and special symbols as they are
- Maintain backslashes (\\) as they may be used as escape characters
- Do not edit any characters that appear to be special symbols
- For idiomatic expressions, prioritize conveying the meaning over literal translation.
- When appropriate, adapt cultural references to be more relevant to a Japanese audience.
- The text is about Minecraft mods. Keep this context in mind while translating

Once you receive the input text, proceed with the translation following these rules strictly.

# Example

### input
§6Checks for ore behind the
§6walls, floors or ceilings.
Whether or not mining fatigue is applied to players in the temple
if it has not yet been cleared.

### incorrect output
§6壁、床、または天井の後ろにある鉱石をチェックします。
まだクリアされていない場合、寺院内のプレイヤーにマイニング疲労が適用されるかどうか。

### correct output
§6後ろにある鉱石をチェックします。
§6壁、床、または天井
寺院内のプレイヤーにマイニング疲労が適用されるかどうか。
もしクリアされていない場合


### input
Add a new requirement group.Requirement groups can hold multiplerequirements and basicallymake them one big requirement.Requirement groups have two modes.In §zAND §rmode, all requirements needto return TRUE (which means "Yes, load!"),but in §zOR §rmode, only one requirementneeds to return TRUE.

### incorrect output
新しい要件グループを追加します。
要件グループは複数の要件を保持でき、基本的にそれらを1つの大きな要件にまとめます。要件グループには2つのモードがあります。
§zAND §rモードでは、すべての要件がTRUE（「はい、ロードする！」を意味します）を返す必要がありますが、§zOR §rモードでは、1つの要件だけがTRUEを返す必要があります。

### correct output
新しい要件グループを追加します。要件グループは複数の要件を保持し、基本的にそれらを1つの大きな要件にまとめます。要件グループには2つのモードがあります。§zAND §rモードでは、すべての要件がTRUE（「はい、読み込みます！」という意味）を返す必要がありますが、§zOR §rモードでは、1つの要件だけがTRUEを返せば十分です。"""


LOG_DIRECTORY = None


def provide_api_key():
    global API_KEY

    return API_KEY


def set_api_key(api_key):
    global API_KEY

    API_KEY = api_key


def provide_api_base():
    global API_BASE

    return API_BASE


def set_api_base(api_base):
    global API_BASE

    API_BASE = api_base


def provide_chunk_size():
    global CHUNK_SIZE

    return CHUNK_SIZE


def set_chunk_size(chunk_size):
    global CHUNK_SIZE

    CHUNK_SIZE = chunk_size


def provide_model():
    global MODEL

    return MODEL


def set_model(model):
    global MODEL

    MODEL = model


def provide_prompt():
    global PROMPT

    return PROMPT


def set_prompt(prompt):
    global PROMPT

    PROMPT = prompt


def provide_log_directory():
    global LOG_DIRECTORY

    return LOG_DIRECTORY


def set_log_directory(log_directory):
    global LOG_DIRECTORY

    LOG_DIRECTORY = log_directory


def provide_temperature():
    global TEMPERATURE

    return TEMPERATURE


def set_temperature(temperature):
    global TEMPERATURE

    TEMPERATURE = temperature


def provide_request_interval():
    global REQUEST_INTERVAL

    return REQUEST_INTERVAL


def set_request_interval(interval):
    global REQUEST_INTERVAL

    REQUEST_INTERVAL = interval