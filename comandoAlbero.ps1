function Get-Tree {
    param([string]$Path = ".", [string]$Indent = "")
    $lines = @()
    Get-ChildItem $Path | ForEach-Object {
        if ($_.Name -eq "venv" -or $_.Name -eq ".github") { return }
        if ($_.PSIsContainer) {
            $lines += "$Indent+ $($_.Name)"
            $lines += Get-Tree -Path $_.FullName -Indent "$Indent  "
        } elseif ($_.Extension -eq '.py' -and $_.Name -ne '__init__.py') {
            $lines += "$Indent- $($_.Name)"
        }
    }
    return $lines
}
Get-Tree | Out-File -FilePath albero.txt -Encoding utf8