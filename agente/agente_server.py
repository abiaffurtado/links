#!/usr/bin/env python3
"""
Agente de Comunicação LigueLead — Backend sem n8n
Uso: python3 agente_server.py [porta]
Requer: pip install openai
"""
import json, sys, os
from http.server import BaseHTTPRequestHandler, HTTPServer
from openai import OpenAI

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8899
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

SYSTEM_PROMPT = """Você é um agente especialista em estratégias de comunicação automatizada usando a LigueLead.

A LigueLead oferece 3 canais de comunicação:
1. **SMS** — 95%+ de abertura, ideal para lembretes e alertas rápidos. Limite: 160 caracteres.
2. **Voz (ligação automatizada)** — maior impacto pessoal, ideal para cobranças, confirmações críticas, eventos urgentes.
3. **SMS Flash** — aparece direto na tela do celular sem abrir o app, 100% de visualização, ideal para alertas de alta urgência.

Quando o usuário descrever uma dor ou cenário de negócio, crie uma régua de comunicação completa com:

## 🎯 Nome da Régua
(ex: "Régua de Cobrança" ou "Régua de Confirmação de Agendamento")

## 📌 Objetivo
Uma frase clara.

## 📋 Fluxo de Comunicação
Para cada etapa, especifique:
- **Gatilho**: o que inicia essa etapa (ex: "D+1 após vencimento")
- **Canal**: SMS / Voz / SMS Flash
- **Mensagem pronta**: texto exato para usar
- **Objetivo da etapa**: o que busca

## 💡 Por que essa régua funciona
Breve explicação estratégica.

## 📊 Resultado esperado
KPI ou impacto estimado.

Responda sempre em português brasileiro. Seja específico, acionável e use emojis para facilitar a leitura. Mensagens devem estar prontas para copiar e usar."""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}")

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        message = body.get("message", "")

        if not message:
            self.send_response(400)
            self.send_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "message required"}).encode())
            return

        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.7,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message}
            ]
        )
        strategy = response.choices[0].message.content

        self.send_response(200)
        self.send_cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"strategy": strategy}).encode())


if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("⚠️  Defina OPENAI_API_KEY no ambiente")
        print("   export OPENAI_API_KEY=sk-...")
        sys.exit(1)
    print(f"🤖 Agente LigueLead rodando em http://localhost:{PORT}")
    print(f"   Endpoint: POST http://localhost:{PORT}/")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
