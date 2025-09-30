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
import torch

# Configure logging para imprimir no terminal
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Download NLTK data de forma consolidada
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('stemmers/rslp')
    nltk.data.find('tokenizers/punkt_tab')
except LookupError as e:
    # Extrai o nome do pacote do erro para um download mais limpo
    package_name = re.search(r"'(.*?)'", str(e)).group(1).split('/')[-1]
    logger.info(f"Downloading required NLTK package: '{package_name}'")
    nltk.download(package_name)


app = Flask(__name__)
CORS(app)

class EmailClassifier:
    def __init__(self):
        self.stemmer = RSLPStemmer()
        self.stop_words = set(stopwords.words('portuguese') + stopwords.words('english'))
        
        self.ai_classifier = None
        self.use_ai_model = self._initialize_ai_model()
        
        # Keywords para fallback e lógica híbrida
        self.productive_keywords = {'reuniao', 'projeto', 'prazo', 'entrega', 'relatorio', 'apresentacao', 'trabalho', 'tarefa'}
        self.unproductive_keywords = {'spam', 'promocao', 'desconto', 'oferta', 'gratis', 'ganhe', 'premio', 'clique', 'oportunidade', 'dinheiro'}
        
        logger.info(f"EmailClassifier initialized. AI Model: {'Enabled' if self.use_ai_model else 'Disabled'}")

    def _initialize_ai_model(self):
        try:
            logger.info("Initializing AI classification model...")
            model_name = "MoritzLaurer/deberta-v3-base-mnli-fever-anli"
            self.ai_classifier = pipeline(
                "zero-shot-classification",
                model=model_name,
                device=0 if torch.cuda.is_available() else -1
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
        return [self.stemmer.stem(token) for token in tokens if token not in self.stop_words and len(token) > 2]

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
            token_set = set(tokens)
            keyword_set = self.productive_keywords if category == "Produtivo" else self.unproductive_keywords
            found_keywords = list(token_set.intersection(keyword_set))
            
            return {
                "category": category,
                "confidence": confidence,
                "method": "AI",
                "found_keywords": found_keywords[:10]
            }
        except Exception as e:
            logger.error(f"AI classification failed: {e}", exc_info=True)
            return self.classify_with_keywords(content)

    def classify_with_keywords(self, content: str) -> Dict:
        tokens = self.preprocess_text(content)
        token_set = set(tokens)
        productive_score = len(token_set.intersection(self.productive_keywords))
        unproductive_score = len(token_set.intersection(self.unproductive_keywords))
        
        if productive_score > unproductive_score:
            category = "Produtivo"
            confidence = min(0.95, max(0.6, (productive_score + 1) / (productive_score + unproductive_score + 2)))
        elif unproductive_score > productive_score:
            category = "Improdutivo"
            confidence = min(0.95, max(0.6, (unproductive_score + 1) / (productive_score + unproductive_score + 2)))
        else:
            category = "Produtivo"
            confidence = 0.5
        
        keyword_set = self.productive_keywords if category == "Produtivo" else self.unproductive_keywords
        found_keywords = list(token_set.intersection(keyword_set))
        
        return {"category": category, "confidence": confidence, "method": "Keywords", "found_keywords": found_keywords[:10]}

    def classify_email(self, content: str) -> Dict:
        start_time = datetime.now()
        
        if self.use_ai_model:
            classification_result = self.classify_with_ai(content)
        else:
            classification_result = self.classify_with_keywords(content)
        
        if classification_result["category"] == "Produtivo" and classification_result["method"].startswith("AI"):
            spam_triggers = {'investimento', 'renda', 'lucro', 'ganhar dinheiro', 'gratis', 'oportunidade unica', 'clique aqui', 'promocao'}
            content_lower = content.lower()
            if any(trigger in content_lower for trigger in spam_triggers):
                logger.info("Hybrid Logic Triggered: Overriding AI result to Improductive.")
                classification_result["category"] = "Improdutivo"
                classification_result["confidence"] = 0.90 
                classification_result["method"] = "AI + Hybrid Rule"

        suggested_response = self.generate_response(classification_result["category"], content)
        reasoning = self.generate_reasoning(
            classification_result["category"], classification_result["found_keywords"], classification_result["method"]
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
        
        logger.info(f"Classification completed: {result['category']} ({result['confidence']:.2f} confidence) in {processing_time:.2f}s using {result['classificationMethod']}")
        return result

    def generate_response(self, category: str, content: str) -> str:
        if category == "Produtivo":
            return "Obrigado, recebemos sua mensagem e retornaremos em breve."
        else:
            return "Obrigado pelo contato, mas não temos interesse no momento."

    def generate_reasoning(self, category: str, found_keywords: List[str], method: str) -> str:
        reasoning_intro = f"Este email foi classificado como {category.upper()} usando {method}."
        keywords_text = f"Palavras-chave influentes: {', '.join(found_keywords)}" if found_keywords else "Nenhuma palavra-chave específica foi destacada."
        return f"{reasoning_intro}\n{keywords_text}"

classifier = EmailClassifier()

@app.route('/classify', methods=['POST'])
def classify_email_route():
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Email content is required'}), 400
        content = data['content']
        if len(content.strip()) < 10:
            return jsonify({'error': 'Email content too short'}), 400
        
        result = classifier.classify_email(content)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in /classify route: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'ai_model_enabled': classifier.use_ai_model})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False, ssl_context='adhoc')

