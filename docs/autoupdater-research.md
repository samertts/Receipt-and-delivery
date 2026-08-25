# Auto-updater research notes

- WinSparkle official site: https://winsparkle.org/ — toolkit-independent Windows updater, uses an appcast feed, ships a DLL, and presents native update UI. The project describes itself as MIT-licensed.
- WinSparkle publishing guide: https://winsparkle.org/guides/publishing-updates/ — appcast is RSS 2.0 with Sparkle extensions; appcast, release notes, and downloads should be served over HTTPS. It supports platform-specific Windows entries and installer arguments, including Inno Setup arguments.

Design implication for Receipt-and-delivery: the current app is a PySide6 + PyInstaller EXE with Inno Setup. A separate signed updater/helper or WinSparkle DLL can be used; updates must be served over HTTPS and verified before installation. A GitHub Actions workflow can publish the installer and appcast metadata, but a release should not be auto-installed without signature/hash verification and an explicit user-visible update flow.

- TUFup: https://github.com/dennisvang/tufup — standalone Python application updater using signed metadata and hashes backed by The Update Framework; suitable when stronger rollback/repository security is required, but adds release metadata/key-management complexity.
- WinSparkle: https://github.com/vslavik/winsparkle — Windows-native toolkit-independent updater with appcast support and EdDSA signing tools; suitable for a native update dialog, but Python/PySide6 integration requires shipping and binding a DLL.
- TUF official getting started: https://theupdateframework.io/docs/getting-started/ — TUF provides a framework for adding security properties to existing content delivery systems with Python and Go implementations.

Recommendation for this repository: start with a small separate updater helper that checks a signed HTTPS manifest, verifies SHA-256 and Ed25519 signature, downloads an Inno Setup installer to a temporary directory, verifies again, launches it only after explicit user confirmation, and keeps the existing app running until the installer is ready. Consider TUFup or WinSparkle as a later hardening/UX option after key and release operations are established.
