from pymem import Pymem


def read_pointer(process: Pymem, base_address, offsets):
    address = process.read_ulonglong(base_address)
    for offset in offsets:
        address += offset
        address = process.read_ulonglong(address)
    return address
