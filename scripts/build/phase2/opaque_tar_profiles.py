"""Two literal opaque historical copy archives; no user-defined paths/profiles."""
PROFILES={
    'h10':{
        'evidence':'h10-live-root-evidence','evidence_inode':8707431,'copy_inode':8707434,
        'entries':27,'device':64788,'inode':8707439,'bytes':3731302400,'allocated_bytes':3731308544,
        'mtime_ns':1794055054388498491,
        'sha256':'84bbe95d1dbfe3b50a8284e95006b461c7eab6a3a1091e41bfe519a96fa7898d',
        'assembly_sha256':'722a12e94a148bbb28a1d2b8febb3bf04595c7c15aa7057ab58548b78669e016',
        'copy_report_sha256':'6d4bc9ccabe760104b06450bdadfbe4751a6cd07fdb1e7e6d6e73252a5e505ee',
        'manifest':'18-image-manifest.json',
        'manifest_sha256':'4693cfd359b5e0428b24bdaca53d06b561a9c39253dfb013d93f51a17e648398',
        'input_manifest_sha256':'5f12e46d5fcceb6472e1b4d667c6bbfecbbf072403c3887553bd45fedfc36293'},
    'h11':{
        'evidence':'h11-release-root-evidence','evidence_inode':1239390,'copy_inode':1239393,
        'entries':31,'device':64788,'inode':1239398,'bytes':3731630080,'allocated_bytes':3731636224,
        'mtime_ns':1794056866601470587,
        'sha256':'b914a7dc2c0678c4153c2e2f0cdb39d97764c937a3e5b5e139ed3914324a9efe',
        'assembly_sha256':'2d580bb375dcee7a6379398b1fd82bccffb7e462d354b55680337f1e41c506f7',
        'copy_report_sha256':'de1c055e1d65c35d3df046d92fb2f175f20bc8ba97166b7b6600605051fb38d9',
        'manifest':'20-image-manifest.json',
        'manifest_sha256':'74d8ec2db4e97a2f43723c2d1634214c245e6e3bba10cb24bbc3fc3350c27780',
        'input_manifest_sha256':'e7bb4f59cce5775648772ce0f278a5b9c9582e5c88d744c09f54709254bad2c7'}
}


def profile(name):
    if name not in PROFILES:raise ValueError('Unknown fixed opaque archive profile')
    result=dict(PROFILES[name])
    if any(value is None for value in result.values()):raise ValueError('Opaque archive profile identity is incomplete')
    return result
