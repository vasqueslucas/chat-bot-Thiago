import os
import time
import requests
from dotenv import load_dotenv
from pathlib import Path

# ====== CARREGAR TOKEN DO .env NA MESMA PASTA ======

# Descobre a pasta onde está o arquivo bot.py
BASE_DIR = Path(__file__).resolve().parent

# Caminho completo do .env
env_path = BASE_DIR / ".env"

print("📁 Pasta do bot.py:", BASE_DIR)
print("🧾 Procurando .env em:", env_path)

# Carrega o .env a partir desse caminho exato
load_dotenv(env_path)

TOKEN = os.getenv("TELEGRAM_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

if not TOKEN:
    print("❌ TOKEN não encontrado.")
    print("Verifique se o arquivo .env tem a linha:")
    print("TELEGRAM_TOKEN=SEU_TOKEN_AQUI")
    raise SystemExit("Encerrando porque o TOKEN está vazio.")

print("🤖 Bot do Lucas  iniciando...")
print("BASE_URL:", BASE_URL)


# ====== FUNÇÃO PARA PEGAR ÚLTIMA MENSAGEM ======

def get_last_update():
    """
    Busca o último update do bot (offset=-1) e retorna
    chat_id, texto da mensagem e data.
    Não quebra se não existir 'result' ou se der erro na API.
    """
    try:
        res = requests.get(f"{BASE_URL}/getUpdates?offset=-1", timeout=10)
    except Exception as e:
        print("❌ Erro na requisição ao Telegram:", e)
        return None, None, None

    if not res.ok:
        print("❌ Erro HTTP:", res.status_code, res.text)
        return None, None, None

    try:
        dados = res.json()
    except Exception as e:
        print("❌ Erro ao converter resposta para JSON:", e)
        print("Resposta bruta:", res.text)
        return None, None, None

    if not dados.get("ok", False):
        print("❌ Erro na API do Telegram:", dados)
        return None, None, None

    results = dados.get("result", [])

    if not results:
        return None, None, None

    update = results[-1]
    message = update.get("message")
    if not message:
        return None, None, None

    chat = message.get("chat")
    text = message.get("text")
    date = message.get("date")

    if not chat or text is None or date is None:
        return None, None, None

    chat_id = chat.get("id")

    return chat_id, text, date


# ====== FUNÇÃO PRINCIPAL DE LÓGICA DO BOT ======

def tratar_mensagem(texto):
    """
    Decide o que responder com base no texto recebido.
    - Comandos de física (/vm, /dist, /tviagem)
    - Conversões (/km, /temp, /horas)
    - /start e /help
    - Calculadora (eval) como fallback
    """
    if texto is None:
        return None

    texto = texto.strip()
    parts = texto.split()
    comando = parts[0].lower()
    

    # --- FÍSICA: VELOCIDADE MÉDIA / DISTÂNCIA / TEMPO ---

    # /vm distancia_km tempo_h
    if comando == "/vm":
        if len(parts) < 3:
            return "Use assim: /vm distancia_km tempo_h  (ex: /vm 100 2)"
        try:
            distancia = float(parts[1].replace(",", "."))
            tempo = float(parts[2].replace(",", "."))
            if tempo == 0:
                return "O tempo não pode ser 0, né 😅"
            velocidade = distancia / tempo
            return f"Velocidade média = {velocidade:.2f} km/h"
        except ValueError:
            return "Valores inválidos. Exemplo: /vm 120 1.5"

    # /dist velocidade_kmh tempo_h
    if comando == "/dist":
        if len(parts) < 3:
            return "Use assim: /dist velocidade_kmh tempo_h  (ex: /dist 80 2)"
        try:
            velocidade = float(parts[1].replace(",", "."))
            tempo = float(parts[2].replace(",", "."))
            distancia = velocidade * tempo
            return f"Distância percorrida = {distancia:.2f} km"
        except ValueError:
            return "Valores inválidos. Exemplo: /dist 90 2.5"

    # /tviagem distancia_km velocidade_kmh
    if comando == "/tviagem":
        if len(parts) < 3:
            return "Use assim: /tviagem distancia_km velocidade_kmh  (ex: /tviagem 150 100)"
        try:
            distancia = float(parts[1].replace(",", "."))
            velocidade = float(parts[2].replace(",", "."))
            if velocidade == 0:
                return "Velocidade 0 não rola, né 😅"
            tempo = distancia / velocidade
            return f"Tempo de viagem ≈ {tempo:.2f} h"
        except ValueError:
            return "Valores inválidos. Exemplo: /tviagem 200 80"

    # --- CONVERSOR DE UNIDADES ---

    if comando == "/km":
        if len(parts) < 2:
            return "Use assim: /km valor  (ex: /km 10)"
        try:
            valor = float(parts[1].replace(",", "."))
            metros = valor * 1000
            return f"{valor} km = {metros} m"
        except ValueError:
            return "Valor inválido. Tente algo como: /km 5"

    if comando == "/temp":
        if len(parts) < 2:
            return "Use assim: /temp valor_em_C  (ex: /temp 30)"
        try:
            celsius = float(parts[1].replace(",", "."))
            fahrenheit = celsius * 9/5 + 32
            return f"{celsius} °C = {fahrenheit:.1f} °F"
        except ValueError:
            return "Valor inválido. Tente algo como: /temp 25"

    if comando == "/horas":
        if len(parts) < 2:
            return "Use assim: /horas valor  (ex: /horas 2)"
        try:
            horas = float(parts[1].replace(",", "."))
            minutos = horas * 60
            return f"{horas} horas = {minutos} minutos"
        except ValueError:
            return "Valor inválido. Tente algo como: /horas 1.5"

    # --- AJUDA / MENU ---

    if comando in ["/start", "/help"]:
        return (
            "🤖 Bot do Lucas  aqui!\n\n"
            "Funções disponíveis:\n"
            "🧮 Calculadora: envie expressões como 2+2, 10*3, (5+7)/2\n"
            "📏 Converter km → m: /km valor   (ex: /km 10)\n"
            "🌡️ Converter °C → °F: /temp valor   (ex: /temp 30)\n"
            "⏱️ Converter horas → minutos: /horas valor   (ex: /horas 1.5)\n"
            "🚗 Velocidade média: /vm distancia_km tempo_h   (ex: /vm 100 2)\n"
            "📍 Distância: /dist velocidade_kmh tempo_h      (ex: /dist 80 2)\n"
            "⏳ Tempo de viagem: /tviagem distancia_km velocidade_kmh   (ex: /tviagem 150 100)\n"
        )

    # --- CALCULADORA PADRÃO (eval) ---

    try:
        resultado = eval(texto)
        return f"Resultado: {resultado}"
    except Exception:
        return (
            "Não entendi 🤔\n"
            "Tente:\n"
            "• Expressões matemáticas (ex: 2+2, (5+7)/2)\n"
            "• Ou comandos:\n"
            "   /km 10\n"
            "   /temp 30\n"
            "   /horas 2\n"
            "   /vm 100 2\n"
            "   /dist 80 2\n"
            "   /tviagem 150 100\n"
            "   /help\n"
        )


# ====== LOOP PRINCIPAL ======

last_date = 0

print("🤖 Bot do Lucas  iniciado (loop principal)...")

while True:
    try:
        chat_id, text, msg_date = get_last_update()

        if chat_id is None:
            time.sleep(1)
            continue

        if msg_date > last_date:
            last_date = msg_date
            print(f"📩 Mensagem recebida: {text}")

            resposta = tratar_mensagem(text)

            if resposta:
                r = requests.post(
                    f"{BASE_URL}/sendMessage",
                    data={"chat_id": chat_id, "text": resposta}
                )
                print("📤 Resposta enviada. Status:", r.status_code)

        time.sleep(1)

    except Exception as e:
        print("🔥 Erro no loop principal:", e)
        time.sleep(2)
        continue
