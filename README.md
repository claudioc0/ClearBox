project:
  name: "Email Classifier AI"
  description: >
    Sistema completo de classificação de emails que utiliza um modelo de linguagem
    avançado (IA) para categorizar conteúdo como Produtivo ou Improdutivo e gerar
    respostas automáticas personalizadas.
  author: "Claudio Colombo"
  status: "Completo"

badges:
  - "https://img.shields.io/badge/Python-3.9%2B-blue.svg"
  - "https://img.shields.io/badge/Flask-3.0-green.svg"
  - "https://img.shields.io/badge/Hugging_Face-Transformers-yellow.svg"
  - "https://img.shields.io/badge/Frontend-Vanilla_JS-orange.svg"
  - "https://img.shields.io/badge/Status-Completo-brightgreen.svg"

features:
  frontend:
    - "Upload Inteligente: arrastar e soltar arquivos .txt e .pdf"
    - "Extração de PDF no cliente com PDF.js"
    - "Modo Escuro persistente"
    - "Histórico de Classificações no navegador"
    - "Interface Reativa com animações e toasts"
  backend:
    - "Classificação com IA (DeBERTa - Zero-Shot)"
    - "Lógica Híbrida com rede de segurança baseada em regras"
    - "API RESTful com endpoints de saúde e documentação"
    - "Respostas Contextuais automáticas"
    - "Destaque de Palavras-Chave produtivas/improdutivas"

technologies:
  frontend:
    - "HTML5 e CSS3"
    - "Tailwind CSS (via CDN)"
    - "JavaScript (Vanilla)"
    - "PDF.js (Mozilla)"
  backend:
    - "Python 3.9+"
    - "Flask e Flask-CORS"
    - "Hugging Face Transformers"
    - "PyTorch"
    - "NLTK"
    - "pyOpenSSL"
    - "Gunicorn"

installation:
  prerequisites:
    - "Python 3.9+"
    - "pip"
    - "Git"
  steps:
    backend:
      - "git clone https://github.com/claudioc0/email-classifier-ai.git"
      - "cd email-classifier-ai/project"
      - "python -m venv venv"
      - ".\\venv\\Scripts\\Activate.ps1"
      - "pip install -r backend/requirements.txt"
      - "python backend/app.py"
    frontend:
      - "cd project"
      - "python -m http.server 8080"
    access: "http://localhost:8080"
  notes: >
    O backend roda em https://localhost:8000. A primeira vez pode exigir
    aceitar o aviso de segurança no navegador (digitar 'thisisunsafe' no Chrome/Opera).

algorithm:
  description: "Dois estágios para máxima precisão"
  stages:
    - "Classificação Primária com IA (DeBERTa)"
    - "Lógica Híbrida (verificação de palavras-chave spam)"

future_improvements:
  - "IA Explicável (XAI) com LIME"
  - "Fine-Tuning do modelo DeBERTa"
  - "Testes Automatizados (unitários e integração)"
  - "Pipeline CI/CD com GitHub Actions"
  - "Integração com APIs de e-mail (Gmail, Outlook)"
