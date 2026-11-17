"""Fixed owner-approved temporary MVP host floor; ADR-0251, no environment override."""
STANDARD_HOST_FLOOR=100*1024**3+512*1024**2
MVP_HOST_FLOOR=60*1024**3+512*1024**2

def host_floor(mvp=False):
    if type(mvp) is not bool:raise ValueError('Explicit fixed delivery profile required')
    return MVP_HOST_FLOOR if mvp else STANDARD_HOST_FLOOR
