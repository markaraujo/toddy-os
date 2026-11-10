"""Resume the failed no-xsltproc Meson setup without extracting or replaying work."""
from pathlib import Path
import hashlib,json,subprocess

def main(recipe):
 w=Path('/build');assert (Path('/src')/'toddy-build.sh').read_text()==recipe
 assert (w/'compile').is_dir() and not (w/'compile/build.ninja').exists() and not (w/'compile/meson-private/coredata.dat').exists()
 assert not (w/'original-tests.exit').exists() and not (w/'stage-results.json').exists() and not list((w/'stage').iterdir())
 old=(w/'compile/meson-logs/meson-log.txt').read_text();assert "Program 'xsltproc' not found or not executable" in old
 assert subprocess.check_output(['pkg-config','--modversion','libxslt'],text=True).strip()=='1.1.45'
 (w/'configuration-1-failed.log').write_text(old)
 guard='[[ $(id -u) == 101 && ! -e /build/compile ]]';assert recipe.count(guard)==1
 selected=recipe.replace(guard,'[[ $(id -u) == 101 && -d /build/compile && ! -e /build/compile/build.ninja ]]',1)
 (w/'configuration-resume.json').write_text(json.dumps({'scope':'Same failed Meson tree after missing owned xsltproc supplied; no application compile/test/stage had occurred. Only initial fresh-directory guard changed, source unchanged.','source_recipe_sha256':hashlib.sha256(recipe.encode()).hexdigest(),'selected_command_sha256':hashlib.sha256(selected.encode()).hexdigest(),'prior_configuration_log_sha256':hashlib.sha256(old.encode()).hexdigest()},indent=2)+'\n')
 subprocess.run(['bash','-c',selected],check=True)
 bad=subprocess.run(['/stage/usr/bin/gnome-terminal','--toddy-invalid-option'],capture_output=True,text=True,timeout=15)
 assert bad.returncode!=0 and 'unknown option' in bad.stderr.lower() and '--toddy-invalid-option' in bad.stderr
 (w/'cli-invalid-verified.json').write_text(json.dumps({'actual_option_error_verified':True,'returncode':bad.returncode,'option':'--toddy-invalid-option','display_or_other_error_not_accepted':True},indent=2)+'\n')
