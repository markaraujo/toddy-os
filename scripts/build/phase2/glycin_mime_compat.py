"""Exact DDS MIME spelling compatibility (ADR0143), same decoder implementation."""
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


def add_dds_decoder_alias(data):
    old=b'"image/x-dds" => Self::new(ImageRsDecoder::Dds('
    new=b'"image/x-dds" | "image/vnd.ms-dds" => Self::new(ImageRsDecoder::Dds('
    assert data.count(old)==1 and new not in data
    return data.replace(old,new)
