# Original-source native packages

`source_packages_native.py` wraps existing reviewed generators in the existing
native archive/ownership/package machinery. It does not grant story acceptance.
The fixed components are branding, installer-branding, assistant, agent, voice and integrations.
The separate existing executor install/check recipe remains unchanged.

After the active compiler releases the global guest lock, use the candidate
verified metadata sync. It selects only exact frozen B01 SHA512 npm archives and
SHA256 supplemental notices; no whole local cache/state directory is transferred.
Native packaging revalidates the complete 88-location/87-archive custody before
staging the agent. Missing custody fails rather than removing dependencies.
Npm supplemental terms have their own `npm-supplemental-notices` directory,
leaving the existing native packager's source-notices inventory namespace intact.
Branding retains its primary project copyright and separate approved-art terms.

For each component, in the designated guarded builder only:

```sh
cd /opt/toddy-build/scripts/build
python3 run_step.py b06-source-branding-install-1 phase2/source-branding-install.sh phase2/source-branding-check.sh --user root
python3 run_step.py b06-source-assistant-install-1 phase2/source-assistant-install.sh phase2/source-assistant-check.sh --user root
python3 run_step.py b06-source-agent-install-1 phase2/source-agent-install.sh phase2/source-agent-check.sh --user root
```

Voice and integrations use their respective fixed names in the same pattern.
These are first-install recipes: any existing stage/package/receipt requires
inspection instead of replay. Every invocation retains full-root verification,
first checks native dependency versions and target reserve, and rejects foreign
payload ownership. Actual archive/installation evidence is produced only by the
native execution. Postchecks compare all staged/installed bytes, executable modes,
root ownership, native package ownership, dependencies and Dpkg audit.

No package generator adds owner state, model weights, credentials, enabled grants
or automatic service activation. The branding slice copies approved art exactly;
it does not qualify defaults/cache rebuilding, small-icon readability or B11.
Optional voice/native catalog, plugin qualification, local model activation,
installed GTK/GDM/Pi/Stop/Keyring behavior and release composition remain separate
real runtime gates. Building these archives is not B06-B13/G2 acceptance.
