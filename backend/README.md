# Email Classifier Backend

Sistema backend em Python para classificação inteligente de emails usando processamento de linguagem natural (NLP).

## Funcionalidades

- **Classificação Automática**: Categoriza emails como "Produtivo" ou "Improdutivo"
- **Processamento NLP**: Utiliza NLTK para pré-processamento de texto
- **Geração de Respostas**: Sugere respostas automáticas personalizadas
- **API RESTful**: Interface HTTP para integração com frontend
- **Análise Detalhada**: Fornece reasoning para cada classificação

## Instalação

1. **Instalar dependências**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Executar o servidor**:
```bash
python app.py
```

O servidor estará disponível em `http://localhost:8000`

## Endpoints da API

### POST /classify
Classifica o conteúdo de um email.

**Request Body**:
```json
{
  "content": "Texto do email para classificar",
  "source": "text"
}
```

**Response**:
```json
{
  "category": "Produtivo",
  "confidence": 0.85,
  "suggestedResponse": "Resposta sugerida...",
  "reasoning": "Explicação da classificação...",
  "processingTime": 0.15
}
```

### GET /health
Verifica o status do serviço.

### GET /
Informações sobre a API.

## Algoritmo de Classificação

O sistema utiliza:

1. **Pré-processamento NLP**:
   - Tokenização
   - Remoção de stop words
   - Stemming (RSLP para português)
   - Limpeza de caracteres especiais

2. **Classificação por Keywords**:
   - Palavras-chave produtivas: reunião, projeto, prazo, etc.
   - Palavras-chave improdutivas: spam, promoção, desconto, etc.

3. **Cálculo de Confiança**:
   - Baseado na proporção de keywords encontradas
   - Valores entre 0.5 e 0.95

4. **Geração de Respostas**:
   - Respostas contextuais baseadas no tipo de email
   - Templates personalizados para diferentes cenários

## Tecnologias Utilizadas

- **Flask**: Framework web
- **NLTK**: Processamento de linguagem natural
- **Flask-CORS**: Suporte a CORS para integração frontend
- **Python 3.8+**: Linguagem de programação

## Melhorias Futuras

- Integração com APIs de IA (OpenAI, Hugging Face)
- Machine Learning com modelos treinados
- Suporte a múltiplos idiomas
- Cache de resultados
- Métricas de performance