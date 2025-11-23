import * as vscode from 'vscode';
import axios from 'axios';

let chatViewProvider: JarvisChatViewProvider;
let codebaseIndexProvider: CodebaseIndexProvider;
let completionProvider: vscode.Disposable | undefined;

export function activate(context: vscode.ExtensionContext) {
    console.log('JARVIS AI Assistant is now active!');

    const config = vscode.workspace.getConfiguration('jarvis');
    const serverUrl = config.get<string>('serverUrl', 'http://localhost:5000');

    // Initialize Chat View Provider
    chatViewProvider = new JarvisChatViewProvider(context.extensionUri, serverUrl);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider('jarvis.chatView', chatViewProvider)
    );

    // Initialize Codebase Index Provider
    codebaseIndexProvider = new CodebaseIndexProvider();
    context.subscriptions.push(
        vscode.window.registerTreeDataProvider('jarvis.codebaseView', codebaseIndexProvider)
    );

    // Register Commands
    registerCommands(context, serverUrl);

    // Register Inline Completion Provider
    if (config.get<boolean>('enableInlineCompletion', true)) {
        registerInlineCompletionProvider(context, serverUrl);
    }

    // Auto-index workspace if enabled
    if (config.get<boolean>('autoIndexWorkspace', false)) {
        indexWorkspace(serverUrl);
    }

    // Status bar item
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.text = '$(hubot) JARVIS';
    statusBarItem.tooltip = 'JARVIS AI Assistant';
    statusBarItem.command = 'jarvis.openChat';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);
}

function registerCommands(context: vscode.ExtensionContext, serverUrl: string) {
    // Open Chat
    context.subscriptions.push(
        vscode.commands.registerCommand('jarvis.openChat', () => {
            vscode.commands.executeCommand('jarvis.chatView.focus');
        })
    );

    // Explain Code
    context.subscriptions.push(
        vscode.commands.registerCommand('jarvis.explainCode', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            const selection = editor.document.getText(editor.selection);
            if (!selection) {
                vscode.window.showWarningMessage('Please select some code first');
                return;
            }

            await processCodeAction(serverUrl, 'explain', selection, editor.document.languageId);
        })
    );

    // Improve Code
    context.subscriptions.push(
        vscode.commands.registerCommand('jarvis.improveCode', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            const selection = editor.document.getText(editor.selection);
            if (!selection) {
                vscode.window.showWarningMessage('Please select some code first');
                return;
            }

            await processCodeAction(serverUrl, 'improve', selection, editor.document.languageId);
        })
    );

    // Generate Tests
    context.subscriptions.push(
        vscode.commands.registerCommand('jarvis.generateTests', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            const selection = editor.document.getText(editor.selection);
            if (!selection) {
                vscode.window.showWarningMessage('Please select some code first');
                return;
            }

            await processCodeAction(serverUrl, 'generate_tests', selection, editor.document.languageId);
        })
    );

    // Review Current File
    context.subscriptions.push(
        vscode.commands.registerCommand('jarvis.reviewCode', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No active file to review');
                return;
            }

            const content = editor.document.getText();
            const fileName = editor.document.fileName;

            await processCodeAction(serverUrl, 'review', content, editor.document.languageId, fileName);
        })
    );

    // Generate Commit Message
    context.subscriptions.push(
        vscode.commands.registerCommand('jarvis.generateCommitMessage', async () => {
            await generateCommitMessage(serverUrl);
        })
    );

    // Ask About Code
    context.subscriptions.push(
        vscode.commands.registerCommand('jarvis.askAboutCode', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            const selection = editor.document.getText(editor.selection);
            const question = await vscode.window.showInputBox({
                prompt: 'What would you like to know about this code?',
                placeHolder: 'e.g., What does this function do?'
            });

            if (question) {
                await processCodeAction(serverUrl, 'ask', selection, editor.document.languageId, undefined, question);
            }
        })
    );

    // Index Workspace
    context.subscriptions.push(
        vscode.commands.registerCommand('jarvis.indexWorkspace', async () => {
            await indexWorkspace(serverUrl);
        })
    );

    // Security Scan
    context.subscriptions.push(
        vscode.commands.registerCommand('jarvis.securityScan', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No active file to scan');
                return;
            }

            await processCodeAction(serverUrl, 'security_scan', editor.document.getText(), editor.document.languageId, editor.document.fileName);
        })
    );

    // Trigger Inline Completion
    context.subscriptions.push(
        vscode.commands.registerCommand('jarvis.inlineComplete', async () => {
            await vscode.commands.executeCommand('editor.action.inlineSuggest.trigger');
        })
    );
}

