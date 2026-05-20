from flask import Flask, request
import anthropic
import requests
import os

app = Flask(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")

SYSTEM_PROMPT = "You are a professional customer service assistant for HDS company. Reply in Arabic."

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
conversation_history = {}


@app.route("/webhook", methods=["GET"])
def verify():
          mode = request.args.get("hub.mode")
          token = request.args.get("hub.verify_token")
          challenge = request.args.get("hub.challenge")
          if mode == "subscribe" and token == VERIFY_TOKEN:
                        return challenge, 200
                    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook():
          data = request.json
    try:
                  entry = data["entry"][0]
                  changes = entry["changes"][0]
                  value = changes["value"]
                  if "messages" not in value:
                                    return "OK", 200
                                message = value["messages"][0]
        if message["type"] != "text":
                          return "OK", 200
                      user_message = message["text"]["body"]
        from_number = message["from"]
        if from_number not in conversation_history:
                          conversation_history[from_number] = []
                      conversation_history[from_number].append({"role": "user", "content": user_message})
        if len(conversation_history[from_number]) > 20:
                          conversation_history[from_number] = conversation_history[from_number][-20:]
                      response = client.messages.create(
                                        model="claude-sonnet-4-5",
                                        max_tokens=1024,
                                        system=SYSTEM_PROMPT,
                                        messages=conversation_history[from_number],
                      )
        reply = response.content[0].text
        conversation_history[from_number].append({"role": "assistant", "content": reply})
        send_whatsapp_message(from_number, reply)
except Exception as e:
        print(f"Error: {e}")
    return "OK", 200


def send_whatsapp_message(to, text):
          url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
                  "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                  "Content-Type": "application/json",
    }
    payload = {
                  "messaging_product": "whatsapp",
                  "to": to,
                  "type": "text",
                  "text": {"body": text},
    }
    requests.post(url, json=payload, headers=headers)


if __name__ == "__main__":
          app.run(host="0.0.0.0", port=5000)
