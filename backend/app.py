from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
import logging
from typing import Dict, List
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import RSLPStemmer
from datetime import datetime
from transformers import pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure NLTK data directory
nltk_data_dir = "/tmp/nltk_data"
os.makedirs(nltk_data_dir, exist_ok=True)
nltk.data.path.append(nltk_data_dir)

# Ensure required NLTK packages are installed
nltk_packages = ['punkt', 'stopwords', 'rslp']
for pkg in nltk_packages:
    try:
        nltk.data.find(pkg)
        logger.info(f"NLTK package '{pkg}' found.")
    except LookupError:
        logger.info(f"Downloading NLTK package '{pkg}' to {nltk_data_dir}...")
        nltk.download(pkg, download_dir=nltk_data_dir)

# Initialize Flask
app = Flask(__name__, static_folder='../static', static_url_path='')
CORS(app)

# ----- Email Classifier -----
class EmailClassifier:
    def __init__(self):
        self.stemmer = RSLPStemmer()
        self.stop_words = set(stopwords.words('portuguese') + stopwords.words('english'))
        
        self.ai_classifier = None
        self.use_ai_model = self._initialize_ai_model()
        
        # Keywords for fallback
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
        
        logger.info(f"EmailClassifier initialized. AI Model: {'Enabled' if self.use_ai_model else 'Disabled'}")

    def _initialize_ai_model(self):
        """Initialize zero-shot AI model"""
        try:
            logger.info("Initializing AI classification model...")
            model_name = "facebook/bart-large-mnli"
            self.ai_classifier = pipeline("zero-shot-classification", model=model_name, device=-1)
            logger.info(f"AI model '{model_name}' loaded successfully")
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize AI model: {e}")
            logger.info("Falling back to keyword-based classification")
            return False

    def preprocess_text(self, text: str) -> List[str]:
        """Preprocess text for classification"""
        text = text.lower()
        text = re.sub(r'[^a-záàâãéèêíïóôõöúçñ\s]', ' ', text)
        tokens = word_tokenize(text, language='portuguese')
        return [self.stemmer.stem(token) for token in tokens
                if token not in self.stop_words and len(token) > 2]

    def classify_with_ai(self, content: str) -> Dict:
        """Classify email using AI"""
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
            token_set = set(tokens)
            found_keywords = list(token_set.intersection(
                self.productive_keywords if category == "Produtivo" else self.unproductive_keywords
            ))
            
            return {"category": category, "confidence": confidence,
                    "method": "AI", "found_keywords": found_keywords[:10]}
        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            return self.classify_with_keywords(content)

    def classify_with_keywords(self, content: str) -> Dict:
        """Fallback keyword-based classification"""
        tokens = self.preprocess_text(content)
        token_set = set(tokens)
        found_productive = list(token_set.intersection(self.productive_keywords))
        found_unproductive = list(token_set.intersection(self.unproductive_keywords))
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
        
        return {"category": category, "confidence": confidence,
                "method": "Keywords", "found_keywords": found_keywords[:10]}

    def classify_email(self, content: str) -> Dict:
        """Hybrid classification logic"""
        start_time = datetime.now()
        classification_result = (self.classify_with_ai(content)
                                 if self.use_ai_model else self.classify_with_keywords(content))
        
        # Hybrid Rule: override AI if spam triggers found
        if classification_result["category"] == "Produtivo" and classification_result["method"] == "AI":
            spam_triggers = {'investimento', 'renda', 'lucro', 'ganhar dinheiro', 'gratis',
                             'oportunidade unica', 'clique aqui', 'promocao'}
            if any(trigger in content.lower() for trigger in spam_triggers):
                logger.info("Hybrid logic triggered: AI Productive overridden to Improdutivo")
                classification_result.update({"category": "Improdutivo",
                                              "confidence": 0.90,
                                              "method": "AI + Hybrid Rule"})
        
        suggested_response = self.generate_response(classification_result["category"], content)
        reasoning = self.generate_reasoning(classification_result["category"],
                                            classification_result["found_keywords"],
                                            classification_result["method"])
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
        
        logger.info(f"Classification completed: {result['category']} ({result['confidence']:.2f}) "
                    f"in {processing_time:.2f}s using {result['classificationMethod']}")
        return result

    def generate_response(self, category: str, content: str) -> str:
        """Generate suggested response"""
        content_lower = content.lower()
        if category == "Produtivo":
            if any(word in content_lower for word in ['reuniao', 'meeting', 'encontro', 'agenda']):
                return "Obrigado pelo seu email. Responderei sobre a reunião em breve."
            elif any(word in content_lower for word in ['projeto', 'project', 'proposta', 'desenvolvimento']):
                return "Recebi o projeto/proposta e retornarei em até 2 dias úteis."
            elif any(word in content_lower for word in ['relatorio', 'report', 'analise', 'documento']):
                return "Recebi o documento e farei a análise. Retornarei com comentários."
            elif any(word in content_lower for word in ['prazo', 'deadline', 'entrega', 'urgente']):
                return "Entendi a urgência e priorizarei esta demanda."
            else:
                return "Recebi sua mensagem e retornarei com uma resposta detalhada em breve."
        else:
            return "Este email é considerado improdutivo/spam. Não é necessário responder."

    def generate_reasoning(self, category: str, found_keywords: List[str], method: str) -> str:
        """Generate reasoning for classification"""
        reasoning = f"Este email foi classificado como {category.upper()} usando {method}.\n"
        reasoning += f"Indicadores encontrados: {len(found_keywords)} palavras-chave."
        if found_keywords:
            reasoning += f"\nPalavras identificadas: {', '.join(found_keywords[:5])}"
            if len(found_keywords) > 5:
                reasoning += f" (e mais {len(found_keywords) - 5})"
        return reasoning

# Initialize classifier
classifier = EmailClassifier()

# ----- Routes -----
@app.route('/classify', methods=['POST'])
def classify_email_route():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Email content is required'}), 400
    content = data['content']
    if len(content.strip()) < 10:
        return jsonify({'error': 'Email content too short (minimum 10 chars)'}), 400
    result = classifier.classify_email(content)
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Email Classifier API',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat(),
        'ai_model_enabled': classifier.use_ai_model
    })

@app.route('/info', methods=['GET'])
def api_info():
    return jsonify({
        'service': 'Email Classifier API',
        'version': '2.0.0',
        'description': 'Sistema inteligente de classificação de emails com IA',
        'endpoints': {
            'POST /classify': 'Classify email content',
            'GET /health': 'Health check',
            'GET /info': 'API information'
        },
        'ai_model_enabled': classifier.use_ai_model
    })

@app.route('/', methods=['GET'])
def serve_frontend():
    return app.send_static_file('index.html')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ----- Main -----
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    logger.info(f"Starting Email Classifier API on port {port}, Debug={debug}, AI Model={'Enabled' if classifier.use_ai_model else 'Disabled'}")
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
