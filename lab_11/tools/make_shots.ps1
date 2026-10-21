param(
    [string]$Only = ""
)

$root = "C:\elkin\lab_11"
$shotsDir = Join-Path $root "screens"
$payloadDir = Join-Path $env:TEMP "lab11-payloads"
New-Item -ItemType Directory -Force -Path $payloadDir | Out-Null

$prologue = @"
`$ErrorActionPreference = 'Continue'
`$env:PYTHONIOENCODING = 'utf-8'
`$OutputEncoding = [Console]::OutputEncoding = (New-Object System.Text.UTF8Encoding `$false)
Set-Location 'C:\elkin\lab_11'
"@

$jobs = @(
    @{ Name = "11-01-schema";           Title = "python demo_schema.py";              Body = "python demo_schema.py";                                Wait = 5000;  Rows = 40 },
    @{ Name = "11-02-sql";              Title = "python demo_sql.py - запросы 1-6";   Body = "python demo_sql.py | Select-Object -First 44";         Wait = 5000;  Rows = 40 },
    @{ Name = "11-03-sql";              Title = "python demo_sql.py - запросы 7-15";  Body = "python demo_sql.py | Select-Object -Skip 44 -First 44"; Wait = 5000;  Rows = 40 },
    @{ Name = "11-04-pytest";           Title = "pytest -v";                          Body = "python -m pytest -v";                                  Wait = 9000;  Rows = 40 },
    @{ Name = "11-05-client-list";      Title = "client.py --demo - список книг";     Body = "python init_db.py | Out-Null; python client.py --demo | Select-Object -First 42";        Wait = 7000; Rows = 40 },
    @{ Name = "11-06-client-crud";      Title = "client.py --demo - CRUD";            Body = "python init_db.py | Out-Null; python client.py --demo | Select-Object -Skip 42 -First 42"; Wait = 7000; Rows = 40 },
    @{ Name = "11-07-client-transaction"; Title = "client.py --demo - выдача и возврат"; Body = "python init_db.py | Out-Null; python client.py --demo | Select-Object -Skip 84 -First 42"; Wait = 7000; Rows = 40 },
    @{ Name = "11-08-client-redis";     Title = "client.py --demo - Redis-кэш";       Body = "python init_db.py | Out-Null; python client.py --demo | Select-Object -Skip 126";        Wait = 9000; Rows = 40 },
    @{ Name = "11-09-transaction";      Title = "python demo_transaction.py";         Body = "python init_db.py | Out-Null; python demo_transaction.py"; Wait = 6000; Rows = 40 },
    @{ Name = "11-10-redis";            Title = "python demo_cache.py";               Body = "python demo_cache.py";                                 Wait = 13000; Rows = 44 },
    @{ Name = "11-11-cdn";              Title = "python demo_cdn.py - заголовки";     Body = "python demo_cdn.py | Select-Object -First 44";         Wait = 9000;  Rows = 42 },
    @{ Name = "11-12-cdn-cache";        Title = "python demo_cdn.py - кэш edge";      Body = "python demo_cdn.py | Select-Object -Skip 128";         Wait = 14000; Rows = 42 },
    @{ Name = "11-13-menu";             Title = "client.py - меню";                   Body = "python client.py";                                     Wait = 4000;  Rows = 30 }
)

foreach ($job in $jobs) {
    if ($Only -and -not $job.Name.StartsWith($Only)) { continue }

    $payloadPath = Join-Path $payloadDir ($job.Name + ".ps1")
    $content = $prologue + "`r`n" + $job.Body
    Set-Content -LiteralPath $payloadPath -Value $content -Encoding UTF8

    $out = Join-Path $shotsDir ($job.Name + ".png")
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root "tools\shot.ps1") `
        -Title $job.Title -PayloadFile $payloadPath -Out $out -WaitMs $job.Wait -Rows $job.Rows
    Start-Sleep -Milliseconds 700
}