async function processCodeAction(
    serverUrl: string,
    action: string,
    code: string,
    language: string,
    fileName?: string,
    question?: string
) {
    const panel = vscode.window.createWebviewPanel(
        'jarvisResult',
        `JARVIS: ${action.charAt(0).toUpperCase() + action.slice(1)}`,
        vscode.ViewColumn.Beside,
        { enableScripts: true }
    );

    panel.webview.html = getLoadingHtml();

    try {
        const response = await axios.post(`${serverUrl}/api/code/action`, {
            action,
            code,
            language,
            file_name: fileName,
            question
        });

        panel.webview.html = getResultHtml(action, response.data.result, code, language);
    } catch (error: any) {
        panel.webview.html = getErrorHtml(error.message);
    }
}

async function generateCommitMessage(serverUrl: string) {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) {
        vscode.window.showWarningMessage('No workspace folder open');
        return;
    }

    const terminal = vscode.window.createTerminal('JARVIS Git');

    try {
        // Get git diff
        const { execSync } = require('child_process');
        const cwd = workspaceFolders[0].uri.fsPath;

        let diff = '';
        try {
            diff = execSync('git diff --staged', { cwd, encoding: 'utf-8' });
            if (!diff.trim()) {
                diff = execSync('git diff', { cwd, encoding: 'utf-8' });
            }
        } catch (e) {
            vscode.window.showWarningMessage('No git changes found');
            return;
        }

        if (!diff.trim()) {
            vscode.window.showWarningMessage('No changes to commit');
            return;
        }

        const response = await axios.post(`${serverUrl}/api/code/commit-message`, {
            diff: diff.substring(0, 10000)  // Limit diff size
        });

        const commitMessage = response.data.message;

        // Show commit message and let user edit
        const result = await vscode.window.showInputBox({
            value: commitMessage,
            prompt: 'Review and edit commit message',
            validateInput: (value) => value.trim() ? null : 'Commit message cannot be empty'
        });

        if (result) {
            // Copy to clipboard
            await vscode.env.clipboard.writeText(result);
            vscode.window.showInformationMessage('Commit message copied to clipboard!');
        }
    } catch (error: any) {
        vscode.window.showErrorMessage(`Failed to generate commit message: ${error.message}`);
    }
}

async function indexWorkspace(serverUrl: string) {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders) {
        vscode.window.showWarningMessage('No workspace folder open');
        return;
    }

    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'JARVIS: Indexing workspace...',
        cancellable: true
    }, async (progress, token) => {
        try {
            const files = await vscode.workspace.findFiles(
                '**/*.{ts,js,py,java,go,rs,cpp,c,h,jsx,tsx,vue,rb,php,cs,swift,kt}',
                '**/node_modules/**'
            );

            const fileContents: { path: string; content: string; language: string }[] = [];

            for (let i = 0; i < files.length && !token.isCancellationRequested; i++) {
                progress.report({
                    increment: (100 / files.length),
                    message: `Processing ${i + 1}/${files.length} files`
                });

                const file = files[i];
                try {
                    const doc = await vscode.workspace.openTextDocument(file);
                    fileContents.push({
                        path: file.fsPath,
                        content: doc.getText().substring(0, 5000), // Limit content size
                        language: doc.languageId
                    });
                } catch (e) {
                    // Skip files that can't be read
                }
            }

            await axios.post(`${serverUrl}/api/code/index`, {
                workspace: workspaceFolders[0].uri.fsPath,
                files: fileContents
            });

            vscode.window.showInformationMessage(`JARVIS indexed ${fileContents.length} files`);
            codebaseIndexProvider.refresh();
        } catch (error: any) {
            vscode.window.showErrorMessage(`Indexing failed: ${error.message}`);
        }
    });
}

