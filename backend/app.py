import os
import nltk

# --- Configuração de diretórios e variáveis de ambiente ---
hf_cache_dir = "/tmp/hf_cache"
os.makedirs(hf_cache_dir, exist_ok=True)
os.environ["TRANSFORMERS_CACHE"] = hf_cache_dir
os.environ["HF_HOME"] = hf_cache_dir
os.environ["HF_DATASETS_CACHE"] = hf_cache_dir

nltk_data_dir = "/tmp/nltk_data"
os.makedirs(nltk_data_dir, exist_ok=True)
nltk.data.path.insert(0, nltk_data_dir)


import re
import logging
from typing import Dict, List
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import RSLPStemmer

from transformers import pipeline

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- Download dos pacotes NLTK necessários ---
nltk_packages = ['punkt', 'stopwords', 'rslp']
for pkg_id in nltk_packages:
    try:
        if pkg_id == 'rslp':
            nltk.data.find(f'stemmers/{pkg_id}')
        elif pkg_id == 'stopwords':
            nltk.data.find(f'corpora/{pkg_id}')
        else:
            nltk.data.find(f'tokenizers/{pkg_id}')
        logger.info(f"NLTK package '{pkg_id}' already downloaded.")
    except LookupError:
        logger.info(f"Downloading NLTK package '{pkg_id}' to {nltk_data_dir}...")
        nltk.download(pkg_id, download_dir=nltk_data_dir)

# --- Flask App ---
app = Flask(__name__, static_folder='../static', static_url_path='')
CORS(app)

@app.route('/')
def api_info():
    return app.send_static_file('index.html')

