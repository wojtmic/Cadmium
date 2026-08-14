import * as vscode from "vscode";
import * as path from "path";

const CADMIUM_SRC_DIR = "bundled/cadmium-src";
const JAVA_STUBS_DIR = "bundled/java-stubs";

function bundledPaths(context: vscode.ExtensionContext): string[] {
  return [
    path.join(context.extensionPath, CADMIUM_SRC_DIR),
    path.join(context.extensionPath, JAVA_STUBS_DIR),
  ];
}

async function applyExtraPaths(context: vscode.ExtensionContext): Promise<void> {
  const config = vscode.workspace.getConfiguration("python.analysis");
  const existing = config.get<string[]>("extraPaths") ?? [];
  const toAdd = bundledPaths(context);

  const merged = Array.from(new Set([...existing, ...toAdd]));

  if (merged.length === existing.length && toAdd.every((p) => existing.includes(p))) {
    return;
  }

  await config.update("extraPaths", merged, vscode.ConfigurationTarget.Global);
}

export async function activate(context: vscode.ExtensionContext) {
  await applyExtraPaths(context);

  context.subscriptions.push(
    vscode.commands.registerCommand("cadmiumTypes.reapply", async () => {
      await applyExtraPaths(context);
      vscode.window.showInformationMessage("Cadmium type paths reapplied.");
    })
  );
}

export function deactivate() {
  // Deliberately not removing the extraPaths entries on deactivate/uninstall.
  // VS Code doesn't call deactivate() on uninstall reliably, and leaving a
  // couple of stale-but-harmless paths behind is a far smaller problem than
  // racing another extension's write to the same global setting.
}
