# DeviceDiag034:0.6.3also rejected on physical phone
- Stop blind large APK rebuilds: generic phone error remains unconfirmed. Build tiny separate diagnostic/installer using existing downloaded0.6.3.
- No INTERNET permission; inspect only explicitly chosen file, installed package signatures/version, OS/ABI; no chat data.
- Verify exact expected SHA/size before offering install. Session API still requires normal Android permission/user confirmation and never bypasses signatures. Capture status+legacy error+message locally for user to share explicitly.
- Never uninstall existing app or erase conversations. Same target-package update; separate helper package.
- Preserve models/old releases unchanged. Build/sign/check tiny helper, test launch in standard emulator, deliver Gofile. Exact physical cause remains pending user report.
