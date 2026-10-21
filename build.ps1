# Builds DadABase.apk with the Android SDK command-line tools (no Gradle), the same way as storm-table.
#
#   powershell -ExecutionPolicy Bypass -File .\build.ps1 [-VersionCode 2] [-VersionName 1.1]
#
# The bundled jokes come from docs\jokes.json (the same file GitHub Pages serves as the live feed), so every
# build carries the latest jokes as its offline fallback.
#
# Keep dad-a-base.keystore: Android only installs an update over the old app when it is signed with the same key.
param([int]$VersionCode = 1, [string]$VersionName = '1.0')
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$sdk = if ($env:ANDROID_HOME -and (Test-Path $env:ANDROID_HOME)) { $env:ANDROID_HOME } else { Join-Path $env:USERPROFILE 'Android\Sdk' }
$targetSdk = 36
$bt = Join-Path $sdk 'build-tools\36.0.0'
$jar = Join-Path $sdk "platforms\android-$targetSdk\android.jar"
$jdk = Get-ChildItem (Join-Path $env:USERPROFILE 'Android') -Directory -Filter 'jdk-*' -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $jdk) { $jdk = $env:JAVA_HOME }
foreach ($p in @("$bt\aapt2.exe", "$bt\d8.bat", "$bt\zipalign.exe", "$bt\apksigner.bat", $jar, "$jdk\bin\javac.exe")) {
  if (-not (Test-Path $p)) { throw "Missing build tool: $p" }
}
$env:JAVA_HOME = $jdk
$env:Path = "$jdk\bin;$env:Path"

function Run([string]$exe, [string[]]$argList) {
  $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  & $exe @argList
  $code = $LASTEXITCODE; $ErrorActionPreference = $prev
  if ($code -ne 0) { throw "$([IO.Path]::GetFileName($exe)) failed with exit code $code" }
}

$out = Join-Path $root 'build'
if (Test-Path $out) { Remove-Item $out -Recurse -Force }
foreach ($d in 'compiled', 'classes', 'dex', 'assets') { New-Item -ItemType Directory -Force (Join-Path $out $d) | Out-Null }
$utf8 = New-Object System.Text.UTF8Encoding $false

Write-Host '1/5 Page and jokes'
$feed = [IO.File]::ReadAllText((Join-Path $root 'docs\jokes.json'), [Text.Encoding]::UTF8)
$null = $feed | ConvertFrom-Json  # fail the build on a broken feed file
$jokesJs = "window.DAD_JOKES = $feed;`n"
[IO.File]::WriteAllText((Join-Path $root 'web\jokes.js'), $jokesJs, $utf8)  # keeps the browser preview in step
# Assets sit at the top level: aapt2 on Windows writes subfolder entries with a backslash, which Android cannot open.
Copy-Item (Join-Path $root 'web\index.html'), (Join-Path $root 'web\jokes.js') (Join-Path $out 'assets')

Write-Host '2/5 Resources'
Run "$bt\aapt2.exe" @('compile', '--dir', (Join-Path $root 'android\res'), '-o', (Join-Path $out 'compiled\res.zip'))
Run "$bt\aapt2.exe" @('link', '-o', "$out\unsigned.apk", '-I', $jar, '--manifest', (Join-Path $root 'android\AndroidManifest.xml'),
  '-A', "$out\assets", '--min-sdk-version', '24', '--target-sdk-version', "$targetSdk",
  '--version-code', "$VersionCode", '--version-name', $VersionName, (Join-Path $out 'compiled\res.zip'))

Write-Host '3/5 Code'
$sources = @(Get-ChildItem (Join-Path $root 'android\java') -Recurse -Filter *.java | ForEach-Object { $_.FullName })
Run "$jdk\bin\javac.exe" (@('-nowarn', '-Xlint:-options', '-source', '8', '-target', '8', '-bootclasspath', $jar, '-encoding', 'UTF-8', '-d', "$out\classes") + $sources)
$classes = @(Get-ChildItem "$out\classes" -Recurse -Filter *.class | ForEach-Object { $_.FullName })
Run "$bt\d8.bat" (@('--release', '--min-api', '24', '--lib', $jar, '--output', "$out\dex") + $classes)

Write-Host '4/5 Package'
Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem
$zip = [IO.Compression.ZipFile]::Open("$out\unsigned.apk", [IO.Compression.ZipArchiveMode]::Update)
[void][IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, "$out\dex\classes.dex", 'classes.dex')
$zip.Dispose()
Run "$bt\zipalign.exe" @('-p', '-f', '4', "$out\unsigned.apk", "$out\aligned.apk")

Write-Host '5/5 Sign'
$ks = Join-Path $root 'dad-a-base.keystore'
$pw = 'dadabase'
if (-not (Test-Path $ks)) {
  Run "$jdk\bin\keytool.exe" @('-genkeypair', '-keystore', $ks, '-alias', 'dadabase', '-keyalg', 'RSA', '-keysize', '2048',
    '-validity', '10000', '-storepass', $pw, '-keypass', $pw, '-dname', 'CN=Dad-A-Base, O=Personal, C=US')
}
$apk = Join-Path $root 'DadABase.apk'
Run "$bt\apksigner.bat" @('sign', '--ks', $ks, '--ks-key-alias', 'dadabase', '--ks-pass', "pass:$pw", '--key-pass', "pass:$pw", '--out', $apk, "$out\aligned.apk")
Run "$bt\apksigner.bat" @('verify', $apk)
Remove-Item "$apk.idsig" -ErrorAction SilentlyContinue
Write-Host ("Built {0} ({1:N2} MB)" -f $apk, ((Get-Item $apk).Length / 1MB))
