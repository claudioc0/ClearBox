<p align="center">
  <img src="https://img.icons8.com/color/96/000000/artificial-intelligence.png" alt="AI Icon" width="80"/>
</p>

<h1 align="center">
  <span style="color:#2563eb;">📧 ClearBox</span>
</h1>

<p align="center">
  <span style="color:#10b981;">Sistema inteligente para classificação automática de emails</span>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue.svg" />
  <img src="https://img.shields.io/badge/Flask-3.0-green.svg" />
  <img src="https://img.shields.io/badge/Hugging_Face-Transformers-yellow.svg" />
  <img src="https://img.shields.io/badge/Frontend-Vanilla_JS-orange.svg" />
  <img src="https://img.shields.io/badge/Status-Completo-brightgreen.svg" />
</p>

---

## 📝 <span style="color:#6366f1;">Descrição do Projeto</span>

Sistema completo de classificação de emails que utiliza um modelo de linguagem avançado (IA) para categorizar conteúdo como <span style="color:#10b981;"><strong>Produtivo</strong></span> ou <span style="color:#ef4444;"><strong>Improdutivo</strong></span> e gerar respostas automáticas personalizadas.

---

## ✨ <span style="color:#0ea5e9;">Funcionalidades</span>

### <span style="color:#22d3ee;">Frontend</span>
* 🗂️ **Upload Inteligente**: arrastar e soltar arquivos .txt e .pdf
* 📄 **Extração de PDF no cliente** com PDF.js
* 🌙 **Modo Escuro persistente**
* 🕑 **Histórico de Classificações** no navegador
* ⚡ **Interface Reativa** com animações e toasts

### <span style="color:#22d3ee;">Backend</span>
* 🤖 **Classificação com IA (DeBERTa - Zero-Shot)**
* 🛡️ **Lógica Híbrida** com rede de segurança baseada em regras
* 🔗 **API RESTful** com endpoints de saúde e documentação
* 📝 **Respostas Contextuais automáticas**
* 🏷️ **Destaque de Palavras-Chave** produtivas/improdutivas

---

## 🛠️ <span style="color:#f59e42;">Tecnologias Utilizadas</span>

### <span style="color:#fbbf24;">Frontend</span>
* 🌐 **HTML5 e CSS3**
* 🎨 **Tailwind CSS (via CDN)**
* 💻 **JavaScript (Vanilla)**
* 📚 **PDF.js (Mozilla)**

### <span style="color:#fbbf24;">Backend</span>
* 🐍 **Python 3.9+**
* 🔥 **Flask e Flask-CORS**
* 🤗 **Hugging Face Transformers**
* 🧠 **PyTorch**
* 🗣️ **NLTK**
* 🔒 **pyOpenSSL**
* 🚀 **Gunicorn**

---

## 🚀 <span style="color:#10b981;">Instalação</span>

### <span style="color:#6366f1;">Pré-requisitos</span>
* Python 3.9+
* pip
* Git

### <span style="color:#6366f1;">Passos</span>

#### Backend
```bash
git clone https://github.com/claudioc0/email-classifier-ai.git
cd email-classifier-ai/project
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
python backend/app.py
```

#### Frontend
```bash
cd project
python -m http.server 8080
```

Acesse: [http://localhost:8080](http://localhost:8080)

> ⚠️ O backend roda em https://localhost:8000. Na primeira vez, pode ser necessário aceitar o aviso de segurança no navegador (digite `thisisunsafe` no Chrome/Opera).

---

## 🧩 <span style="color:#6366f1;">Algoritmo</span>

**Dois estágios para máxima precisão:**
1. 🧠 **Classificação Primária com IA (DeBERTa)**
2. 🛡️ **Lógica Híbrida** (verificação de palavras-chave spam)

---

## 🌱 <span style="color:#22c55e;">Melhorias Futuras</span>

* 🧠 **IA Explicável (XAI) com LIME**
* 🛠️ **Fine-Tuning do modelo DeBERTa**
* 🧪 **Testes Automatizados (unitários e integração)**
* 🔄 **Pipeline CI/CD com GitHub Actions**
* 📧 **Integração com APIs de e-mail (Gmail, Outlook)**

---

<div align="center">
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="48" alt="Python Dev Icon"/>
  <br>
  <span style="color:#6366f1;"><strong>Desenvolvido por Claudio Colombo</strong></span><br>
  Utilizando tecnologias modernas para classificação inteligente de emails.
</div>
