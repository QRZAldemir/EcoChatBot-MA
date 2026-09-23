# ═══════════════════════════════════════════════════════════════════
# EcoChatBot-Marcx · Gerador de Árvore de Estrutura
# Gera um arquivo estrutura.txt com a árvore REAL do projeto
# ═══════════════════════════════════════════════════════════════════

$ErrorActionPreference = "SilentlyContinue"

$raiz = "E:\EcoChatBot-MA"
$saida = "$raiz\docs\estrutura-gerada.txt"

# Função para gerar árvore
function Show-Tree {
    param($Path, $Prefix = "")
    
    $items = Get-ChildItem -Path $Path -Force |
        Where-Object {
            $_.Name -notin @('node_modules', '.git', 'dist', '.angular', 'out-tsc', '__pycache__', '.venv', 'venv')
        } |
        Sort-Object { $_.PSIsContainer } -Descending
    
    $total = $items.Count
    $i = 0
    
    foreach ($item in $items) {
        $i++
        $isLast = ($i -eq $total)
        $connector = if ($isLast) { "└── " } else { "├── " }
        $newPrefix = if ($isLast) { "$Prefix    " } else { "$Prefix│   " }
        
        $emoji = if ($item.PSIsContainer) { "📁 " } else { "📄 " }
        Write-Output "$Prefix$connector$emoji$($item.Name)"
        
        if ($item.PSIsContainer) {
            Show-Tree -Path $item.FullName -Prefix $newPrefix
        }
    }
}

# Header
$header = @"
╔══════════════════════════════════════════════════════════════════╗
║  ECOCHATBOT-MARCX · ESTRUTURA GERADA AUTOMATICAMENTE             ║
║  Gerado em: $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")                              ║
╚══════════════════════════════════════════════════════════════════╝

"@

$header | Out-File -FilePath $saida -Encoding UTF8

# Gerar árvore
Write-Output "E:\EcoChatBot-MA" | Out-File -FilePath $saida -Append -Encoding UTF8
Show-Tree -Path $raiz | Out-File -FilePath $saida -Append -Encoding UTF8

Write-Host "✅ Árvore gerada em: $saida" -ForegroundColor Green
Write-Host "📄 Arquivo: $saida"