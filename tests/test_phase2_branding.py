"""Keep reusable native branding inputs linked, licensed and separate from web art."""
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BrandingInputs(unittest.TestCase):
    def test_payload_has_real_sources_and_no_web_or_mockup_assets(self):
        data = json.loads((ROOT / "assets/brand/gnome/package-map.json").read_text())
        assets = {"assets/brand/" + r["file"]: r for r in json.loads((ROOT / data["source_asset_manifest"]).read_text())}
        blocked = {p for paths in data["excluded_runtime_assets"].values() for p in paths}
        destinations = set()
        for row in data["payload"]:
            self.assertTrue((ROOT / row["source"]).is_file())
            self.assertTrue(row["destination"].startswith("/usr/share/"))
            self.assertNotIn("..", Path(row["destination"]).parts)
            self.assertNotIn(row["destination"], destinations)
            destinations.add(row["destination"])
            self.assertNotIn(row["source"], blocked)
            if row["kind"] == "wallpaper":
                self.assertIn(assets[row["source"]]["role"], {"generated-background", "generated-branded-wallpaper"})
                self.assertEqual(hashlib.sha256((ROOT / row["source"]).read_bytes()).hexdigest(), assets[row["source"]]["sha256"])
        xml = ET.parse(ROOT / "assets/brand/gnome/toddy-backgrounds.xml")
        self.assertEqual({e.text for e in xml.findall("./wallpaper/filename")}, {r["destination"] for r in data["payload"] if r["kind"] == "wallpaper"})
        for control in ("reapply_at_login", "dconf_locks", "global_gtk_css", "shell_extension_required"):
            self.assertFalse(data["defaults"][control])
        self.assertTrue(data["defaults"]["respect_existing_user_values"])

    def test_native_icon_roles_have_retained_provenance(self):
        data = json.loads((ROOT / "ui/phase2/icon-roles.json").read_text())
        provenance = {r["file"]: r for r in json.loads((ROOT / data["provenance_manifest"]).read_text())}
        for role in data["roles"]:
            source = ROOT / role["reference"]
            self.assertEqual(source.stem, role["theme_name"])
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), provenance[source.name]["sha256"])
            self.assertTrue(provenance[source.name]["license"])
            self.assertEqual(role["fallback"], "visible-text-label")

    def test_identity_and_launcher_use_one_namespace_without_a_fake_executable(self):
        identity = json.loads((ROOT / "ui/phase2/identity.json").read_text())
        app = identity["application"]
        self.assertEqual(app["id"], app["icon_name"])
        self.assertTrue(app["id"].startswith("io.github.markaraujo."))
        template = (ROOT / app["desktop_template"]).read_text()
        self.assertIn("Icon=" + app["id"] + "\n", template)
        self.assertIn("Exec=@TODDY_EXECUTABLE@", template)
        self.assertNotIn("pkexec", template)
        self.assertFalse(identity["profile_name_changes_application_id"])


if __name__ == "__main__":
    unittest.main()
