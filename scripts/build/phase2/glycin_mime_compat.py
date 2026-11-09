"""Exact DDS canonical MIME alias compatibility (ADR0143), no decoder changes."""
import configparser


def add_dds_canonical_alias(data):
    text=data.decode('utf-8')
    config=configparser.ConfigParser(interpolation=None,strict=True)
    config.read_string(text)
    legacy='loader:image/x-dds';canonical='loader:image/vnd.ms-dds'
    assert legacy in config and canonical not in config
    assert set(config[legacy])=={'exec'}
    executable=config[legacy]['Exec']
    assert executable.startswith('/') and '\n' not in executable and executable.endswith('/glycin-image-rs')
    updated=text.rstrip()+'\n\n['+canonical+']\nExec='+executable+'\n'
    check=configparser.ConfigParser(interpolation=None,strict=True);check.read_string(updated)
    assert set(check)==set(config)|{canonical} and dict(check[canonical])==dict(config[legacy])
    assert all(dict(check[name])==dict(config[name]) for name in config)
    return updated.encode('utf-8')
