import * as vscode from 'vscode';
import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

/**
 * Read-Only Virtual File System Provider for CognitiveZip (.czip)
 * Allows browsing and viewing compressed archives without extracting them.
 */
class CZipFileSystemProvider implements vscode.FileSystemProvider {
    private _emitter = new vscode.EventEmitter<vscode.FileChangeEvent[]>();
    readonly onDidChangeFile: vscode.Event<vscode.FileChangeEvent[]> = this._emitter.event;

    watch(): vscode.Disposable {
        return new vscode.Disposable(() => {});
    }

    async stat(uri: vscode.Uri): Promise<vscode.FileStat> {
        // Simple virtual file stat
        return {
            type: uri.path.endsWith('/') ? vscode.FileType.Directory : vscode.FileType.File,
            ctime: Date.now(),
            mtime: Date.now(),
            size: 1024,
        };
    }

    async readDirectory(uri: vscode.Uri): Promise<[string, vscode.FileType][]> {
        // Query files list using czip cli
        const archivePath = uri.authority;
        try {
            const { stdout } = await execFileAsync('python', ['-m', 'cognitive_zip.cli', 'list', archivePath]);
            const lines = stdout.split('\n');
            const entries: [string, vscode.FileType][] = [];
            for (const line of lines) {
                const match = line.match(/•\s+(\S+)/);
                if (match) {
                    entries.push([match[1], vscode.FileType.File]);
                }
            }
            return entries;
        } catch {
            return [];
        }
    }

    createDirectory(): void {
        throw vscode.FileSystemError.NoPermissions('CognitiveZip virtual archive is read-only');
    }

    async readFile(uri: vscode.Uri): Promise<Uint8Array> {
        const archivePath = uri.authority;
        const filePath = uri.path.replace(/^\//, '');

        try {
            // Read selectively using czip cat (Zero-Extraction)
            const { stdout } = await execFileAsync('python', ['-m', 'cognitive_zip.cli', 'cat', archivePath, filePath], {
                encoding: 'buffer',
            });
            return new Uint8Array(stdout);
        } catch (err: any) {
            throw vscode.FileSystemError.FileNotFound(uri);
        }
    }

    writeFile(): void {
        throw vscode.FileSystemError.NoPermissions('CognitiveZip virtual archive is read-only');
    }

    delete(): void {
        throw vscode.FileSystemError.NoPermissions('CognitiveZip virtual archive is read-only');
    }

    rename(): void {
        throw vscode.FileSystemError.NoPermissions('CognitiveZip virtual archive is read-only');
    }
}

export function activate(context: vscode.Context) {
    const provider = new CZipFileSystemProvider();
    context.subscriptions.push(
        vscode.workspace.registerFileSystemProvider('czip', provider, { isReadonly: true })
    );

    // Command: Semantic Search Inside Archive
    context.subscriptions.push(
        vscode.commands.registerCommand('czip.semanticSearch', async (uri: vscode.Uri) => {
            const archivePath = uri ? uri.fsPath : await vscode.window.showInputBox({ prompt: 'Path to .czip archive' });
            if (!archivePath) return;

            const query = await vscode.window.showInputBox({
                prompt: 'Enter natural language search or keyword',
                placeHolder: 'e.g., auth token expiry or database connection',
            });
            if (!query) return;

            try {
                const { stdout } = await execFileAsync('python', ['-m', 'cognitive_zip.cli', 'query', archivePath, query]);
                const outputDoc = await vscode.workspace.openTextDocument({
                    content: stdout,
                    language: 'markdown',
                });
                await vscode.window.showTextDocument(outputDoc);
            } catch (err: any) {
                vscode.window.showErrorMessage(`Search error: ${err.message}`);
            }
        })
    );
}

export function deactivate() {}
