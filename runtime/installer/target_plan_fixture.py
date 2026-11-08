"""B01 no-write Calamares Python-job fixture, not an installer implementation.

All disk/media/account identities below are synthetic. No device discovery,
partitioning, package installation, account creation or acquisition occurs.
"""
import copy
import json
import libcalamares


def plan(candidate):
    if set(candidate) != {"schema_version", "target_serial", "boot_mode", "ai_choice", "extras"}:
        raise ValueError("Unknown or missing plan field")
    if type(candidate["schema_version"]) is not int or candidate["schema_version"] != 1:
        raise ValueError("Unsupported plan version")
    if candidate["target_serial"] != "TODDY-INSTALL-FIXTURE":
        raise ValueError("Only the synthetic fixture target is accepted")
    if candidate["boot_mode"] not in {"uefi", "bios"}:
        raise ValueError("Unsupported fixture boot mode")
    if candidate["ai_choice"] not in {"later", "api", "local"}:
        raise ValueError("Unsupported acquisition choice")
    extras = candidate["extras"]
    if not isinstance(extras, list) or len(extras) != len(set(extras)):
        raise ValueError("Invalid extras")
    if any(item not in {"docker", "opencode"} for item in extras):
        raise ValueError("Unqualified fixture option")
    return {
        "schema_version": 1,
        "scope": "synthetic-no-write",
        "target_serial": candidate["target_serial"],
        "boot_mode": candidate["boot_mode"],
        "offline_desktop": True,
        "offline_setup": True,
        "git_in_base": True,
        "mandatory_agent_backend": False,
        "credentials_in_installer": False,
        "acquisition": candidate["ai_choice"],
        "extras_deferred": sorted(extras),
        "review_in_installed_session": True,
    }


def pretty_name():
    return "Toddy no-write target-plan fixture"


def run():
    candidate = dict(libcalamares.job.configuration)
    result = plan(candidate)
    assert result["scope"] == "synthetic-no-write"
    assert result["mandatory_agent_backend"] is False
    assert result["credentials_in_installer"] is False
    negatives = [
        {"schema_version": 2},
        {"schema_version": True},
        {"target_serial": "TODDY-LFS-TARGET"},
        {"target_serial": "/dev/vda"},
        {"boot_mode": "unknown"},
        {"ai_choice": "hosted-required"},
        {"extras": ["mise"]},
        {"extras": ["docker", "docker"]},
        {"password": "fixture-only"},
    ]
    for change in negatives:
        invalid = copy.deepcopy(candidate)
        invalid.update(change)
        try:
            plan(invalid)
        except ValueError:
            continue
        raise AssertionError("Invalid plan accepted: " + repr(change))
    result["negative_cases"] = len(negatives)
    libcalamares.globalstorage.insert("toddyFixturePlanJson", json.dumps(
        result, sort_keys=True, separators=(",", ":"), allow_nan=False))
    return None
