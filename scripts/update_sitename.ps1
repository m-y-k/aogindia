$logFile = "d:\Drone Projects\AOG India\update_log.txt"
$lines = @()

$allHtml = Get-ChildItem "d:\Drone Projects\AOG India\*.html" | Select-Object -ExpandProperty FullName
$lines += "Files found: $($allHtml.Count)"

foreach ($file in $allHtml) {
    $content = [System.IO.File]::ReadAllText($file)
    $orig = $content

    # Fix JSON-LD "name": "AOG India Esports"
    $content = $content.Replace('"AOG India Esports"', '"AOG India eSports"')

    # Fix meta content="AOG India Esports"
    $content = $content.Replace('content="AOG India Esports"', 'content="AOG India eSports"')

    # Fix any remaining plain-text occurrences (not inside paths/URLs)
    # e.g. "By AOG India Esports" in descriptions
    $content = [regex]::Replace($content, 'AOG India Esports(?![/.])', 'AOG India eSports')

    if ($content -ne $orig) {
        [System.IO.File]::WriteAllText($file, $content, (New-Object System.Text.UTF8Encoding $false))
        $lines += "UPDATED: $(Split-Path $file -Leaf)"
    } else {
        $lines += "unchanged: $(Split-Path $file -Leaf)"
    }
}

$lines += "--- done ---"
[System.IO.File]::WriteAllLines($logFile, $lines)
