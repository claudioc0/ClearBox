const CONFIG = {
    API_URL: '/classify',
    HEALTH_URL: '/health',
    MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
    MIN_TEXT_LENGTH: 10,
    TOAST_DURATION: 5000,
    HISTORY_KEY: 'email-classifier-history',
    THEME_KEY: 'email-classifier-theme',
    MAX_HISTORY_ITEMS: 10,
    
    SELECTORS: {
        dropZone: '#drop-zone',
        fileInput: '#file-input',
        fileInfo: '#file-info',
        fileName: '#file-name',
        emailText: '#email-text',
        submitText: '#submit-text',
        charCount: '#char-count',
        loadingContainer: '#loading-container',
        resultContainer: '#result-container',
        resultContent: '#result-content',
        errorContainer: '#error-container',
        errorMessage: '#error-message',
        historySection: '#history-section',
        historyList: '#history-list',
        clearHistory: '#clear-history',
        themeToggle: '#theme-toggle',
        toastContainer: '#toast-container'
    }
};

class EmailClassifier {
    constructor() {
        this.isProcessing = false;
        this.dragCounter = 0;
        this.history = this.loadHistory();
        this.init();
    }

    init() {
        this.initTheme();
        this.setupEventListeners();
        this.renderHistory();
        this.checkAPIHealth();
    }

    initTheme() {
        const savedTheme = localStorage.getItem(CONFIG.THEME_KEY);
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const theme = savedTheme || (prefersDark ? 'dark' : 'light');
        
        this.setTheme(theme);
        this.updateThemeToggleIcon(theme);
    }

    setTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
        localStorage.setItem(CONFIG.THEME_KEY, theme);
    }

    updateThemeToggleIcon(theme) {
        const darkIcon = document.getElementById('theme-toggle-dark-icon');
        const lightIcon = document.getElementById('theme-toggle-light-icon');
        
        if (theme === 'dark') {
            darkIcon.classList.add('hidden');
            lightIcon.classList.remove('hidden');
        } else {
            darkIcon.classList.remove('hidden');
            lightIcon.classList.add('hidden');
        }
    }

    setupEventListeners() {
        document.addEventListener('click', this.handleDocumentClick.bind(this));
        document.addEventListener('change', this.handleDocumentChange.bind(this));
        document.addEventListener('input', this.handleDocumentInput.bind(this));
        document.addEventListener('keydown', this.handleDocumentKeydown.bind(this));
        
        this.setupDragAndDrop();
    }

    handleDocumentClick(event) {
        const target = event.target;
        const closest = target.closest.bind(target);
        
        if (closest('#theme-toggle')) {
            this.toggleTheme();
        }
        
        else if (closest(CONFIG.SELECTORS.dropZone)) {
            document.querySelector(CONFIG.SELECTORS.fileInput).click();
        }
        
        else if (closest(CONFIG.SELECTORS.submitText)) {
            this.handleTextSubmit();
        }
        
        else if (closest('.copy-response-btn')) {
            this.copyResponse(target);
        }
        
        else if (closest('.new-classification-btn')) {
            this.resetInterface();
        }
        
        else if (closest(CONFIG.SELECTORS.clearHistory)) {
            this.confirmClearHistory();
        }
        
        else if (closest('.history-item')) {
            this.loadHistoryItem(target.closest('.history-item'));
        }
        
        else if (closest('.toast-close')) {
            this.closeToast(target.closest('.toast'));
        }
    }

    handleDocumentChange(event) {
        const target = event.target;
        
        if (target.matches(CONFIG.SELECTORS.fileInput)) {
            const files = target.files;
            if (files && files.length > 0) {
                this.handleFile(files[0]);
            }
        }
    }

    handleDocumentInput(event) {
        const target = event.target;
        
        if (target.matches(CONFIG.SELECTORS.emailText)) {
            this.updateCharCount();
        }
    }

    handleDocumentKeydown(event) {
        const target = event.target;
        
        if (target.matches(CONFIG.SELECTORS.emailText) && event.ctrlKey && event.key === 'Enter') {
            event.preventDefault();
            const submitBtn = document.querySelector(CONFIG.SELECTORS.submitText);
            if (!submitBtn.disabled) {
                this.handleTextSubmit();
            }
        }
    }

    setupDragAndDrop() {
        const dropZone = document.querySelector(CONFIG.SELECTORS.dropZone);
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                this.dragCounter++;
                dropZone.classList.add('drag-over');
            }, false);
        });

        dropZone.addEventListener('dragleave', () => {
            this.dragCounter--;
            if (this.dragCounter === 0) {
                dropZone.classList.remove('drag-over');
            }
        }, false);

        dropZone.addEventListener('drop', (e) => {
            this.dragCounter = 0;
            dropZone.classList.remove('drag-over');
            
            const files = e.dataTransfer?.files;
            if (files && files.length > 0) {
                this.handleFile(files[0]);
            }
        }, false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    toggleTheme() {
        const isDark = document.documentElement.classList.contains('dark');
        const newTheme = isDark ? 'light' : 'dark';
        this.setTheme(newTheme);
        this.updateThemeToggleIcon(newTheme);
    }

    updateCharCount() {
        const textarea = document.querySelector(CONFIG.SELECTORS.emailText);
        const charCount = document.querySelector(CONFIG.SELECTORS.charCount);
        const submitBtn = document.querySelector(CONFIG.SELECTORS.submitText);
        
        const text = textarea.value.trim();
        charCount.textContent = text.length.toString();
        
        submitBtn.disabled = text.length < CONFIG.MIN_TEXT_LENGTH;
    }

    async handleFile(file) {
        const validTypes = ['text/plain', 'application/pdf'];
        if (!validTypes.includes(file.type)) {
            this.showToast('Tipo de arquivo não suportado. Use apenas arquivos .txt ou .pdf', 'error');
            return;
        }

        if (file.size > CONFIG.MAX_FILE_SIZE) {
            this.showToast('Arquivo muito grande. Tamanho máximo: 10MB', 'error');
            return;
        }

        const fileName = document.querySelector(CONFIG.SELECTORS.fileName);
        const fileInfo = document.querySelector(CONFIG.SELECTORS.fileInfo);
        
        fileName.textContent = `${file.name} (${this.formatFileSize(file.size)})`;
        fileInfo.classList.remove('hidden');

        try {
            const text = await this.extractTextFromFile(file);
            
            if (text.trim().length < CONFIG.MIN_TEXT_LENGTH) {
                this.showToast('Conteúdo do arquivo muito curto para classificação', 'error');
                return;
            }
            
            const emailData = {
                content: text,
                source: 'file',
                filename: file.name
            };
            
            await this.processEmail(emailData);
        } catch (error) {
            this.showToast('Erro ao processar arquivo: ' + error.message, 'error');
        }
    }

    async extractTextFromFile(file) {
        if (file.type === 'text/plain') {
            return await file.text();
        } else if (file.type === 'application/pdf') {
            return await this.extractPDFText(file);
        } else {
            throw new Error('Formato de arquivo não suportado');
        }
    }

    async extractPDFText(file) {
        try {
            const arrayBuffer = await file.arrayBuffer();
            const pdf = await pdfjsLib.getDocument(arrayBuffer).promise;
            let fullText = '';
            
            for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const textContent = await page.getTextContent();
                const pageText = textContent.items.map(item => item.str).join(' ');
                fullText += pageText + '\n';
            }
            
            return fullText;
        } catch (error) {
            throw new Error('Erro ao extrair texto do PDF: ' + error.message);
        }
    }

    async handleTextSubmit() {
        if (this.isProcessing) return;

        const textarea = document.querySelector(CONFIG.SELECTORS.emailText);
        const text = textarea.value.trim();
        
        if (text.length < CONFIG.MIN_TEXT_LENGTH) {
            this.showToast('Texto muito curto para classificação', 'error');
            return;
        }

        try {
            const emailData = {
                content: text,
                source: 'text'
            };
            
            await this.processEmail(emailData);
            
            textarea.value = '';
            this.updateCharCount();
        } catch (error) {
            this.showToast('Erro ao processar texto: ' + error.message, 'error');
        }
    }

    async processEmail(emailData) {
        if (this.isProcessing) return;

        try {
            this.isProcessing = true;
            this.showLoading();
            
            const result = await this.classifyEmail(emailData);
            this.showResult(result);
            this.addToHistory(emailData, result);
        } catch (error) {
            this.showError('Falha na classificação do email: ' + error.message);
        } finally {
            this.isProcessing = false;
            this.hideLoading();
        }
    }

    async classifyEmail(emailData) {
        try {
            const response = await fetch(CONFIG.API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(emailData),
            });

            if (!response.ok) {
                let errorMessage = `HTTP error! status: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('API Error:', error);
            
            this.showToast('Erro na API: ' + error.message + '. Usando resposta simulada.', 'warning');
            
            return this.getMockResponse(emailData);
        }
    }

    getMockResponse(emailData) {
        const content = emailData.content.toLowerCase();
        
        const productiveKeywords = [
            'reunião', 'projeto', 'prazo', 'entrega', 'relatório', 'apresentação',
            'meeting', 'project', 'deadline', 'delivery', 'report', 'presentation',
            'trabalho', 'tarefa', 'responsabilidade', 'objetivo', 'meta', 'agenda',
            'cronograma', 'planejamento', 'estratégia', 'desenvolvimento', 'análise'
        ];
        
        const unproductiveKeywords = [
            'spam', 'promoção', 'desconto', 'oferta', 'grátis', 'ganhe', 'prêmio',
            'promotion', 'discount', 'offer', 'free', 'win', 'prize', 'lottery',
            'clique aqui', 'click here', 'urgente', 'urgent', 'limitado', 'exclusivo'
        ];

        const foundProductiveKeywords = productiveKeywords.filter(keyword => content.includes(keyword));
        const foundUnproductiveKeywords = unproductiveKeywords.filter(keyword => content.includes(keyword));

        const productiveScore = foundProductiveKeywords.length;
        const unproductiveScore = foundUnproductiveKeywords.length;

        const isProductive = productiveScore > unproductiveScore;
        const confidence = Math.max(0.6, Math.min(0.95, (Math.max(productiveScore, unproductiveScore) + 2) / 5));

        const category = isProductive ? 'Produtivo' : 'Improdutivo';
        
        const suggestedResponse = this.generateResponse(category, content);
        const reasoning = this.generateReasoning(category, foundProductiveKeywords, foundUnproductiveKeywords);

        return {
            category,
            confidence,
            suggestedResponse,
            reasoning,
            processingTime: Math.random() * 2 + 1,
            highlightedKeywords: isProductive ? foundProductiveKeywords : foundUnproductiveKeywords,
            originalContent: emailData.content
        };
    }

    generateResponse(category, content) {
        if (category === 'Produtivo') {
            if (content.includes('reunião') || content.includes('meeting')) {
                return `Obrigado pelo seu email.

Recebi sua solicitação de reunião e vou verificar minha agenda. Retornarei em breve com minha disponibilidade.

Caso seja urgente, não hesite em entrar em contato por telefone.

Atenciosamente,
[Seu Nome]`;
            } else if (content.includes('projeto') || content.includes('project')) {
                return `Obrigado pelo contato.

Recebi as informações sobre o projeto e vou analisar os detalhes fornecidos. Retornarei com um feedback detalhado em até 2 dias úteis.

Caso tenha alguma dúvida adicional, fique à vontade para entrar em contato.

Atenciosamente,
[Seu Nome]`;
            } else {
                return `Obrigado pelo seu email.

Recebi sua mensagem e vou analisar as informações fornecidas. Retornarei com uma resposta detalhada em breve.

Caso seja urgente, não hesite em entrar em contato por telefone.

Atenciosamente,
[Seu Nome]`;
            }
        } else {
            return `Obrigado pelo contato.

No momento, não tenho interesse na proposta apresentada. Caso tenha algo mais específico relacionado ao meu trabalho, fique à vontade para entrar em contato novamente.

Para remover meu email de sua lista de contatos, responda com "REMOVER" no assunto.

Atenciosamente,
[Seu Nome]`;
        }
    }

    generateReasoning(category, productiveKeywords, unproductiveKeywords) {
        if (category === 'Produtivo') {
            return `Este email foi classificado como PRODUTIVO baseado na análise de linguagem natural.

Palavras-chave identificadas: ${productiveKeywords.length > 0 ? productiveKeywords.join(', ') : 'termos relacionados a trabalho'}

A análise identificou termos associados a atividades profissionais, projetos, reuniões ou assuntos corporativos relevantes, indicando que este email requer atenção e resposta adequada.`;
        } else {
            return `Este email foi classificado como IMPRODUTIVO baseado na análise de linguagem natural.

Palavras-chave identificadas: ${unproductiveKeywords.length > 0 ? unproductiveKeywords.join(', ') : 'termos promocionais'}

A análise identificou padrões típicos de emails promocionais, spam ou conteúdo não relacionado a atividades profissionais, sugerindo que pode ser tratado com menor prioridade.`;
        }
    }

    showLoading() {
        const loadingContainer = document.querySelector(CONFIG.SELECTORS.loadingContainer);
        const resultContainer = document.querySelector(CONFIG.SELECTORS.resultContainer);
        const errorContainer = document.querySelector(CONFIG.SELECTORS.errorContainer);

        loadingContainer.classList.remove('hidden');
        resultContainer.classList.add('hidden');
        errorContainer.classList.add('hidden');
    }

    hideLoading() {
        const loadingContainer = document.querySelector(CONFIG.SELECTORS.loadingContainer);
        loadingContainer.classList.add('hidden');
    }

    showResult(result) {
        const container = document.querySelector(CONFIG.SELECTORS.resultContainer);
        const content = document.querySelector(CONFIG.SELECTORS.resultContent);
        const errorContainer = document.querySelector(CONFIG.SELECTORS.errorContainer);

        errorContainer.classList.add('hidden');

        container.classList.remove('hidden');

        this.renderResult(content, result);
    }

    renderResult(container, result) {
        container.innerHTML = '';
        
        const isProductive = result.category === 'Produtivo';
        const categoryColor = isProductive ? 'green' : 'red';
        
        const mainDiv = document.createElement('div');
        mainDiv.className = 'space-y-6';
        
        const classificationDiv = this.createClassificationSection(result, categoryColor);
        mainDiv.appendChild(classificationDiv);
        
        const confidenceDiv = this.createConfidenceSection(result);
        mainDiv.appendChild(confidenceDiv);
        
        const responseDiv = this.createResponseSection(result);
        mainDiv.appendChild(responseDiv);
        
        if (result.reasoning) {
            const analysisDiv = this.createAnalysisSection(result);
            mainDiv.appendChild(analysisDiv);
        }
        
        if (result.highlightedKeywords && result.originalContent) {
            const highlightedDiv = this.createHighlightedContentSection(result);
            mainDiv.appendChild(highlightedDiv);
        }
        
        const actionsDiv = this.createActionButtons();
        mainDiv.appendChild(actionsDiv);
        
        container.appendChild(mainDiv);
    }

    createClassificationSection(result, categoryColor) {
        const div = document.createElement('div');
        div.className = `bg-${categoryColor}-50 dark:bg-${categoryColor}-900/20 border border-${categoryColor}-200 dark:border-${categoryColor}-800 rounded-lg p-4`;
        
        const headerDiv = document.createElement('div');
        headerDiv.className = 'flex items-center mb-2';
        
        const icon = document.createElement('svg');
        icon.className = `w-5 h-5 text-${categoryColor}-600 dark:text-${categoryColor}-400 mr-2`;
        icon.setAttribute('fill', 'none');
        icon.setAttribute('stroke', 'currentColor');
        icon.setAttribute('viewBox', '0 0 24 24');
        
        const iconPath = document.createElement('path');
        iconPath.setAttribute('stroke-linecap', 'round');
        iconPath.setAttribute('stroke-linejoin', 'round');
        iconPath.setAttribute('stroke-width', '2');
        iconPath.setAttribute('d', result.category === 'Produtivo' 
            ? 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
            : 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'
        );
        
        icon.appendChild(iconPath);
        headerDiv.appendChild(icon);
        
        const title = document.createElement('h4');
        title.className = `font-semibold text-${categoryColor}-800 dark:text-${categoryColor}-200`;
        title.textContent = 'Categoria Identificada';
        headerDiv.appendChild(title);
        
        const category = document.createElement('p');
        category.className = `text-2xl font-bold text-${categoryColor}-700 dark:text-${categoryColor}-300`;
        category.textContent = result.category;
        
        const confidence = document.createElement('p');
        confidence.className = `text-sm text-${categoryColor}-600 dark:text-${categoryColor}-400 mt-1`;
        confidence.textContent = `Confiança: ${Math.round(result.confidence * 100)}%`;
        
        div.appendChild(headerDiv);
        div.appendChild(category);
        div.appendChild(confidence);
        
        return div;
    }

    createConfidenceSection(result) {
        const div = document.createElement('div');
        div.className = 'bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4';
        
        const headerDiv = document.createElement('div');
        headerDiv.className = 'flex items-center mb-3';
        
        const icon = document.createElement('svg');
        icon.className = 'w-5 h-5 text-purple-600 dark:text-purple-400 mr-2';
        icon.setAttribute('fill', 'none');
        icon.setAttribute('stroke', 'currentColor');
        icon.setAttribute('viewBox', '0 0 24 24');
        
        const iconPath = document.createElement('path');
        iconPath.setAttribute('stroke-linecap', 'round');
        iconPath.setAttribute('stroke-linejoin', 'round');
        iconPath.setAttribute('stroke-width', '2');
        iconPath.setAttribute('d', 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z');
        
        icon.appendChild(iconPath);
        headerDiv.appendChild(icon);
        
        const title = document.createElement('h4');
        title.className = 'font-semibold text-purple-800 dark:text-purple-200';
        title.textContent = 'Nível de Confiança';
        headerDiv.appendChild(title);
        
        const progressContainer = document.createElement('div');
        progressContainer.className = 'relative';
        
        const progressBg = document.createElement('div');
        progressBg.className = 'w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3';
        
        const progressBar = document.createElement('div');
        const confidencePercent = Math.round(result.confidence * 100);
        progressBar.className = `progress-bar h-3 rounded-full transition-all duration-1000 ease-out`;
        progressBar.style.width = `${confidencePercent}%`;
        
        if (confidencePercent >= 80) {
            progressBar.style.background = 'linear-gradient(90deg, #10b981, #059669)';
        } else if (confidencePercent >= 60) {
            progressBar.style.background = 'linear-gradient(90deg, #f59e0b, #d97706)';
        } else {
            progressBar.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';
        }
        
        progressBg.appendChild(progressBar);
        progressContainer.appendChild(progressBg);
        
        const percentText = document.createElement('div');
        percentText.className = 'text-center mt-2 text-lg font-bold text-purple-700 dark:text-purple-300';
        percentText.textContent = `${confidencePercent}%`;
        
        div.appendChild(headerDiv);
        div.appendChild(progressContainer);
        div.appendChild(percentText);
        
        return div;
    }

    createResponseSection(result) {
        const div = document.createElement('div');
        div.className = 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4';
        
        const headerDiv = document.createElement('div');
        headerDiv.className = 'flex items-center mb-3';
        
        const icon = document.createElement('svg');
        icon.className = 'w-5 h-5 text-blue-600 dark:text-blue-400 mr-2';
        icon.setAttribute('fill', 'none');
        icon.setAttribute('stroke', 'currentColor');
        icon.setAttribute('viewBox', '0 0 24 24');
        
        const iconPath = document.createElement('path');
        iconPath.setAttribute('stroke-linecap', 'round');
        iconPath.setAttribute('stroke-linejoin', 'round');
        iconPath.setAttribute('stroke-width', '2');
        iconPath.setAttribute('d', 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z');
        
        icon.appendChild(iconPath);
        headerDiv.appendChild(icon);
        
        const title = document.createElement('h4');
        title.className = 'font-semibold text-blue-800 dark:text-blue-200';
        title.textContent = 'Resposta Sugerida';
        headerDiv.appendChild(title);
        
        const responseContainer = document.createElement('div');
        responseContainer.className = 'bg-white dark:bg-slate-700 rounded-lg p-4 border border-blue-100 dark:border-blue-700';
        
        const textarea = document.createElement('textarea');
        textarea.className = 'w-full text-gray-700 dark:text-gray-300 bg-transparent border-none resize-none focus:outline-none';
        textarea.rows = 8;
        textarea.value = result.suggestedResponse;
        
        responseContainer.appendChild(textarea);
        
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'flex space-x-3 mt-3';
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-response-btn text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium flex items-center px-3 py-2 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors';
        copyBtn.innerHTML = `
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
            </svg>
            Copiar resposta
        `;
        copyBtn.dataset.response = textarea.value;
        
        buttonContainer.appendChild(copyBtn);
        
        div.appendChild(headerDiv);
        div.appendChild(responseContainer);
        div.appendChild(buttonContainer);
        
        return div;
    }

    createAnalysisSection(result) {
        const div = document.createElement('div');
        div.className = 'bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-lg p-4';
        
        const headerDiv = document.createElement('div');
        headerDiv.className = 'flex items-center mb-3';
        
        const icon = document.createElement('svg');
        icon.className = 'w-5 h-5 text-gray-600 dark:text-gray-400 mr-2';
        icon.setAttribute('fill', 'none');
        icon.setAttribute('stroke', 'currentColor');
        icon.setAttribute('viewBox', '0 0 24 24');
        
        const iconPath = document.createElement('path');
        iconPath.setAttribute('stroke-linecap', 'round');
        iconPath.setAttribute('stroke-linejoin', 'round');
        iconPath.setAttribute('stroke-width', '2');
        iconPath.setAttribute('d', 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z');
        
        icon.appendChild(iconPath);
        headerDiv.appendChild(icon);
        
        const title = document.createElement('h4');
        title.className = 'font-semibold text-gray-800 dark:text-gray-200';
        title.textContent = 'Análise Detalhada';
        headerDiv.appendChild(title);
        
        const reasoning = document.createElement('p');
        reasoning.className = 'text-gray-700 dark:text-gray-300 text-sm whitespace-pre-line';
        reasoning.textContent = result.reasoning;
        
        div.appendChild(headerDiv);
        div.appendChild(reasoning);
        
        return div;
    }

    createHighlightedContentSection(result) {
        const div = document.createElement('div');
        div.className = 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4';
        
        const headerDiv = document.createElement('div');
        headerDiv.className = 'flex items-center mb-3';
        
        const icon = document.createElement('svg');
        icon.className = 'w-5 h-5 text-yellow-600 dark:text-yellow-400 mr-2';
        icon.setAttribute('fill', 'none');
        icon.setAttribute('stroke', 'currentColor');
        icon.setAttribute('viewBox', '0 0 24 24');
        
        const iconPath = document.createElement('path');
        iconPath.setAttribute('stroke-linecap', 'round');
        iconPath.setAttribute('stroke-linejoin', 'round');
        iconPath.setAttribute('stroke-width', '2');
        iconPath.setAttribute('d', 'M7 20l4-16m2 16l4-16M6 9h14M4 15h14');
        
        icon.appendChild(iconPath);
        headerDiv.appendChild(icon);
        
        const title = document.createElement('h4');
        title.className = 'font-semibold text-yellow-800 dark:text-yellow-200';
        title.textContent = 'Palavras-chave Identificadas';
        headerDiv.appendChild(title);
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'bg-white dark:bg-slate-700 rounded-lg p-4 border border-yellow-100 dark:border-yellow-700 max-h-32 overflow-y-auto';
        
        const highlightedContent = this.highlightKeywords(result.originalContent, result.highlightedKeywords);
        contentDiv.innerHTML = highlightedContent;
        
        div.appendChild(headerDiv);
        div.appendChild(contentDiv);
        
        return div;
    }

    highlightKeywords(content, keywords) {
        let highlightedContent = content;
        
        keywords.forEach(keyword => {
            const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
            highlightedContent = highlightedContent.replace(regex, `<span class="highlighted-keyword">${keyword}</span>`);
        });
        
        return highlightedContent;
    }

    createActionButtons() {
        const div = document.createElement('div');
        div.className = 'flex space-x-3';
        
        const newBtn = document.createElement('button');
        newBtn.className = 'new-classification-btn btn-secondary flex-1 text-gray-700 dark:text-gray-300 font-semibold py-3 px-6 rounded-lg border border-gray-200 dark:border-gray-600 shadow-md flex items-center justify-center';
        newBtn.innerHTML = `
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            Nova Classificação
        `;
        
        div.appendChild(newBtn);
        
        return div;
    }

    copyResponse(button) {
        const textarea = button.closest('.bg-blue-50, .dark\\:bg-blue-900\\/20').querySelector('textarea');
        const textToCopy = textarea ? textarea.value : button.dataset.response;
        
        navigator.clipboard.writeText(textToCopy).then(() => {
            const originalHTML = button.innerHTML;
            button.innerHTML = `
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                Copiado!
            `;
            button.classList.add('text-green-600', 'dark:text-green-400');
            
            setTimeout(() => {
                button.innerHTML = originalHTML;
                button.classList.remove('text-green-600', 'dark:text-green-400');
            }, 2000);
            
            this.showToast('Resposta copiada para a área de transferência!', 'success');
        }).catch(err => {
            console.error('Erro ao copiar texto: ', err);
            this.showToast('Erro ao copiar texto', 'error');
        });
    }

    resetInterface() {
        const fileInput = document.querySelector(CONFIG.SELECTORS.fileInput);
        const fileInfo = document.querySelector(CONFIG.SELECTORS.fileInfo);
        fileInput.value = '';
        fileInfo.classList.add('hidden');
        
        const textarea = document.querySelector(CONFIG.SELECTORS.emailText);
        textarea.value = '';
        this.updateCharCount();
        
        const resultContainer = document.querySelector(CONFIG.SELECTORS.resultContainer);
        const errorContainer = document.querySelector(CONFIG.SELECTORS.errorContainer);
        resultContainer.classList.add('hidden');
        errorContainer.classList.add('hidden');
        
        this.showToast('Interface limpa. Pronto para nova classificação!', 'info');
    }

    showError(message) {
        const container = document.querySelector(CONFIG.SELECTORS.resultContainer);
        const errorContainer = document.querySelector(CONFIG.SELECTORS.errorContainer);
        const errorMessage = document.querySelector(CONFIG.SELECTORS.errorMessage);

        container.classList.add('hidden');

        errorContainer.classList.remove('hidden');
        errorMessage.textContent = message;
    }

    showToast(message, type = 'info') {
        const container = document.querySelector(CONFIG.SELECTORS.toastContainer);
        const template = document.getElementById('toast-template');
        const toast = template.content.cloneNode(true);
        
        const toastElement = toast.querySelector('.toast');
        const icon = toast.querySelector('.toast-icon');
        const messageElement = toast.querySelector('.toast-message');
        const closeButton = toast.querySelector('.toast-close');
        
        messageElement.textContent = message;
        
        let iconPath, colorClasses;
        switch (type) {
            case 'success':
                iconPath = 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z';
                colorClasses = 'text-green-600 dark:text-green-400';
                toastElement.classList.add('border-green-200', 'dark:border-green-800');
                break;
            case 'error':
                iconPath = 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z';
                colorClasses = 'text-red-600 dark:text-red-400';
                toastElement.classList.add('border-red-200', 'dark:border-red-800');
                break;
            case 'warning':
                iconPath = 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
                colorClasses = 'text-yellow-600 dark:text-yellow-400';
                toastElement.classList.add('border-yellow-200', 'dark:border-yellow-800');
                break;
            default:
                iconPath = 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
                colorClasses = 'text-blue-600 dark:text-blue-400';
                toastElement.classList.add('border-blue-200', 'dark:border-blue-800');
        }
        
        icon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${iconPath}"></path>`;
        icon.classList.add(...colorClasses.split(' '));
        
        container.appendChild(toast);
        
        const timeoutId = setTimeout(() => {
            this.closeToast(toastElement);
        }, CONFIG.TOAST_DURATION);
        
        toastElement.dataset.timeoutId = timeoutId;
    }

    closeToast(toastElement) {
        if (toastElement.dataset.timeoutId) {
            clearTimeout(toastElement.dataset.timeoutId);
        }
        
        toastElement.classList.remove('animate-toast-in');
        toastElement.classList.add('animate-toast-out');
        
        setTimeout(() => {
            if (toastElement.parentNode) {
                toastElement.parentNode.removeChild(toastElement);
            }
        }, 300);
    }

    loadHistory() {
        try {
            const history = localStorage.getItem(CONFIG.HISTORY_KEY);
            return history ? JSON.parse(history) : [];
        } catch (error) {
            console.error('Error loading history:', error);
            return [];
        }
    }

    saveHistory() {
        try {
            localStorage.setItem(CONFIG.HISTORY_KEY, JSON.stringify(this.history));
        } catch (error) {
            console.error('Error saving history:', error);
        }
    }

    addToHistory(emailData, result) {
        const historyItem = {
            id: Date.now(),
            timestamp: new Date().toISOString(),
            content: emailData.content,
            source: emailData.source,
            filename: emailData.filename,
            category: result.category,
            confidence: result.confidence,
            suggestedResponse: result.suggestedResponse,
            reasoning: result.reasoning
        };
        
        this.history.unshift(historyItem);
        
        if (this.history.length > CONFIG.MAX_HISTORY_ITEMS) {
            this.history = this.history.slice(0, CONFIG.MAX_HISTORY_ITEMS);
        }
        
        this.saveHistory();
        this.renderHistory();
    }

    renderHistory() {
        const historyList = document.querySelector(CONFIG.SELECTORS.historyList);
        
        if (this.history.length === 0) {
            historyList.innerHTML = `
                <p class="text-gray-500 dark:text-gray-400 text-sm text-center py-8">
                    Nenhuma classificação ainda
                </p>
            `;
            return;
        }
        
        historyList.innerHTML = '';
        
        this.history.forEach(item => {
            const historyItem = this.createHistoryItem(item);
            historyList.appendChild(historyItem);
        });
    }

    createHistoryItem(item) {
        const template = document.getElementById('history-item-template');
        const historyItem = template.content.cloneNode(true);
        
        const itemElement = historyItem.querySelector('.history-item');
        const category = historyItem.querySelector('.history-category');
        const time = historyItem.querySelector('.history-time');
        const preview = historyItem.querySelector('.history-preview');
        
        const isProductive = item.category === 'Produtivo';
        category.textContent = item.category;
        category.className = `history-category text-sm font-semibold px-2 py-1 rounded ${
            isProductive 
                ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300' 
                : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
        }`;
        
        const date = new Date(item.timestamp);
        time.textContent = date.toLocaleString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const previewText = item.content.length > 100 
            ? item.content.substring(0, 100) + '...' 
            : item.content;
        preview.textContent = previewText;
        
        itemElement.dataset.historyId = item.id;
        
        return historyItem;
    }

    loadHistoryItem(element) {
        const historyId = element.dataset.historyId;
        const item = this.history.find(h => h.id == historyId);
        
        if (!item) return;
        
        const result = {
            category: item.category,
            confidence: item.confidence,
            suggestedResponse: item.suggestedResponse,
            reasoning: item.reasoning,
            originalContent: item.content
        };
        
        this.showResult(result);
        this.showToast('Classificação carregada do histórico', 'info');
    }


        confirmClearHistory() {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 animate-fade-in';
        
        modal.innerHTML = `
            <div class="bg-white dark:bg-slate-800 rounded-xl p-6 max-w-md mx-4 shadow-2xl animate-slide-up">
                <div class="flex items-center mb-4">
                    <svg class="w-6 h-6 text-red-600 dark:text-red-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                    </svg>
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Confirmar Limpeza</h3>
                </div>
                
                <p class="text-gray-600 dark:text-gray-300 mb-6">
                    Tem certeza que deseja apagar todo o histórico de classificações? Esta ação não pode ser desfeita.
                </p>
                
                <div class="flex space-x-3">
                    <button class="cancel-clear flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors font-medium">
                        Cancelar
                    </button>
                    <button class="confirm-clear flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium">
                        Apagar Histórico
                    </button>
                </div>
            </div>
        `;
        
        const cancelBtn = modal.querySelector('.cancel-clear');
        const confirmBtn = modal.querySelector('.confirm-clear');
        
        cancelBtn.addEventListener('click', () => {
            this.closeModal(modal);
        });
        
        confirmBtn.addEventListener('click', () => {
            this.clearHistory();
            this.closeModal(modal);
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal(modal);
            }
        });
        
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                this.closeModal(modal);
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
        
        document.body.appendChild(modal);
    }
    
    closeModal(modal) {
        modal.classList.remove('animate-fade-in');
        modal.classList.add('animate-fade-out');
        
        setTimeout(() => {
            if (modal.parentNode) {
                modal.parentNode.removeChild(modal);
            }
        }, 300);
    }

    clearHistory() {
        this.history = [];
        this.saveHistory();
        this.renderHistory();
        this.showToast('Histórico limpo com sucesso', 'success');
    }

    async checkAPIHealth() {
        try {
            const response = await fetch(CONFIG.HEALTH_URL);
            if (response.ok) {
                this.showToast('Conectado ao servidor de classificação', 'success');
            }
        } catch (error) {
            this.showToast('Servidor offline - usando modo demonstração', 'warning');
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new EmailClassifier();
});