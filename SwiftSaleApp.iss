;--------------------------------
; SwiftSaleApp Inno Setup Script
;--------------------------------

[Setup]
; Application metadata
AppName=SwiftSaleApp
AppVersion=3.1              
DefaultDirName={userappdata}\SwiftSaleApp
DefaultGroupName=SwiftSaleApp
OutputBaseFilename=SwiftSaleApp_3.1_installer
Compression=lzma
SolidCompression=yes
AllowNoIcons=yes

; Install per-user without requiring administrative privileges
PrivilegesRequired=lowest

; Branding: application icon (ICO) and wizard banner (BMP)
SetupIconFile=swiftsale_logo.ico
WizardImageFile=wizard_banner.bmp

; Display settings
DisableDirPage=no
DisableProgramGroupPage=no
UninstallDisplayIcon={app}\SwiftSaleApp_3.1.exe

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Main executable
Source: "C:\Users\lovei\SCD_SALES\swiftsaleapp\dist\SwiftSaleApp\SwiftSaleApp_3.1.exe"; DestDir: "{app}"; Flags: ignoreversion
; Internal folder (all dependencies, data files, databases, etc.)
Source: "C:\Users\lovei\SCD_SALES\swiftsaleapp\dist\SwiftSaleApp\_internal\*"; DestDir: "{app}\_internal"; Flags: recursesubdirs createallsubdirs ignoreversion
; Include branding assets in the installation folder
Source: "swiftsale_logo.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "wizard_banner.bmp"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu entry (per‐user)
Name: "{userprograms}\SwiftSaleApp"; Filename: "{app}\SwiftSaleApp_3.1.exe"
; Optional desktop icon (per‐user, controlled by installer task)
Name: "{userdesktop}\SwiftSaleApp"; Filename: "{app}\SwiftSaleApp_3.1.exe"; Tasks: desktopicon

[Run]
; Launch the application after installation
Filename: "{app}\SwiftSaleApp_3.1.exe"; Description: "Launch SwiftSaleApp"; Flags: nowait postinstall skipifsilent