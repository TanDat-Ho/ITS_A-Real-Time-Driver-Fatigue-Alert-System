; Driver Fatigue Detection System NSIS Installer Script
; This script creates a Windows installer for the application

!define APP_NAME "Driver Fatigue Detection System"
!define APP_VERSION "1.0.0"
!define PUBLISHER "ITS Project Team"
!define WEB_SITE "https://github.com/your-repo/driver-fatigue-detection"
!define APP_EXE "DriverFatigueAlert.exe"
!define INSTALL_DIR "$PROGRAMFILES64\${APP_NAME}"

; Modern UI 2
!include "MUI2.nsh"
!include "FileFunc.nsh"

; General Settings
Name "${APP_NAME}"
OutFile "..\..\dist\DriverFatigueSetup-${APP_VERSION}.exe"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "InstallDir"
RequestExecutionLevel admin
SetCompressor lzma

; Variables
Var StartMenuFolder

; Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "..\..\assets\icon\app_icon.ico"
!define MUI_UNICON "..\..\assets\icon\app_icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP_NOSTRETCH
!define MUI_WELCOMEFINISHPAGE_BITMAP_NOSTRETCH

; Language Selection Dialog Settings
!define MUI_LANGDLL_REGISTRY_ROOT "HKLM" 
!define MUI_LANGDLL_REGISTRY_KEY "Software\${APP_NAME}" 
!define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY

; Start Menu Folder Page Configuration
!define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKLM" 
!define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\${APP_NAME}" 
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder

!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; Version Information
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "CompanyName" "${PUBLISHER}"
VIAddVersionKey "LegalCopyright" "© 2023 ${PUBLISHER}"
VIAddVersionKey "FileDescription" "${APP_NAME} Installer"
VIAddVersionKey "FileVersion" "${APP_VERSION}"

; Installer Sections
Section "!Core Application" SecCore
    SectionIn RO
    
    SetOutPath "$INSTDIR"
    
    ; Copy main executable and all dependencies
    File /r "..\..\dist\DriverFatigueAlert\*.*"
    
    ; Create application data directory
    CreateDirectory "$APPDATA\DriverFatigueAlert"
    CreateDirectory "$APPDATA\DriverFatigueAlert\config"
    CreateDirectory "$APPDATA\DriverFatigueAlert\logs"
    
    ; Copy default configuration files
    SetOutPath "$APPDATA\DriverFatigueAlert\config"
    File "..\..\config\*.*"
    
    ; Store installation folder
    WriteRegStr HKLM "Software\${APP_NAME}" "InstallDir" $INSTDIR
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Add to Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "HelpLink" "${WEB_SITE}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1
    
    ; Calculate installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "EstimatedSize" "$0"
    
SectionEnd

Section "Desktop Shortcut" SecDesktop
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
SectionEnd

Section "Quick Launch Shortcut" SecQuickLaunch
    CreateShortCut "$QUICKLAUNCH\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
SectionEnd

; Start Menu Shortcuts
Section "Start Menu Shortcuts" SecStartMenu
    !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
        
        CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
        CreateShortCut "$SMPROGRAMS\$StartMenuFolder\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
        CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
        
    !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

; Section descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} "Installs the core application files and dependencies (required)."
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "Creates a desktop shortcut for easy access."
    !insertmacro MUI_DESCRIPTION_TEXT ${SecQuickLaunch} "Creates a quick launch shortcut."
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} "Creates Start Menu shortcuts."
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Uninstaller Section
Section "Uninstall"
    
    ; Remove files and uninstaller
    Delete "$INSTDIR\${APP_EXE}"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR\_internal"
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$QUICKLAUNCH\${APP_NAME}.lnk"
    
    ; Remove Start Menu folder
    !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
    Delete "$SMPROGRAMS\$StartMenuFolder\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk"
    RMDir "$SMPROGRAMS\$StartMenuFolder"
    
    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    DeleteRegKey HKLM "Software\${APP_NAME}"
    
    ; Note: We keep user data in $APPDATA\DriverFatigueAlert
    ; User can manually delete if desired
    
SectionEnd

; Installer Functions
Function .onInit
    ; Language selection
    !insertmacro MUI_LANGDLL_DISPLAY
    
    ; Check if already installed
    ReadRegStr $R0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString"
    StrCmp $R0 "" done
    
    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
    "${APP_NAME} is already installed. $\n$\nClick `OK` to remove the \
    previous version or `Cancel` to cancel this upgrade." \
    IDOK uninst
    Abort
    
    uninst:
        ClearErrors
        Exec $INSTDIR\Uninstall.exe
    
    done:
FunctionEnd

Function un.onInit
    !insertmacro MUI_UNGETLANGUAGE
FunctionEnd
