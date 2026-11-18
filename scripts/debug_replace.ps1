$f = "d:\Drone Projects\AOG India\index.html"
$c = [System.IO.File]::ReadAllText($f)
$old = "AOG India Esports"
$new = "AOG India eSports"
$r = ""
$r += "old[10]=" + [int]($old[10]) + " new[10]=" + [int]($new[10]) + "`n"
$e = [regex]::Escape($old)
$r += "escaped: $e`n"
$ms = [regex]::Matches($c, $e)
$r += "matches: " + $ms.Count + "`n"
if ($ms.Count -gt 0) {
    $m = $ms[0]
    $r += "match val: " + $m.Value + "`n"
    $mv = $m.Value
    foreach ($ch in $mv.ToCharArray()) { $r += "[" + [int]$ch + "]" }
    $r += "`n"
    $eq = ($mv -ceq $old)
    $r += "ceq: $eq`n"
    $r += "Replace test: " + $mv.Replace($old, $new) + "`n"
}
[System.IO.File]::WriteAllText("d:\Drone Projects\AOG India\update_log.txt", $r)
