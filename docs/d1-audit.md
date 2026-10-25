# Next milestone: focused read-only identity audit

D1 begins with owners and data flows for application/display name, executable name, Linux application ID, .desktop integration, icon resources, StartupWMClass, D-Bus identity, default data/working directory, About/version identity, and autoupdate endpoint/signing behavior.

Identify exact files, functions, CMake options, generated resources and runtime consumers. Compare stock baseline with proposed Jerkgram identity; verify profile separation, launcher/DBus coexistence and update isolation before any implementation.

Proposals only: product Jerkgram, executable Jerkgram, application ID com.jerkgram.desktop, separate Jerkgram data namespace. The first alpha must not consume official Telegram updates without a separately safe Jerkgram updater. Do not hardcode proposals until the audit resolves all owners.

Deliver an evidence-backed mapping and bounded materialization plan. No name replacement, icons, data migration, updater patch or feature belongs in the builder foundation task.
