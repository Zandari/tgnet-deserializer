from dataclasses import dataclass
from typing import Optional, List, BinaryIO, Callable
from pprint import pprint


@dataclass()
class TcpAddress:
    address:    str
    port:       int
    flags:      int
    secret:     str


@dataclass()
class ServerSalt:
    valid_since: int
    valid_until: int
    salt:        int


@dataclass()
class Datacenter:
    config_version:             int
    datacenter_id:              int
    last_init_version:          int
    last_init_media_version:    int
    ipv4:                       List[TcpAddress]
    ipv6:                       List[TcpAddress]
    ipv4_download:              List[TcpAddress]
    ipv6_download:              List[TcpAddress]
    is_cdn_datacenter:          bool
    auth_key_perm:              bytes
    auth_key_temp:              bytes
    auth_key_temp_id:           int
    auth_key_media_temp:        bytes
    auth_key_media_temp_id:     int
    authorized:                 bool    # physically its int32 1 | 0
    server_salts:               List[ServerSalt]
    media_server_salts:         List[ServerSalt]



@dataclass()
class Config:
    config_version:               int
    test_backend:                 bool
    client_blocked:               bool
    last_init_system_langcode:    str
    is_current_datacenter:        bool
    # if is_current_datacenter is True
    current_datacenter:           Optional[Datacenter]       = None
    current_datacenter_id:        Optional[int]              = None
    time_difference:              Optional[int]              = None
    last_dc_update_time:          Optional[int]              = None
    push_session_id:              Optional[int]              = None
    registered_for_internal_push: Optional[bool]             = None
    timestamp:                    Optional[int]              = None
    sessions_count:               Optional[int]              = None
    sessions:                     Optional[List[int]]        = None
    datacenters_count:            Optional[int]              = None
    datacenters:                  Optional[List[Datacenter]] = None


_read_int32 = lambda f: int.from_bytes(f.read(4), "little")
_read_int64 = lambda f: int.from_bytes(f.read(8), "little")
_read_bool  = lambda f: f.read(4) == b'\xb5\x75\x72\x99' 

def _read_str(f):
    length = int.from_bytes(f.read(1), "little")
    string = f.read(length).decode("utf-8")
    f.seek(4 - (length + 1) % 4, 1)
    return string

def _read_array(file: BinaryIO, func: Callable) -> list:
    count = _read_int32(file)
    return [func(file) for _ in range(count)]

def _read_address(file: BinaryIO) -> TcpAddress:
    return TcpAddress(
        address = _read_str(file),
        port    = _read_int32(file),
        flags   = _read_int32(file),
        secret  = _read_str(file)
    )
    

def _read_server_salt(file: BinaryIO) -> ServerSalt:
    return ServerSalt(
        valid_since = _read_int32(file),
        valid_until = _read_int32(file),
        salt        = _read_int64(file)
    )


def _read_datacenter(file: BinaryIO) -> Datacenter:
    return Datacenter(
        config_version             = _read_int32(file),
        datacenter_id              = _read_int32(file),
        last_init_version          = _read_int32(file),
        last_init_media_version    = _read_int32(file),
        ipv4                       = _read_array(file, _read_address),
        ipv6                       = _read_array(file, _read_address),
        ipv4_download              = _read_array(file, _read_address),
        ipv6_download              = _read_array(file, _read_address),
        is_cdn_datacenter          = _read_bool(file),
        auth_key_perm              = file.read(_read_int32(file)),
        auth_key_temp              = file.read(_read_int32(file)),
        auth_key_temp_id           = _read_int64(file),
        auth_key_media_temp        = file.read(_read_int32(file)),
        auth_key_media_temp_id     = _read_int64(file),
        authorized                 = _read_int32(file) == 1,
        server_salts               = _read_array(file, _read_server_salt),
        media_server_salts         = _read_array(file, _read_server_salt)
    ) 
    

def deserialize(filepath: str) -> Config:
    file = open(filepath, "rb")
    file.seek(4, 0)
    conf = Config(
        config_version            = _read_int32(file),
        test_backend              = _read_bool(file),
        client_blocked            = _read_bool(file),
        last_init_system_langcode = _read_str(file),
        is_current_datacenter     = _read_bool(file),
    ) 
    if conf.is_current_datacenter:
        pass
    file.close()
    return conf


if __name__ == "__main__":
    pprint(deserialize("tgnet.dat"))
