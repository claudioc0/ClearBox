from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
import string
import logging
from typing import Dict, List, Tuple
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import RSLPStemmer
from datetime import datetime
from transformers import pipeline
import torch
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

nltk_data_dir = "/tmp/nltk_data"
os.makedirs(nltk_data_dir, exist_ok=True)
nltk.data.path.append(nltk_data_dir)

os.environ["TRANSFORMERS_CACHE"] = "/tmp/hf_cache"
os.environ["HF_DATASETS_CACHE"] = "/tmp/hf_cache"
os.environ["HF_HOME"] = "/tmp/hf_cache"

nltk_packages = ['punkt', 'stopwords', 'rslp']

for pkg in nltk_packages:
    try:
        nltk.data.find(pkg)
        logger.info(f"NLTK package '{pkg}' found.")
    except LookupError:
        logger.info(f"Downloading NLTK package '{pkg}' to {nltk_data_dir}...")
        nltk.download(pkg, download_dir=nltk_data_dir)



app = Flask(__name__, static_folder='../static', static_url_path='')
CORS(app)

@app.route('/')
def api_info():
    """Serve o arquivo principal do frontend."""
    return app.send_static_file('index.html')

class EmailClassifier:
    def __init__(self):
        self.stemmer = RSLPStemmer()
        self.stop_words = set(stopwords.words('portuguese') + stopwords.words('english'))
        
        # Initialize AI model for zero-shot classification
        self.ai_classifier = None
        self.use_ai_model = self._initialize_ai_model()
        
        # Keywords for fallback classification
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
        """Initialize the AI model for zero-shot classification"""
        try:
            logger.info("Initializing AI classification model...")
            # Usando o modelo  que é mais pequeno e adequado para o plano gratuito
            model_name = "valhalla/distilbart-mnli-12-3"
            self.ai_classifier = pipeline(
                "zero-shot-classification",
                model=model_name,
                device=-1  # Força o uso de CPU, mais estável no Heroku
            )
            
            logger.info(f"AI model '{model_name}' loaded successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to initialize AI model: {e}")
            logger.info("Falling back to keyword-based classification")
            return False

    def preprocess_text(self, text: str) -> List[str]:
        """Preprocess email text for classification"""
        text = text.lower()
        
        text = re.sub(r'[^a-záàâãéèêíïóôõöúçñ\s]', ' ', text)
        
        try:
            tokens = word_tokenize(text, language='portuguese')
        except LookupError:
            nltk.download('punkt', download_dir=nltk_data_dir)
            tokens = word_tokenize(text, language='portuguese')
        
        processed_tokens = []
        for token in tokens:
            if token not in self.stop_words and len(token) > 2:
                stemmed_token = self.stemmer.stem(token)
                processed_tokens.append(stemmed_token)
        
        return processed_tokens


    def classify_with_ai(self, content: str) -> Dict:
        """Classify email using AI model"""
        try:
            # RÓTULOS FINAIS E OTIMIZADOS
            candidate_labels = [
                "E-mail de trabalho sobre tarefa, projeto ou reunião",
                "E-mail de marketing, spam, propaganda ou anúncio"
            ]
            
            result = self.ai_classifier(content, candidate_labels, multi_label=False)
            
            # Adicione este log para depuração
            logger.info(f"AI Model Raw Output: {result}")
            
            top_label = result['labels'][0]
            confidence = result['scores'][0]
            
            if top_label == candidate_labels[0]:
                category = "Produtivo"
            else:
                category = "Improdutivo"
            
            tokens = self.preprocess_text(content)
            token_set = set(tokens)
            
            if category == "Produtivo":
                found_keywords = list(token_set.intersection(self.productive_keywords))
            else:
                found_keywords = list(token_set.intersection(self.unproductive_keywords))
            
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
        
        return {
            "category": category,
            "confidence": confidence,
            "method": "Keywords",
            "found_keywords": found_keywords[:10]  
        }


    def classify_email(self, content: str) -> Dict:
        """Main classification method with Hybrid Logic"""
        start_time = datetime.now()
        
        logger.info(f"Classifying email with {len(content)} characters")
        
        # PASSO 1: Classificação inicial com IA
        if self.use_ai_model:
            classification_result = self.classify_with_ai(content)
        else:
            classification_result = self.classify_with_keywords(content)
        
        # PASSO 2: LÓGICA HÍBRIDA (REDE DE SEGURANÇA)
        # Se a IA classificou como Produtivo, fazemos uma verificação final
        # para garantir que não seja um spam disfarçado.
        if classification_result["category"] == "Produtivo" and classification_result["method"] == "AI":
            # Palavras-chave de spam de alta certeza
            spam_triggers = {'investimento', 'renda', 'lucro', 'ganhar dinheiro', 'gratis', 'oportunidade unica', 'clique aqui', 'promocao'}
            content_lower = content.lower()
            
            # Se alguma palavra-gatilho de spam for encontrada...
            if any(trigger in content_lower for trigger in spam_triggers):
                logger.info("Hybrid Logic Triggered: AI classified as Productive, but spam keywords were found. Overriding to Improductive.")
                # Inverte a classificação para Improdutivo
                classification_result["category"] = "Improdutivo"
                # Inverte a confiança para refletir a certeza da regra
                classification_result["confidence"] = 0.90 
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
        """Generate appropriate response based on classification"""
        if category == "Produtivo":
            content_lower = content.lower()
            
            if any(word in content_lower for word in ['reuniao', 'meeting', 'encontro', 'agenda']):
                return """Obrigado pelo seu email.

Recebi sua solicitação de reunião e vou verificar minha agenda. Retornarei em breve com minha disponibilidade.

Caso seja urgente, não hesite em entrar em contato por telefone.

Atenciosamente,
[Seu Nome]"""
            
            elif any(word in content_lower for word in ['projeto', 'project', 'proposta', 'desenvolvimento']):
                return """Obrigado pelo contato.

Recebi as informações sobre o projeto e vou analisar os detalhes fornecidos. Retornarei com um feedback detalhado em até 2 dias úteis.

Caso tenha alguma dúvida adicional, fique à vontade para entrar em contato.

Atenciosamente,
[Seu Nome]"""
            
            elif any(word in content_lower for word in ['relatorio', 'report', 'analise', 'documento']):
                return """Obrigado pelo envio.

Recebi o documento e vou proceder com a análise. Caso tenha alguma observação específica ou prazo para retorno, por favor me informe.

Retornarei com meus comentários em breve.

Atenciosamente,
[Seu Nome]"""
            
            elif any(word in content_lower for word in ['prazo', 'deadline', 'entrega', 'urgente']):
                return """Obrigado pelo contato.

Entendi a urgência da solicitação e vou priorizar esta demanda. Retornarei com uma resposta o mais breve possível.

Caso precise de esclarecimentos adicionais, estou à disposição.

Atenciosamente,
[Seu Nome]"""
            
            else:
                return """Obrigado pelo seu email.

Recebi sua mensagem e vou analisar as informações fornecidas. Retornarei com uma resposta detalhada em breve.

Caso seja urgente, não hesite em entrar em contato por telefone.

Atenciosamente,
[Seu Nome]"""
        
        else:  # Improdutivo
            return """Obrigado pelo contato.

No momento, não tenho interesse na proposta apresentada. Caso tenha algo mais específico relacionado ao meu trabalho, fique à vontade para entrar em contato novamente.

Para remover meu email de sua lista de contatos, responda com "REMOVER" no assunto.

Atenciosamente,
[Seu Nome]"""

    def generate_reasoning(self, category: str, found_keywords: List[str], method: str) -> str:
        """Generate reasoning for the classification"""
        
        if category == "Produtivo":
            reasoning = f"""Este email foi classificado como PRODUTIVO usando {method}.

Indicadores encontrados:
• {len(found_keywords)} palavras-chave relacionadas a trabalho e produtividade"""
            
            if found_keywords:
                reasoning += f"\n• Palavras identificadas: {', '.join(found_keywords[:5])}"
                if len(found_keywords) > 5:
                    reasoning += f" (e mais {len(found_keywords) - 5})"
            
            reasoning += "\n\nA análise identificou termos associados a atividades profissionais, projetos, reuniões ou assuntos corporativos relevantes, indicando que este email requer atenção e resposta adequada."
        
        else:
            reasoning = f"""Este email foi classificado como IMPRODUTIVO usando {method}.

Indicadores encontrados:
• {len(found_keywords)} palavras-chave relacionadas a spam/promoções"""
            
            if found_keywords:
                reasoning += f"\n• Palavras identificadas: {', '.join(found_keywords[:5])}"
                if len(found_keywords) > 5:
                    reasoning += f" (e mais {len(found_keywords) - 5})"
            
            reasoning += "\n\nA análise identificou padrões típicos de emails promocionais, spam ou conteúdo não relacionado a atividades profissionais, sugerindo que pode ser tratado com menor prioridade."
        
        return reasoning

classifier = EmailClassifier()

@app.route('/classify', methods=['POST'])
def classify_email():
    """Endpoint to classify email content"""
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
    """Health check endpoint"""
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
    """Root endpoint with API information"""
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