class EmailClassifier:
    def __init__(self):
        self.stemmer = RSLPStemmer()
        self.stop_words = set(stopwords.words('portuguese') + stopwords.words('english'))
        self.productive_keywords = {
            'reuniao', 'projeto', 'prazo', 'entrega', 'relatorio', 'apresentacao',
            'meeting', 'project', 'deadline', 'delivery', 'report', 'presentation',
            'trabalho', 'tarefa', 'responsabilidade', 'objetivo', 'meta', 'agenda',
            'cronograma', 'planejamento', 'estrategia', 'desenvolvimento', 'analise',
            'proposta', 'orcamento', 'contrato', 'negociacao', 'cliente', 'fornecedor',
            'colaboracao', 'equipe', 'time', 'departamento', 'gerencia', 'diretoria',
            'solucao', 'problema', 'discussao', 'feedback', 'revisao', 'aprovacao'
        }
        self.unproductive_keywords = {
            'spam', 'promocao', 'desconto', 'oferta', 'gratis', 'ganhe', 'premio',
            'promotion', 'discount', 'offer', 'free', 'win', 'prize', 'lottery',
            'clique', 'click', 'urgente', 'urgent', 'limitado', 'limited',
            'exclusivo', 'exclusive', 'oportunidade', 'opportunity', 'dinheiro',
            'money', 'renda', 'income', 'investimento', 'investment', 'lucro',
            'profit', 'ganhar', 'earn', 'facil', 'easy', 'rapido', 'quick',
            'compre', 'buy', 'venda', 'sale', 'barato', 'cheap', 'economize'
        }
        self.ai_classifier = None
        self.use_ai_model = self._initialize_ai_model()
        logger.info(f"EmailClassifier initialized. AI Model: {'Enabled' if self.use_ai_model else 'Disabled'}")

    def _initialize_ai_model(self):
        try:
            logger.info("Initializing AI classification model...")
            model_name = "facebook/bart-large-mnli"
            self.ai_classifier = pipeline(
                "zero-shot-classification",
                model=model_name,
                device=-1,
                cache_dir=hf_cache_dir
            )
            logger.info(f"AI model '{model_name}' loaded successfully")
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize AI model: {e}")
            logger.info("Falling back to keyword-based classification")
            return False

    def preprocess_text(self, text: str) -> List[str]:
        text = text.lower()
        text = re.sub(r'[^a-záàâãéèêíïóôõöúçñ\s]', ' ', text)
        tokens = word_tokenize(text, language='portuguese')
        return [
            self.stemmer.stem(token)
            for token in tokens
            if token not in self.stop_words and len(token) > 2
        ]

    def find_keywords(self, tokens, keyword_set):
        found = set()
        for token in tokens:
            for kw in keyword_set:
                stemmed_kw = self.stemmer.stem(kw)
                if stemmed_kw in token or token in stemmed_kw or kw in token or token in kw:
                    found.add(kw)
        return list(found)

    def classify_with_ai(self, content: str) -> Dict:
        try:
            candidate_labels = [
                "E-mail de trabalho sobre tarefa, projeto ou reunião",
                "E-mail de marketing, spam, propaganda ou anúncio"
            ]
            result = self.ai_classifier(content, candidate_labels, multi_label=False)
            logger.info(f"AI Model Raw Output: {result}")
            top_label = result['labels'][0]
            confidence = result['scores'][0]
            category = "Produtivo" if top_label == candidate_labels[0] else "Improdutivo"
            tokens = self.preprocess_text(content)
            found_keywords = self.find_keywords(
                tokens,
                self.productive_keywords if category == "Produtivo" else self.unproductive_keywords
            )
            return {
                "category": category,
                "confidence": confidence,
                "method": "AI",
                "found_keywords": found_keywords[:10]
            }
        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            return self.classify_with_keywords(content)

    def classify_with_keywords(self, content: str) -> Dict:
        tokens = self.preprocess_text(content)
        found_productive = self.find_keywords(tokens, self.productive_keywords)
        found_unproductive = self.find_keywords(tokens, self.unproductive_keywords)
        productive_score = len(found_productive)
        unproductive_score = len(found_unproductive)
        if productive_score > unproductive_score:
            category = "Produtivo"
            confidence = min(0.95, max(0.6, (productive_score + 1) / (productive_score + unproductive_score + 2)))
            found_keywords = found_productive
        elif unproductive_score > productive_score:
            category = "Improdutivo"
            confidence = min(0.95, max(0.6, (unproductive_score + 1) / (productive_score + unproductive_score + 2)))
            found_keywords = found_unproductive
        else:
            category = "Produtivo"
            confidence = 0.5
            found_keywords = found_productive if found_productive else []
        return {
            "category": category,
            "confidence": confidence,
            "method": "Keywords",
            "found_keywords": found_keywords[:10]
        }

    def classify_email(self, content: str) -> Dict:
        start_time = datetime.now()
        logger.info(f"Classifying email with {len(content)} characters")
        if self.use_ai_model:
            classification_result = self.classify_with_ai(content)
        else:
            classification_result = self.classify_with_keywords(content)
        # Lógica híbrida para detectar spam disfarçado
        if classification_result["category"] == "Produtivo" and classification_result["method"] == "AI":
            spam_triggers = {
                'investimento', 'renda', 'lucro', 'ganhar dinheiro', 'gratis', 'oportunidade unica', 'clique aqui', 'promocao',
                'lottery', 'prize', 'winner', 'click here', 'urgent', 'confidential', 'agent', 'claim your prize', 'selected as a winner',
                'contact our agent', 'provide your details', 'annual international lottery', 'you have won', 'usd', 'premio', 'ganhe', 'oferta'
            }
            content_lower = content.lower()
            if any(trigger in content_lower for trigger in spam_triggers):
                logger.info("Hybrid Logic Triggered: AI classified as Productive, but spam keywords were found. Overriding to Improductive.")
                classification_result["category"] = "Improdutivo"
                classification_result["confidence"] = 0.95
                classification_result["method"] = "AI + Hybrid Rule"
        suggested_response = self.generate_response(classification_result["category"], content)
        reasoning = self.generate_reasoning(
            classification_result["category"],
            classification_result["found_keywords"],
            classification_result["method"]
        )
        processing_time = (datetime.now() - start_time).total_seconds()
        result = {
            "category": classification_result["category"],
            "confidence": classification_result["confidence"],
            "suggestedResponse": suggested_response,
            "reasoning": reasoning,
            "processingTime": processing_time,
            "highlightedKeywords": classification_result["found_keywords"],
            "originalContent": content,
            "classificationMethod": classification_result["method"]
        }
        logger.info(f"Classification completed: {result['category']} "
                    f"({result['confidence']:.2f} confidence) "
                    f"in {processing_time:.2f}s using {result['classificationMethod']}")
        return result

    def generate_response(self, category: str, content: str) -> str:
        content_lower = content.lower()
        if category == "Produtivo":
            if any(word in content_lower for word in ['reuniao', 'meeting', 'encontro', 'agenda']):
                return (
                    "Obrigado pelo seu email.\n\n"
                    "Recebi sua solicitação de reunião e vou verificar minha agenda. Retornarei em breve com minha disponibilidade.\n\n"
                    "Caso seja urgente, não hesite em entrar em contato por telefone.\n\n"
                    "Atenciosamente,\n[Seu Nome]"
                )
            elif any(word in content_lower for word in ['projeto', 'project', 'proposta', 'desenvolvimento']):
                return (
                    "Obrigado pelo contato.\n\n"
                    "Recebi as informações sobre o projeto e vou analisar os detalhes fornecidos. Retornarei com um feedback detalhado em até 2 dias úteis.\n\n"
                    "Caso tenha alguma dúvida adicional, fique à vontade para entrar em contato.\n\n"
                    "Atenciosamente,\n[Seu Nome]"
                )
            elif any(word in content_lower for word in ['relatorio', 'report', 'analise', 'documento']):
                return (
                    "Obrigado pelo envio.\n\n"
                    "Recebi o documento e vou proceder com a análise. Caso tenha alguma observação específica ou prazo para retorno, por favor me informe.\n\n"
                    "Retornarei com meus comentários em breve.\n\n"
                    "Atenciosamente,\n[Seu Nome]"
                )
            elif any(word in content_lower for word in ['prazo', 'deadline', 'entrega', 'urgente']):
                return (
                    "Obrigado pelo contato.\n\n"
                    "Entendi a urgência da solicitação e vou priorizar esta demanda. Retornarei com uma resposta o mais breve possível.\n\n"
                    "Caso precise de esclarecimentos adicionais, estou à disposição.\n\n"
                    "Atenciosamente,\n[Seu Nome]"
                )
            else:
                return (
                    "Obrigado pelo seu email.\n\n"
                    "Recebi sua mensagem e vou analisar as informações fornecidas. Retornarei com uma resposta detalhada em breve.\n\n"
                    "Caso seja urgente, não hesite em entrar em contato por telefone.\n\n"
                    "Atenciosamente,\n[Seu Nome]"
                )
        else:
            return (
                "Obrigado pelo contato.\n\n"
                "No momento, não tenho interesse na proposta apresentada. Caso tenha algo mais específico relacionado ao meu trabalho, fique à vontade para entrar em contato novamente.\n\n"
                "Para remover meu email de sua lista de contatos, responda com \"REMOVER\" no assunto.\n\n"
                "Atenciosamente,\n[Seu Nome]"
            )

    def generate_reasoning(self, category: str, found_keywords: List[str], method: str) -> str:
        if category == "Produtivo":
            reasoning = (
                f"Este email foi classificado como PRODUTIVO usando {method}.\n\n"
                f"Indicadores encontrados:\n"
                f"• {len(found_keywords)} palavras-chave relacionadas a trabalho e produtividade"
            )
            if found_keywords:
                reasoning += f"\n• Palavras identificadas: {', '.join(found_keywords[:5])}"
                if len(found_keywords) > 5:
                    reasoning += f" (e mais {len(found_keywords) - 5})"
            reasoning += (
                "\n\nA análise identificou termos associados a atividades profissionais, projetos, reuniões ou assuntos corporativos relevantes, indicando que este email requer atenção e resposta adequada."
            )
        else:
            reasoning = (
                f"Este email foi classificado como IMPRODUTIVO usando {method}.\n\n"
                f"Indicadores encontrados:\n"
                f"• {len(found_keywords)} palavras-chave relacionadas a spam/promoções"
            )
            if found_keywords:
                reasoning += f"\n• Palavras identificadas: {', '.join(found_keywords[:5])}"
                if len(found_keywords) > 5:
                    reasoning += f" (e mais {len(found_keywords) - 5})"
            reasoning += (
                "\n\nA análise identificou padrões típicos de emails promocionais, spam ou conteúdo não relacionado a atividades profissionais, sugerindo que pode ser tratado com menor prioridade."
            )
        return reasoning

