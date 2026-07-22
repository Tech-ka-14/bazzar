; Bazzar Terminal NSIS installer
; Packages release/win-unpacked into a per-user Windows installer.
; Can be compiled on Windows with NSIS or on Linux with electron-builder's
; bundled makensis binary (no wine required).

Unicode true
SetCompressor /SOLID lzma

!include "MUI2.nsh"

!ifndef APP_NAME
  !define APP_NAME "Bazzar Terminal"
!endif
!ifndef APP_VERSION
  !define APP_VERSION "1.1.0"
!endif
!ifndef APP_PUBLISHER
  !define APP_PUBLISHER "Bazzar"
!endif
!ifndef APP_EXE
  !define APP_EXE "Bazzar Terminal.exe"
!endif
!ifndef SOURCE_DIR
  !define SOURCE_DIR "release/win-unpacked"
!endif
!ifndef OUT_FILE
  !define OUT_FILE "release/Bazzar Terminal Setup ${APP_VERSION}.exe"
!endif

Name "${APP_NAME}"
OutFile "${OUT_FILE}"
InstallDir "$LOCALAPPDATA\Programs\${APP_NAME}"
RequestExecutionLevel user
ShowInstDetails show
ShowUninstDetails show

!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${APP_NAME}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install ${APP_NAME}" SEC_INSTALL
  SetShellVarContext current
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer

  ; Complete Electron runtime, renderer, dependencies, and repository payload.
  File /r "${SOURCE_DIR}/*.*"

  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
  CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0

  WriteUninstaller "$INSTDIR\Uninstall ${APP_NAME}.exe"

  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$\"$INSTDIR\Uninstall ${APP_NAME}.exe$\""
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1
SectionEnd

Section "Uninstall"
  SetShellVarContext current

  Delete "$DESKTOP\${APP_NAME}.lnk"
  Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
  RMDir "$SMPROGRAMS\${APP_NAME}"

  Delete "$INSTDIR\Uninstall ${APP_NAME}.exe"
  RMDir /r "$INSTDIR"

  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
SectionEnd
