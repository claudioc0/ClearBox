Email Classifier AI
<p align="center">
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Python-3.9%2B-blue.svg" alt="Python Version">
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Flask-3.0-green.svg" alt="Flask">
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Hugging_Face-Transformers-yellow.svg" alt="Hugging Face Transformers">
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Frontend-Vanilla_JS-orange.svg" alt="Frontend">
<img src="https://www.google.com/search?q=https://img.shields.io/badge/Status-Completo-brightgreen.svg" alt="Status">
</p>

Sistema completo de classificação de emails que utiliza um modelo de linguagem avançado (IA) para categorizar conteúdo como Produtivo ou Improdutivo e gerar respostas automáticas personalizadas.

## ✨ <span style="color:#0ea5e9;">Funcionalidades</span>

### <span style="color:#22d3ee;">Interface Web (Frontend)</span>
* 🗂️ **Upload Inteligente**: Suporte a arrastar e soltar (drag-and-drop) de arquivos .txt e .pdf.
* 📄 **Extração de PDF no Cliente**: O texto de arquivos PDF é extraído diretamente no navegador com pdf.js para maior velocidade e privacidade.
* 🌙 **Modo Escuro**: Tema adaptável para preferência do usuário, com persistência.
* 🕑 **Histórico de Classificações**: As últimas análises são salvas no navegador para consulta rápida.
* ⚡ **Interface Reativa e Moderna**: Design responsivo com animações, toasts de notificação e feedback visual para todas as ações.

### <span style="color:#22d3ee;">Backend Python</span>
* 🤖 **Classificação com IA de Ponta**: Utiliza o modelo DeBERTa da Hugging Face para classificação "Zero-Shot", compreendendo o contexto do texto.
* 🛡️ **Lógica Híbrida**: Combina a decisão da IA com uma "rede de segurança" baseada em regras para corrigir potenciais falhas em casos ambíguos.
* 🔗 **API RESTful Robusta**: Endpoints para classificação, verificação de saúde e documentação.
* 📝 **Respostas Contextuais**: Geração automática de respostas adaptadas à categoria identificada.
* 🏷️ **Destaque de Palavras-Chave**: Identifica e retorna as palavras do texto que correspondem a listas de termos produtivos/improdutivos.

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
* 🤗 **Hugging Face Transformers (para o modelo de IA)**
* 🧠 **PyTorch**
* 🗣️ **NLTK (para pré-processamento de texto)**
* 🔒 **pyOpenSSL (para servidor HTTPS local)**
* 🚀 **Gunicorn (para deploy em produção)**

Instalação e Execução Local
Pré-requisitos
Python 3.9+ e pip
Git

1.Backend
# Clone este repositório 
git clone [https://github.com/claudioc0/email-classifier-ai.git](https://github.com/claudioc0/email-classifier-ai.git)
cd email-classifier-ai/project

# Crie e ative um ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# Instale as dependências
pip install -r backend/requirements.txt

# Execute o servidor Flask (deixe este terminal aberto)
python backend/app.py

2. Frontend
Abra um novo terminal na mesma pasta project.
# Inicie um servidor HTTP simples (deixe este terminal aberto)
python -m http.server 8080

3. Acesso
Acesse http://localhost:8080 no seu navegador.

NOTA IMPORTANTE: O servidor backend roda em https://localhost:8000. Na primeira vez, a aplicação pode parecer "desconectada". Para resolver, abra uma nova aba, acesse https://localhost:8000/health, aceite o aviso de segurança do navegador (no Opera/Chrome, digite thisisunsafe na página de erro) e, em seguida, recarregue a página da aplicação.

Algoritmo de Classificação (Como Funciona)
O sistema utiliza uma abordagem em dois estágios para máxima precisão:

Classificação Primária com IA (DeBERTa): O texto do e-mail é analisado por um modelo de linguagem pré-treinado que entende o contexto e a semântica, classificando-o como "Produtivo" ou "Improdutivo".

Lógica Híbrida (Rede de Segurança): Se a IA classifica um e-mail como "Produtivo", uma verificação final é feita em busca de palavras-chave de spam de alta certeza (ex: "investimento", "renda extra"). Se encontradas, a classificação é corrigida para "Improdutivo", garantindo maior robustez contra falsos positivos.

## 🚀 <span style="color:#10b981;">Melhorias Futuras</span>

* 🧠 **IA Explicável (XAI)**: Reintegrar uma biblioteca como a **LIME** para extrair as palavras-chave que a IA considerou mais importantes, em vez de usar listas estáticas.
* 🛠️ **Fine-Tuning do Modelo**: Treinar o modelo DeBERTa com um dataset específico de e-mails para aumentar ainda mais a precisão.
* 🧪 **Testes Automatizados**: Implementar testes unitários e de integração para a API.
* 🔄 **Pipeline de CI/CD**: Criar um fluxo de integração e deploy contínuo com GitHub Actions.
* 📧 **Integração Direta com E-mail**: Conectar-se a APIs como Gmail ou Outlook para classificar e-mails diretamente da caixa de entrada.

> <span style="color:#6366f1;"><strong>Desenvolvido por Claudio Colombo</strong></span>, usando tecnologias modernas para classificação inteligente de emails.