classifier = EmailClassifier()

@app.route('/classify', methods=['POST'])
def classify_email():
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            logger.warning("Classification request missing content")
            return jsonify({'error': 'Email content is required'}), 400
        content = data['content']
        if len(content.strip()) < 10:
            logger.warning(f"Content too short: {len(content)} characters")
            return jsonify({'error': 'Email content too short for classification (minimum 10 characters)'}), 400
        source = data.get('source', 'unknown')
        filename = data.get('filename', 'N/A')
        logger.info(f"Classification request - Source: {source}, Filename: {filename}, Length: {len(content)}")
        result = classifier.classify_email(content)
        logger.info(f"Classification successful - Category: {result['category']}, Confidence: {result['confidence']:.2f}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Classification failed: {str(e)}", exc_info=True)
        return jsonify({'error': f'Classification failed: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    health_status = {
        'status': 'healthy',
        'service': 'Email Classifier API',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat(),
        'ai_model_enabled': classifier.use_ai_model,
        'classification_method': 'AI + NLP' if classifier.use_ai_model else 'Keywords + NLP'
    }
    logger.info("Health check requested")
    return jsonify(health_status)

@app.route('/info', methods=['GET'])
def serve_frontend():
    return jsonify({
        'service': 'Email Classifier API',
        'version': '2.0.0',
        'description': 'Sistema inteligente de classificação de emails com IA avançada',
        'features': [
            'Classificação por IA (Zero-Shot)',
            'Processamento NLP avançado',
            'Geração de respostas contextuais',
            'Análise de palavras-chave',
            'Suporte multilíngue (PT/EN)'
        ],
        'endpoints': {
            'POST /classify': 'Classify email content',
            'GET /health': 'Health check',
            'GET /': 'API information'
        },
        'example_request': {
            'content': 'Olá, gostaria de agendar uma reunião para discutir o projeto.',
            'source': 'text'
        },
        'ai_model_enabled': classifier.use_ai_model
    })

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    logger.info(f"Starting Email Classifier API on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"AI Model: {'Enabled' if classifier.use_ai_model else 'Disabled (using keywords)'}")
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)