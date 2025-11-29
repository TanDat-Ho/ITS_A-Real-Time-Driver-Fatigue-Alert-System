;=============================================================================
; NSIS Installer Script for Driver Fatigue Alert System
; Version: 1.0.0
; Author: ITS Project Team
;=============================================================================

; Modern UI 2
!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "WinVer.nsh"

; Application Information
!define APP_NAME "Driver Fatigue Alert System"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "ITS Project Team"
!define APP_URL "https://github.com/TanDat-Ho/ITS_A-Real-Time-Driver-Fatigue-Alert-System"
!define APP_SUPPORT_URL "https://github.com/TanDat-Ho/ITS_A-Real-Time-Driver-Fatigue-Alert-System/issues"
!define APP_EXECUTABLE "DriverFatigueAlert.exe"

; Build Information
!define BUILD_DIR "..\dist\DriverFatigueAlert"
!define SOURCE_DIR ".."
!define ASSETS_DIR "..\assets"
!define CONFIG_DIR "..\config"

; Registry Keys
!define REG_UNINSTALL "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
!define REG_APP_PATH "Software\${APP_PUBLISHER}\${APP_NAME}"

; Installer Configuration
Name "${APP_NAME}"
OutFile "${APP_NAME}_Setup_v${APP_VERSION}.exe"
Unicode True
RequestExecutionLevel admin
InstallDir "$PROGRAMFILES\${APP_NAME}"
InstallDirRegKey HKLM "${REG_APP_PATH}" "InstallLocation"

; Version Information
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "ProductVersion" "${APP_VERSION}"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "FileDescription" "${APP_NAME} Installer"
VIAddVersionKey "FileVersion" "1.0.0.0"
VIAddVersionKey "LegalCopyright" "© 2025 ${APP_PUBLISHER}"

; Modern UI Configuration
!define MUI_ABORTWARNING
!define MUI_ICON "${ASSETS_DIR}\icon\app_icon.ico"
!define MUI_UNICON "${ASSETS_DIR}\icon\app_icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "${ASSETS_DIR}\images\installer_header.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "${ASSETS_DIR}\images\installer_welcome.bmp"
!define MUI_COMPONENTSPAGE_SMALLDESC

; Pages
!define MUI_WELCOMEPAGE_TITLE "Welcome to ${APP_NAME} Setup"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of ${APP_NAME}.$\r$\n$\r$\nClick Next to continue."
!insertmacro MUI_PAGE_WELCOME

!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY

; Start Menu Configuration
!define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKLM"
!define MUI_STARTMENUPAGE_REGISTRY_KEY "${REG_APP_PATH}"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "StartMenuFolder"
Var StartMenuFolder
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder

!insertmacro MUI_PAGE_INSTFILES

; Finish Page Configuration
!define MUI_FINISHPAGE_TITLE "Installation Complete"
!define MUI_FINISHPAGE_TEXT "${APP_NAME} has been successfully installed on your computer.$\r$\n$\r$\nClick Finish to close this wizard."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXECUTABLE}"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${APP_NAME}"
!define MUI_FINISHPAGE_LINK "Visit the ${APP_NAME} website"
!define MUI_FINISHPAGE_LINK_LOCATION "${APP_URL}"
!insertmacro MUI_PAGE_FINISH

; Uninstaller Pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installation Types
InstType "Full Installation"
InstType "Minimal Installation"

; Installer Sections
Section "Core Application" SecCore
    SectionIn RO 1 2
    
    ; Set output path
    SetOutPath "$INSTDIR"
    
    ; Check if application is running
    FindProcDLL::FindProc "${APP_EXECUTABLE}"
    IntCmp $R0 1 0 continueInstall continueInstall
        MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
            "${APP_NAME} is currently running. Please close it and try again." \
            /SD IDCANCEL IDOK continueInstall
        Abort
    continueInstall:
    
    ; Copy application files
    DetailPrint "Installing application files..."
    File /r "${BUILD_DIR}\*"
    
    ; Create AppData directory and copy config
    CreateDirectory "$APPDATA\${APP_NAME}"
    SetOutPath "$APPDATA\${APP_NAME}"
    File /r "${CONFIG_DIR}\*"
    
    ; Create log directory
    CreateDirectory "$APPDATA\${APP_NAME}\log"
    CreateDirectory "$APPDATA\${APP_NAME}\output"
    CreateDirectory "$APPDATA\${APP_NAME}\output\snapshots"
    CreateDirectory "$APPDATA\${APP_NAME}\output\screenshots"
    
    ; Registry entries
    WriteRegStr HKLM "${REG_APP_PATH}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "${REG_APP_PATH}" "Version" "${APP_VERSION}"
    WriteRegStr HKLM "${REG_APP_PATH}" "Publisher" "${APP_PUBLISHER}"
    
    ; Uninstaller registry entries
    WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "${REG_UNINSTALL}" "Publisher" "${APP_PUBLISHER}"
    WriteRegStr HKLM "${REG_UNINSTALL}" "URLInfoAbout" "${APP_URL}"
    WriteRegStr HKLM "${REG_UNINSTALL}" "HelpLink" "${APP_SUPPORT_URL}"
    WriteRegStr HKLM "${REG_UNINSTALL}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "${REG_UNINSTALL}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
    WriteRegStr HKLM "${REG_UNINSTALL}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "${REG_UNINSTALL}" "DisplayIcon" "$INSTDIR\${APP_EXECUTABLE}"
    WriteRegDWORD HKLM "${REG_UNINSTALL}" "NoModify" 1
    WriteRegDWORD HKLM "${REG_UNINSTALL}" "NoRepair" 1
    
    ; Calculate installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "${REG_UNINSTALL}" "EstimatedSize" "$0"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
