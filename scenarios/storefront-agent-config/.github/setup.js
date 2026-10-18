// Inert stand-in for a credential harvester (controlloop#444).
//
// The Miasma worm, Mini Shai-Hulud, and CVE-2026-25725 all ran a script
// like this from a committed SessionStart hook on every machine that
// opened the repository. This one reads nothing, sends nothing, and exits.
process.exit(0);
