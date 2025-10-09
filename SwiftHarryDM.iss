; -------------------------------
; SwiftHarryDM Installer Script
; -------------------------------

[Setup]
AppName=SwiftHarryDM
AppVersion=1.0.0
AppPublisher=Harsh Chaudhary
AppPublisherEmail=harshchy143@gmail.com
AppCopyright=Copyright © 2025 Harsh Chaudhary
AppContact=harshchy143@gmail.com
AppVerName=SwiftHarryDM 1.0.0
DefaultDirName={pf}\SwiftHarryDM
DefaultGroupName=SwiftHarryDM
OutputBaseFilename=SwiftHarryDM_Setup
Compression=lzma
SolidCompression=yes
LicenseFile=EULA.txt
SetupIconFile=app.ico

; Version info for installer EXE
VersionInfoVersion=1.0.0
VersionInfoCompany=Harsh Chaudhary
VersionInfoDescription=SwiftHarryDM Installer
VersionInfoProductName=SwiftHarryDM
VersionInfoCopyright=Copyright © 2025 Harsh Chaudhary
VersionInfoComments=Support: harshchy143@gmail.com

[Files]
; Copy everything from dist folder
Source: "dist\SwiftHarryDM\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\SwiftHarryDM"; Filename: "{app}\SwiftHarryDM.exe"

[Run]
Filename: "{app}\SwiftHarryDM.exe"; Description: "Launch SwiftHarryDM"; Flags: nowait postinstall skipifsilent
