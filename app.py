import os
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de las APIs
WHATSAPP_API_URL = f"https://graph.facebook.com/v16.0/{os.getenv('WHATSAPP_PHONE_ID')}/messages"
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')  # Sin espacio adicional

app = Flask(__name__)

@app.before_request
def skip_ngrok_warning():
    # Añade el encabezado ngrok-skip-browser-warning si no está presente
    request.headers.environ['ngrok-skip-browser-warning'] = 'true'
@app.after_request
def add_ngrok_skip_header(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response
    
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """
    Verificar el webhook de WhatsApp.
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print("Webhook verificado correctamente.")
        return challenge, 200
    else:
        print(f"Error en la verificación: token recibido {token}, token esperado {VERIFY_TOKEN}")
        return 'Error de verificación', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Manejar mensajes entrantes de WhatsApp.
    """
    try:
        data = request.json
        if not data:
            return jsonify({'status': 'error', 'message': 'No se recibió ningún JSON'}), 400

        changes = data.get('entry', [{}])[0].get('changes', [{}])
        messages = changes[0].get('value', {}).get('messages', [{}])
        if not messages or not messages[0]:
            return jsonify({'status': 'error', 'message': 'No hay mensajes en el webhook'}), 400

        incoming_message = messages[0].get('text', {}).get('body', '')
        user_phone = messages[0].get('from', '')

        # Enviar respuesta a WhatsApp
        send_whatsapp_message(user_phone, incoming_message)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def send_whatsapp_message(phone, message):
    """
    Enviar un mensaje a través de la API de WhatsApp.
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
    print(f"Respuesta de WhatsApp: {response.json()}")
    return response.json()

if __name__ == '__main__':
    print(f"VERIFY_TOKEN: {VERIFY_TOKEN}")  # Verifica el token en los logs
    app.run(port=5000)