function registerInlineCompletionProvider(context: vscode.ExtensionContext, serverUrl: string) {
    const config = vscode.workspace.getConfiguration('jarvis');
    const delay = config.get<number>('completionDelay', 500);

    let debounceTimer: NodeJS.Timeout | undefined;

    const provider: vscode.InlineCompletionItemProvider = {
        async provideInlineCompletionItems(document, position, context, token) {
            // Clear existing timer
            if (debounceTimer) {
                clearTimeout(debounceTimer);
            }

            // Only trigger on typing or explicit invocation
            if (context.triggerKind !== vscode.InlineCompletionTriggerKind.Automatic &&
                context.triggerKind !== vscode.InlineCompletionTriggerKind.Invoke) {
                return [];
            }

            return new Promise((resolve) => {
                debounceTimer = setTimeout(async () => {
                    if (token.isCancellationRequested) {
                        resolve([]);
                        return;
                    }

                    try {
                        // Get context around cursor
                        const linePrefix = document.lineAt(position).text.substring(0, position.character);
                        const lineSuffix = document.lineAt(position).text.substring(position.character);

                        // Get surrounding lines for context
                        const startLine = Math.max(0, position.line - 10);
                        const endLine = Math.min(document.lineCount - 1, position.line + 5);

                        let contextBefore = '';
                        for (let i = startLine; i < position.line; i++) {
                            contextBefore += document.lineAt(i).text + '\n';
                        }
                        contextBefore += linePrefix;

                        let contextAfter = lineSuffix + '\n';
                        for (let i = position.line + 1; i <= endLine; i++) {
                            contextAfter += document.lineAt(i).text + '\n';
                        }

                        const response = await axios.post(`${serverUrl}/api/code/complete`, {
                            prefix: contextBefore,
                            suffix: contextAfter,
                            language: document.languageId,
                            file_name: document.fileName,
                            max_tokens: config.get<number>('maxCompletionTokens', 150)
                        }, { timeout: 5000 });

                        if (token.isCancellationRequested) {
                            resolve([]);
                            return;
                        }

                        const completion = response.data.completion;
                        if (completion && completion.trim()) {
                            resolve([
                                new vscode.InlineCompletionItem(
                                    completion,
                                    new vscode.Range(position, position)
                                )
                            ]);
                        } else {
                            resolve([]);
                        }
                    } catch (error) {
                        resolve([]);
                    }
                }, delay);
            });
        }
    };

    completionProvider = vscode.languages.registerInlineCompletionItemProvider(
        { pattern: '**' },
        provider
    );
    context.subscriptions.push(completionProvider);
}

// Chat View Provider
class JarvisChatViewProvider implements vscode.WebviewViewProvider {
    private _view?: vscode.WebviewView;

    constructor(
        private readonly _extensionUri: vscode.Uri,
        private readonly _serverUrl: string
    ) {}

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'sendMessage':
                    await this._handleMessage(data.message, data.context);
                    break;
                case 'getActiveFileContext':
                    this._sendActiveFileContext();
                    break;
            }
        });
    }

    private async _handleMessage(message: string, codeContext?: string) {
        if (!this._view) return;

        this._view.webview.postMessage({ type: 'startResponse' });

        try {
            const response = await axios.post(`${this._serverUrl}/api/chat/message`, {
                message,
                context: { code: codeContext }
            });

            this._view.webview.postMessage({
                type: 'response',
                content: response.data.content
            });
        } catch (error: any) {
            this._view.webview.postMessage({
                type: 'error',
                content: `Error: ${error.message}`
            });
        }
    }

    private _sendActiveFileContext() {
        const editor = vscode.window.activeTextEditor;
        if (editor && this._view) {
            const selection = editor.document.getText(editor.selection);
            const fileName = editor.document.fileName.split('/').pop();

            this._view.webview.postMessage({
                type: 'fileContext',
                fileName,
                selection: selection || null,
                language: editor.document.languageId
            });
        }
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JARVIS Chat</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background: var(--vscode-sideBar-background);
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 10px;
        }
        .message {
            margin-bottom: 12px;
            padding: 8px 12px;
            border-radius: 8px;
            max-width: 90%;
        }
        .message.user {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            margin-left: auto;
        }
        .message.assistant {
            background: var(--vscode-editor-background);
            border: 1px solid var(--vscode-panel-border);
        }
        .message pre {
            background: var(--vscode-textBlockQuote-background);
            padding: 8px;
            border-radius: 4px;
            overflow-x: auto;
            margin: 8px 0;
        }
        .message code {
            font-family: var(--vscode-editor-font-family);
            font-size: 12px;
        }
        .input-container {
            padding: 10px;
            border-top: 1px solid var(--vscode-panel-border);
            display: flex;
            gap: 8px;
        }
        .input-container textarea {
            flex: 1;
            padding: 8px;
            border: 1px solid var(--vscode-input-border);
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border-radius: 4px;
            resize: none;
            font-family: inherit;
            font-size: inherit;
        }
        .input-container button {
            padding: 8px 16px;
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .input-container button:hover {
            background: var(--vscode-button-hoverBackground);
        }
        .context-bar {
            padding: 6px 10px;
            background: var(--vscode-editor-background);
            border-bottom: 1px solid var(--vscode-panel-border);
            font-size: 11px;
            color: var(--vscode-descriptionForeground);
        }
        .typing-indicator {
            display: none;
            padding: 8px 12px;
            color: var(--vscode-descriptionForeground);
        }
        .typing-indicator.active { display: block; }
    </style>
</head>
<body>
    <div class="context-bar" id="context-bar">
        <span id="file-context">No file selected</span>
    </div>
    <div class="chat-container" id="chat-container">
        <div class="message assistant">
            <p>Hello! I'm JARVIS, your AI coding assistant. How can I help you today?</p>
            <p style="font-size: 11px; margin-top: 8px; opacity: 0.7;">
                Tip: Select code in the editor to include it in your question.
            </p>
        </div>
    </div>
    <div class="typing-indicator" id="typing">JARVIS is thinking...</div>
    <div class="input-container">
        <textarea id="input" rows="2" placeholder="Ask JARVIS..."></textarea>
        <button onclick="sendMessage()">Send</button>
    </div>
    <script>
        const vscode = acquireVsCodeApi();
        const chatContainer = document.getElementById('chat-container');
        const input = document.getElementById('input');
        const typing = document.getElementById('typing');
        const contextBar = document.getElementById('file-context');

        let currentContext = null;

        // Request file context on load
        vscode.postMessage({ type: 'getActiveFileContext' });

        function sendMessage() {
            const message = input.value.trim();
            if (!message) return;

            // Add user message
            addMessage('user', message);
            input.value = '';

            // Send to extension
            vscode.postMessage({
                type: 'sendMessage',
                message: message,
                context: currentContext
            });
        }

        function addMessage(role, content) {
            const div = document.createElement('div');
            div.className = 'message ' + role;
            div.innerHTML = formatMessage(content);
            chatContainer.appendChild(div);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function formatMessage(content) {
            // Simple markdown-like formatting
            return content
                .replace(/\`\`\`(\w*)\n([\s\S]*?)\`\`\`/g, '<pre><code>$2</code></pre>')
                .replace(/\`([^\`]+)\`/g, '<code>$1</code>')
                .replace(/\n/g, '<br>');
        }

        // Handle messages from extension
        window.addEventListener('message', event => {
            const data = event.data;
            switch (data.type) {
                case 'startResponse':
                    typing.classList.add('active');
                    break;
                case 'response':
                    typing.classList.remove('active');
                    addMessage('assistant', data.content);
                    break;
                case 'error':
                    typing.classList.remove('active');
                    addMessage('assistant', data.content);
                    break;
                case 'fileContext':
                    if (data.selection) {
                        currentContext = data.selection;
                        contextBar.textContent = data.fileName + ' (selection)';
                    } else {
                        currentContext = null;
                        contextBar.textContent = data.fileName || 'No file selected';
                    }
                    break;
            }
        });

        // Enter to send
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    </script>
</body>
</html>`;
    }
}

// Codebase Index Tree Provider
class CodebaseIndexProvider implements vscode.TreeDataProvider<IndexItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<IndexItem | undefined | null | void> = new vscode.EventEmitter<IndexItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<IndexItem | undefined | null | void> = this._onDidChangeTreeData.event;

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: IndexItem): vscode.TreeItem {
        return element;
    }

    async getChildren(element?: IndexItem): Promise<IndexItem[]> {
        if (!element) {
            return [
                new IndexItem('Index Status', vscode.TreeItemCollapsibleState.None, 'status'),
                new IndexItem('Indexed Files', vscode.TreeItemCollapsibleState.Collapsed, 'files')
            ];
        }
        return [];
    }
}

class IndexItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly type: string
    ) {
        super(label, collapsibleState);
        this.tooltip = `${this.label}`;
    }
}

// HTML Templates
function getLoadingHtml(): string {
    return `<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
        }
        .loader {
            border: 3px solid var(--vscode-editor-background);
            border-top: 3px solid var(--vscode-button-background);
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="loader"></div>
    <p style="text-align: center;">JARVIS is analyzing your code...</p>
</body>
</html>`;
}

function getResultHtml(action: string, result: string, code: string, language: string): string {
    return `<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            line-height: 1.6;
        }
        h2 { margin-bottom: 15px; }
        pre {
            background: var(--vscode-textBlockQuote-background);
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
        }
        code {
            font-family: var(--vscode-editor-font-family);
        }
        .section {
            margin-bottom: 20px;
        }
        .copy-btn {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <h2>JARVIS: ${action.charAt(0).toUpperCase() + action.slice(1).replace('_', ' ')}</h2>
    <div class="section">
        ${result.replace(/\n/g, '<br>').replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')}
    </div>
    <button class="copy-btn" onclick="navigator.clipboard.writeText(\`${result.replace(/`/g, '\\`').replace(/\$/g, '\\$')}\`)">
        Copy Result
    </button>
</body>
</html>`;
}

function getErrorHtml(error: string): string {
    return `<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-errorForeground);
        }
    </style>
</head>
<body>
    <h2>Error</h2>
    <p>${error}</p>
    <p style="margin-top: 15px; color: var(--vscode-descriptionForeground);">
        Make sure the JARVIS server is running at the configured URL.
    </p>
</body>
</html>`;
}

export function deactivate() {
    if (completionProvider) {
        completionProvider.dispose();
    }
}
