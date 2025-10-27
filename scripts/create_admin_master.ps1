# PowerShell script para criar/promover admin_master usando .env e docker compose
# Uso: powershell -ExecutionPolicy Bypass -File .\scripts\create_admin_master.ps1

$ErrorActionPreference = 'Stop'

# Ajusta o diretório para a raiz do projeto (onde o script está em ./scripts)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Resolve-Path (Join-Path $scriptDir ".."))

# Verifica .env
if (-not (Test-Path ".env")) {
    Write-Error ".env file not found in project root. Copy .env.example to .env and edit values."
    exit 1
}

# Carrega .env (ignora comentários e linhas vazias)
Get-Content .env |
  Where-Object { $_ -and -not ($_.TrimStart().StartsWith('#')) -and ($_.Contains('=')) } |
  ForEach-Object {
    $parts = $_ -split '=',2
    $name = $parts[0].Trim()
    $value = $parts[1].Trim().Trim("'").Trim('"')
    # Define variável de ambiente para o processo atual
    Set-Item -Path "Env:$name" -Value $value
  }

$SERVICE = if ($env:GESTAO_USUARIOS_SERVICE) { $env:GESTAO_USUARIOS_SERVICE } else { 'gestao-usuarios-service' }

Write-Host "Creating/promoting admin_master in service: $SERVICE"

if (-not $env:ADMIN_MASTER_EMAIL -or -not $env:ADMIN_MASTER_PASSWORD -or -not $env:ADMIN_MASTER_CPF) {
    Write-Error "ADMIN_MASTER_EMAIL, ADMIN_MASTER_PASSWORD and ADMIN_MASTER_CPF must be set in .env"
    exit 1
}

# Prepara valores (escapa aspas simples no name)
$adminEmail = $env:ADMIN_MASTER_EMAIL
$adminPwd   = $env:ADMIN_MASTER_PASSWORD
$adminCpf   = $env:ADMIN_MASTER_CPF
$adminName  = if ($env:ADMIN_MASTER_NAME) { $env:ADMIN_MASTER_NAME -replace "'","\\'" } else { 'Admin' }

# Monta script Python
$py = @"
from django.contrib.auth import get_user_model
User = get_user_model()
email = r'{0}'
pwd = r'{1}'
cpf = r'{2}'
name = r'{3}'

u = User.objects.filter(email=email).first()
if not u:
    u = User.objects.create_user(email=email, password=pwd, name=name, cpf=cpf)
else:
    u.cpf = cpf

u.is_admin = True
u.is_admin_master = True
u.is_staff = True
u.is_superuser = True
u.save()
print('created/promoted', u.email, 'cpf=', u.cpf, 'is_admin_master=', u.is_admin_master)
"@ -f $adminEmail, $adminPwd, $adminCpf, $adminName

# Grava arquivo temporário e envia para o stdin do docker
$tmp = [IO.Path]::Combine([IO.Path]::GetTempPath(), ([IO.Path]::GetRandomFileName() + ".py"))
Set-Content -Path $tmp -Value $py -Encoding UTF8

try {
    # Envia conteúdo do arquivo para o comando docker compose exec -T ... python manage.py shell
    Get-Content -Raw $tmp | & docker compose exec -T $SERVICE python manage.py shell
} catch {
    Write-Error "Erro ao executar comando docker: $_"
    throw
} finally {
    Remove-Item -Force $tmp -ErrorAction SilentlyContinue
}

Write-Host "Done. You can now login via the gateway and use the admin token."