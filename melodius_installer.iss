; Melodius Inno Setup Script
; Optimized for 3-Port Portable Architecture

[Setup]
AppName=Melodius
AppVersion=1.2.0
AppPublisher=MadhushaNirmal
AppPublisherURL=https://github.com/Madhusha2003
AppSupportURL=https://github.com/Madhusha2003/Melodius/issues
AppUpdatesURL=https://github.com/Madhusha2003/Melodius
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
VersionInfoVersion=1.2.0
VersionInfoCompany=Madhusha
VersionInfoDescription=Melodius Desktop Music Player
VersionInfoProductName=Melodius
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

[Icons]
Name: "{group}\Melodius"; FileName: "{app}\Melodius.exe"; WorkingDir: "{app}"
Name: "{commondesktop}\Melodius"; FileName: "{app}\Melodius.exe"; WorkingDir: "{app}"

[Run]
Filename: "{app}\Melodius.exe"; Description: "Launch Melodius"; Flags: postinstall nowait

[Code]
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
