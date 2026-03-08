# SSH公钥认证修复脚本 - 在目标服务器上以管理员身份运行
# 适用于: 164, 168, 165

Write-Host "===== SSH公钥认证修复脚本 =====" -ForegroundColor Cyan

# 1. 公钥内容
$pubkey = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCY0N9/VBr+aIuPZPPvoj2ENOIgfHxAll7k7wzj5yZ/bEYTfbaKyNALn5IPbevN35iHurvxqDXoMCs4XHYGVywEb254Iuh9mCLkZzNYM1gH14onZfIC8LbaTdkREc17DQDHUeXbICY9zsdPqgJu4ZowWf66lKHsGMoJU8Xpq6S7fe1ZOEbF0C3QUzzO9cCxtWmzrJouVINjEGlPmzzpGYWs0w+BWpuMsPRWD8mVWsaVjO5ti2IaFdPd0Sp8aDmwAfoX9Yxzk5TVOedJ2p8L/pNQDLqOT+c5GeWJHMJGj+Hca1UCl4wZhGHaa3VpZ7TMvTfRsW815Vn9muzLnc9PgUUxNbHOsNPAd8ZmV+ztvbcLMIRR/y2MHRluMQudHgfxGzMhJaNaogMD9BhzHRuef+J3JiIPRQwqvEJTqVs/JS7F6jCoslcx3jCDZNeVeXni59Qeh3sk4XpSMMsGJlsq0rmz9qjvkIFShI1sKRJA/rzb/zbz4UPwM8hr1phPFtxbbyYtUQ0HqZkRt5TW8B6kUd422e+Nr6Fgm7S0+KgkuUdRCScMKu1n6vkpTnC9HBLkX9dZxy7E0L65sLJrK0PUYlac4YcTHTFPXPi0XHfiG7feRi3r01hQ3oBpQaRqaHQNdm4MbYd/vMs2C008rt5hbivA5F5aHJZfwbgFjlSh8X8vKw== auto-generated-key"

# 2. 确保目录存在
$sshDir = "C:\ProgramData\ssh"
if (-not (Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    Write-Host "[OK] 创建目录: $sshDir" -ForegroundColor Green
}

# 3. 写入公钥文件
$keyFile = "$sshDir\administrators_authorized_keys"
Set-Content -Path $keyFile -Value $pubkey -Force
Write-Host "[OK] 写入公钥: $keyFile" -ForegroundColor Green

# 4. 设置权限 - 这是关键步骤
Write-Host "正在设置文件权限..." -ForegroundColor Yellow
icacls $keyFile /inheritance:r | Out-Null
icacls $keyFile /grant "SYSTEM:(F)" | Out-Null
icacls $keyFile /grant "BUILTIN\Administrators:(F)" | Out-Null
Write-Host "[OK] 权限设置完成" -ForegroundColor Green

# 5. 检查sshd_config是否有正确配置
$configFile = "$sshDir\sshd_config"
if (Test-Path $configFile) {
    $config = Get-Content $configFile -Raw

    # 检查是否有Match Group administrators配置
    if ($config -notmatch "Match Group administrators") {
        Write-Host "正在添加administrators组配置..." -ForegroundColor Yellow
        $matchBlock = @"

Match Group administrators
    AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys
"@
        Add-Content -Path $configFile -Value $matchBlock
        Write-Host "[OK] 已添加Match Group administrators配置" -ForegroundColor Green
    } else {
        Write-Host "[OK] sshd_config已包含administrators配置" -ForegroundColor Green
    }
} else {
    Write-Host "[WARN] sshd_config不存在，使用默认配置" -ForegroundColor Yellow
}

# 6. 重启sshd服务
Write-Host "正在重启sshd服务..." -ForegroundColor Yellow
Restart-Service sshd -ErrorAction SilentlyContinue
if ($?) {
    Write-Host "[OK] sshd服务已重启" -ForegroundColor Green
} else {
    Write-Host "[WARN] sshd服务重启失败，请手动重启" -ForegroundColor Yellow
}

# 7. 显示结果
Write-Host ""
Write-Host "===== 配置完成 =====" -ForegroundColor Cyan
Write-Host "公钥文件: $keyFile" -ForegroundColor White
icacls $keyFile
Write-Host ""
Write-Host "请在监控主机上测试SSH连接" -ForegroundColor Yellow