SectionEnd

Section "Desktop Shortcut" SecDesktop
    SectionIn 1
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}" "" "$INSTDIR\${APP_EXECUTABLE}" 0
SectionEnd

Section "Start Menu Shortcuts" SecStartMenu
    SectionIn 1
    
    !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\${APP_NAME}.lnk" "$INSTDIR\${APP_EXECUTABLE}" "" "$INSTDIR\${APP_EXECUTABLE}" 0
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\Uninstall ${APP_NAME}.lnk" "$INSTDIR\uninstall.exe"
    
    ; Create additional shortcuts
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\Configuration Folder.lnk" "$APPDATA\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\User Guide.lnk" "$INSTDIR\docs\USER_GUIDE.md"
    
    !insertmacro MUI_STARTMENU_WRITE_END
    
SectionEnd

Section "Visual C++ Redistributable" SecVCRedist
    SectionIn 1
    
    ; Check if Visual C++ 2019+ redistributable is installed
    ReadRegStr $0 HKLM "SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" "Version"
    StrCmp $0 "" installVCRedist skipVCRedist
    
    installVCRedist:
        DetailPrint "Installing Visual C++ Redistributable..."
        ; Download and install VC++ redistributable
        ; Note: You would need to include the redistributable installer
        MessageBox MB_OK "Please ensure Visual C++ Redistributable 2019+ is installed for proper operation."
        Goto vcredistEnd
    
    skipVCRedist:
        DetailPrint "Visual C++ Redistributable already installed"
    
    vcredistEnd:
    
SectionEnd

Section "File Associations" SecFileAssoc
    SectionIn 1
    
    ; Register file associations for .fatigue files (if any)
    WriteRegStr HKCR ".fatigue" "" "FatigueDetection.Config"
    WriteRegStr HKCR "FatigueDetection.Config" "" "Fatigue Detection Configuration"
    WriteRegStr HKCR "FatigueDetection.Config\DefaultIcon" "" "$INSTDIR\${APP_EXECUTABLE},0"
    WriteRegStr HKCR "FatigueDetection.Config\shell\open\command" "" '$INSTDIR\${APP_EXECUTABLE} "%1"'
    
SectionEnd

; Section Descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} "Core application files (required)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "Creates a shortcut on the desktop"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} "Creates shortcuts in the Start Menu"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecVCRedist} "Installs Visual C++ Redistributable (recommended)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecFileAssoc} "Associates .fatigue files with the application"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Installer Functions
Function .onInit
    ; Check Windows version
    ${IfNot} ${AtLeastWin7}
        MessageBox MB_OK "This application requires Windows 7 or later."
        Abort
    ${EndIf}
    
    ; Check for previous installation
    ReadRegStr $R0 HKLM "${REG_UNINSTALL}" "UninstallString"
    StrCmp $R0 "" done
    
    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
        "${APP_NAME} is already installed. $\n$\nClick 'OK' to remove the previous version or 'Cancel' to cancel this upgrade." \
        /SD IDCANCEL IDOK uninst
    Abort
    
    uninst:
        ClearErrors
        ExecWait '$R0 /S'
        
        IfErrors no_remove_uninstaller done
            no_remove_uninstaller:
    
    done:
    
FunctionEnd

; Uninstaller Section
Section "Uninstall"
    
    ; Check if application is running
    FindProcDLL::FindProc "${APP_EXECUTABLE}"
    IntCmp $R0 1 0 continueUninstall continueUninstall
        MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
            "${APP_NAME} is currently running. Please close it and try again." \
            /SD IDCANCEL IDOK continueUninstall
        Abort
    continueUninstall:
    
    ; Remove application files
    DetailPrint "Removing application files..."
    RMDir /r "$INSTDIR"
    
    ; Ask about user data
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "Do you want to remove user configuration and log files?$\n$\nThis will delete all your settings and history." \
        /SD IDNO IDYES removeUserData IDNO keepUserData
    
    removeUserData:
        DetailPrint "Removing user data..."
        RMDir /r "$APPDATA\${APP_NAME}"
        Goto afterUserData
    
    keepUserData:
        DetailPrint "Keeping user data..."
    
    afterUserData:
    
    ; Remove shortcuts
    !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
    
    Delete "$SMPROGRAMS\$StartMenuFolder\*.lnk"
    RMDir "$SMPROGRAMS\$StartMenuFolder"
    Delete "$DESKTOP\${APP_NAME}.lnk"
    
    ; Remove registry entries
    DeleteRegKey HKLM "${REG_UNINSTALL}"
    DeleteRegKey HKLM "${REG_APP_PATH}"
    
    ; Remove file associations
    DeleteRegKey HKCR ".fatigue"
    DeleteRegKey HKCR "FatigueDetection.Config"
    
    ; Remove uninstaller
    Delete "$INSTDIR\uninstall.exe"
    
SectionEnd

; Uninstaller Functions
Function un.onInit
    MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 \
        "Are you sure you want to completely remove ${APP_NAME} and all of its components?" \
        /SD IDYES IDYES +2
    Abort
FunctionEnd

Function un.onUninstSuccess
    HideWindow
    MessageBox MB_ICONINFORMATION|MB_OK \
        "${APP_NAME} was successfully removed from your computer." \
        /SD IDOK
FunctionEnd
