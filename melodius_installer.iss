; Melodius Inno Setup Script
; Optimized for 3-Port Portable Architecture

#include "app_id.iss"
#define MyAppVersion "1.0.0"

[Setup]
AppName=Melodius
AppId={#MyAppId}
AppVersion={#MyAppVersion}
AppPublisher=MadhushaNirmal
AppPublisherURL=https://github.com/Madhusha2003
AppSupportURL=https://github.com/Madhusha2003/Melodius/issues
AppUpdatesURL=https://github.com/Madhusha2003/Melodius
AppCopyright=Copyright (C) 2024 Madhusha Nirmal
AppContact=https://github.com/Madhusha2003
AppComments=Melodius Desktop Music Player - A modern, high-performance music player.
DefaultDirName={autopf}\Melodius
DefaultGroupName=Melodius
UninstallDisplayIcon={app}\Melodius.exe
Compression=lzma2/ultra64
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=Melodius_Setup
PrivilegesRequired=admin
SetupIconFile=assets\melodius_icon_512.ico
WizardImageFile=assets\melodius_icon_1024.png
WizardSmallImageFile=assets\melodius_icon_512.png
WizardStyle=modern
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany=Madhusha
VersionInfoDescription=Melodius Desktop Music Player
VersionInfoProductName=Melodius
VersionInfoCopyright=Copyright (C) 2024 Madhusha Nirmal
LicenseFile=LICENSE.txt

[Files]
; 1. The Main Launcher
Source: "Melodius.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "melodius_3ports.py"; DestDir: "{app}"; Flags: ignoreversion

; 2. Embedded Python Environment (Crucial for portability)
Source: "python_11\*"; DestDir: "{app}\python_11"; Flags: ignoreversion recursesubdirs createallsubdirs

; 3. FastAPI Backend
Source: "backend\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__,*.pyc,*.pyo,.env"

; 4. Reflex Backend Source (Logic)
Source: "frontend\ui_melodius\*"; DestDir: "{app}\frontend\ui_melodius"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__,*.pyc,*.pyo"
Source: "frontend\rxconfig.py"; DestDir: "{app}\frontend"; Flags: ignoreversion

; 5. Pre-compiled Frontend Assets (Static Hosting)
Source: "frontend\.web\build\client\*"; DestDir: "{app}\frontend\.web\build\client"; Flags: ignoreversion recursesubdirs createallsubdirs

; 6. Branding Assets (Required for runtime icons)
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; 7. WebView2 Bootstrapper (auto-installs if runtime is missing)
Source: "tools\MicrosoftEdgeWebview2Setup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\Melodius"; FileName: "{app}\Melodius.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\melodius_icon_512.ico"; AppUserModelID: "Madhusha.Melodius.1.2.0"
Name: "{commondesktop}\Melodius"; FileName: "{app}\Melodius.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\melodius_icon_512.ico"; AppUserModelID: "Madhusha.Melodius.1.2.0"

[Run]
; Show a checkbox on the final page to install WebView2 (only visible if not already installed)
Filename: "{tmp}\MicrosoftEdgeWebview2Setup.exe"; Parameters: "/silent /install"; \
  Description: "Install Microsoft Edge WebView2 Runtime (required for Melodius to display its interface)"; \
  StatusMsg: "Installing Microsoft Edge WebView2 Runtime..."; \
  Flags: postinstall runascurrentuser; Check: not IsWebView2Installed

[Code]
function IsWebView2Installed: Boolean;
var
  Version: string;
begin
  // Check for per-machine installation (64-bit)
  Result := RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version);
  if Result then Exit;
  // Check for per-machine installation (32-bit)
  Result := RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version);
  if Result then Exit;
  // Check for per-user installation
  Result := RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  PathContent: string;
  PthFilePath: string;
begin
  if CurStep = ssPostInstall then
  begin
    // Create the .pth file in the correct location
    PthFilePath := ExpandConstant('{app}\python_11\Lib\site-packages\melodius_paths.pth');
    if not DirExists(ExpandConstant('{app}\python_11\Lib\site-packages')) then
      PthFilePath := ExpandConstant('{app}\python_11\site-packages\melodius_paths.pth');
    PathContent := ExpandConstant('{app}') + #13#10 +
                   ExpandConstant('{app}\backend') + #13#10 +
                   ExpandConstant('{app}\frontend');
    SaveStringToFile(PthFilePath, PathContent, False);
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}"