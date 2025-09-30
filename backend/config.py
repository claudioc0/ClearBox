"""
Configuration file for Email Classifier
"""
import os
from typing import Set

class Config:
    """Main configuration class"""
    
    # API Configuration
    API_HOST = os.environ.get('API_HOST', '0.0.0.0')
    API_PORT = int(os.environ.get('PORT', 8000))
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # AI Model Configuration
    AI_MODEL_NAME = os.environ.get('AI_MODEL_NAME', 'facebook/bart-large-mnli')
    USE_GPU = os.environ.get('USE_GPU', 'auto')  # auto, true, false
    
    # Classification Configuration
    MIN_CONTENT_LENGTH = int(os.environ.get('MIN_CONTENT_LENGTH', 10))
    MAX_KEYWORDS_DISPLAY = int(os.environ.get('MAX_KEYWORDS_DISPLAY', 10))
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'email_classifier.log')
    
    # Keywords for classification (can be overridden via environment)
    PRODUCTIVE_KEYWORDS: Set[str] = {
        # Portuguese keywords
        'reuniao', 'projeto', 'prazo', 'entrega', 'relatorio', 'apresentacao',
        'trabalho', 'tarefa', 'responsabilidade', 'objetivo', 'meta', 'agenda',
        'cronograma', 'planejamento', 'estrategia', 'desenvolvimento', 'analise',
        'proposta', 'orcamento', 'contrato', 'negociacao', 'cliente', 'fornecedor',
        'colaboracao', 'equipe', 'time', 'departamento', 'gerencia', 'diretoria',
        'solucao', 'problema', 'discussao', 'feedback', 'revisao', 'aprovacao',
        'documento', 'arquivo', 'dados', 'informacao', 'resultado', 'status',
        
        # English keywords
        'meeting', 'project', 'deadline', 'delivery', 'report', 'presentation',
        'work', 'task', 'responsibility', 'objective', 'goal', 'agenda',
        'schedule', 'planning', 'strategy', 'development', 'analysis',
        'proposal', 'budget', 'contract', 'negotiation', 'client', 'supplier',
        'collaboration', 'team', 'department', 'management', 'direction',
        'solution', 'problem', 'discussion', 'feedback', 'review', 'approval',
        'document', 'file', 'data', 'information', 'result', 'status'
    }
    
    UNPRODUCTIVE_KEYWORDS: Set[str] = {
        # Portuguese keywords
        'spam', 'promocao', 'desconto', 'oferta', 'gratis', 'ganhe', 'premio',
        'clique', 'urgente', 'limitado', 'exclusivo', 'oportunidade', 'dinheiro',
        'renda', 'investimento', 'lucro', 'ganhar', 'facil', 'rapido',
        'compre', 'venda', 'barato', 'economize', 'sorteio', 'concurso',
        'cadastre', 'inscreva', 'participe', 'aproveite', 'imperdivel',
        
        # English keywords
        'promotion', 'discount', 'offer', 'free', 'win', 'prize', 'lottery',
        'click', 'urgent', 'limited', 'exclusive', 'opportunity', 'money',
        'income', 'investment', 'profit', 'earn', 'easy', 'quick',
        'buy', 'sale', 'cheap', 'save', 'contest', 'giveaway',
        'register', 'subscribe', 'participate', 'enjoy', 'unmissable'
    }
    
    @classmethod
    def load_keywords_from_env(cls):
        """Load keywords from environment variables if provided"""
        productive_env = os.environ.get('PRODUCTIVE_KEYWORDS')
        if productive_env:
            cls.PRODUCTIVE_KEYWORDS.update(productive_env.split(','))
        
        unproductive_env = os.environ.get('UNPRODUCTIVE_KEYWORDS')
        if unproductive_env:
            cls.UNPRODUCTIVE_KEYWORDS.update(unproductive_env.split(','))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    
    # Production-specific settings
    API_HOST = '0.0.0.0'
    USE_GPU = 'false'  # Disable GPU in production for stability

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    MIN_CONTENT_LENGTH = 5  # Lower threshold for testing

# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name: str = None) -> Config:
    """Get configuration based on environment"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config_map.get(config_name, DevelopmentConfig)