"""
Binary Specification for CognitiveZip (.czip) Format.
Optimized for random-access chunk decoding and embedded semantic indexing.
"""

import struct

MAGIC_HEADER = b"CZIP\x01\x00"  # 6 bytes
MAGIC_FOOTER = b"CZIPEND\x00"  # 8 bytes

# Footer format: [8 bytes index_offset] [8 bytes index_size] [4 bytes crc32] [8 bytes MAGIC_FOOTER]
# Total footer length = 28 bytes
FOOTER_STRUCT = struct.Struct(">QQI8s")
FOOTER_SIZE = FOOTER_STRUCT.size


class CompressionType:
    STORED = 0
    DEFLATE = 1
    ZSTD = 2
