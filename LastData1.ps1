# Отключение реальной защиты в Windows Defender:
Set-MpPreference -DisableRealtimeMonitoring $true

# Отключение Tamper Protection (Для этого требуется Windows 10 Pro или Enterprise):
Set-MpPreference -DisableTamperProtection $true

# Добавление C:\ в исключения:
Add-MpPreference -ExclusionPath "C:\"

# Добавление папки Downloads в исключения
$downloadsPath = [System.IO.Path]::Combine([System.Environment]::GetFolderPath("UserProfile"), "Downloads")
Add-MpPreference -ExclusionPath $downloadsPath

# Добавление расширения .exe в исключения:
Add-MpPreference -ExclusionExtension ".exe"

# Дополнительно можно выключить Windows Defender (Требует администраторских прав):
Set-MpPreference -DisableRealtimeMonitoring $true
Set-MpPreference -MAPSReporting Disabled
Set-MpPreference -SubmitSamplesConsent NeverSend
Stop-Service -Name windefend -Force