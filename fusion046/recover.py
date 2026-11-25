"""Recover the byte-identical Gemma 045 checkpoint from its stored release ZIP."""
import argparse
import hashlib
import os
from pathlib import Path
import struct
import time
from urllib.request import Request, urlopen

RELEASE = 'https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/releases/download/liquid-sense-gemma045'
PARTS = (1_400_000_000, 1_250_853_834)
SHA = 'e6e4528057543f0bdf35305c87b79197c639f2d77ddfcf140745a62f4441703c'
SIZE = 2_645_321_119
NAME = b'LiquidSense-Gemma-045.lsmix'


def request(index, first, last):
    url = f'{RELEASE}/LiquidSense-Gemma-045.zip.part{index + 1:02d}'
    headers = {'Range': f'bytes={first}-{last}', 'Accept-Encoding': 'identity'}
    response = urlopen(Request(url, headers=headers), timeout=40)
    expected = f'bytes {first}-{last}/{PARTS[index]}'
    if response.status != 206 or response.headers.get('Content-Range') != expected:
        response.close()
        raise IOError('The server returned a different archive range')
    return response


def read_range(start, count):
    pieces = []
    for index, first, last in intervals(start, count):
        with request(index, first, last) as response:
            pieces.append(response.read())
    data = b''.join(pieces)
    if len(data) != count:
        raise IOError('Incomplete archive metadata')
    return data


def intervals(start, count):
    end = start + count
    boundary = PARTS[0]
    if start < boundary:
        yield 0, start, min(end, boundary) - 1
    if end > boundary:
        yield 1, max(0, start - boundary), end - boundary - 1


def locate():
    tail = read_range(sum(PARTS) - 22, 22)
    marker, disk, central_disk, _, entries, length, offset, comment = struct.unpack('<4s4H2IH', tail)
    if (marker, disk, central_disk, comment) != (b'PK\x05\x06', 0, 0, 0):
        raise ValueError('Unexpected release ZIP footer')
    central = read_range(offset, length)
    i = 0
    for _ in range(entries):
        record = struct.unpack_from('<4s6H3I5H2I', central, i)
        name_size, extra, note = record[10:13]
        name = central[i + 46:i + 46 + name_size]
        i += 46 + name_size + extra + note
        if record[0] != b'PK\x01\x02':
            raise ValueError('Unexpected ZIP directory record')
        if name == NAME:
            if record[4] != 0 or tuple(record[8:10]) != (SIZE, SIZE):
                raise ValueError('The checkpoint must be stored uncompressed')
            local = record[-1]
            h = read_range(local, 30)
            name_size, extra = struct.unpack_from('<HH', h, 26)
            if not h.startswith(b'PK\x03\x04'):
                raise ValueError('Unexpected ZIP local record')
            return local + 30 + name_size + extra
    raise ValueError('Published checkpoint is missing')


def recover(output):
    offset = locate()
    sha = hashlib.sha256()
    for index, first, end in intervals(offset, SIZE):
        for attempt in range(5):
            try:
                with request(index, first, end) as response:
                    while first <= end:
                        block = response.read(min(4 << 20, end - first + 1))
                        if not block:
                            raise IOError('Truncated checkpoint range')
                        output.write(block)
                        sha.update(block)
                        first += len(block)
                break
            except (OSError, TimeoutError) as error:
                if attempt == 4:
                    raise
                print(f'Resuming part {index + 1} at {first} ({type(error).__name__})', flush=True)
                time.sleep(2)
        print(f'Part {index + 1} copied', flush=True)
    if output.tell() != SIZE or sha.hexdigest() != SHA:
        raise ValueError('Checkpoint SHA-256 differs from the published 045')
    output.flush()
    print(f'Checkpoint verified {SHA}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--memory', action='store_true', help='Write an mmap reference and stay alive until released')
    args = parser.parse_args()
    if args.memory:
        fd = os.memfd_create('liquid-sense-045')
        with os.fdopen(fd, 'wb') as handle:
            recover(handle)
            args.output.write_text(f'/proc/{os.getpid()}/fd/{fd}\n')
            released = args.output.with_suffix('.done')
            for _ in range(3600):
                if released.is_file():
                    break
                time.sleep(1)
    else:
        staging = args.output.with_suffix('.partial')
        with staging.open('wb') as handle:
            recover(handle)
        staging.replace(args.output)
