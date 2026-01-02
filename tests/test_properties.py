"""Property-based tests for the Midas BLUE Kaitai Struct parser."""
import struct
import sys
import os
import math

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from kaitaistruct import KaitaiStream
from io import BytesIO

# Add project root to path so we can import the generated parser
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from midas_blue import MidasBlue


# --- Strategies ---

HEAD_REPS = st.sampled_from(["IEEE", "EEEI"])
DATA_REPS = st.sampled_from(["IEEE", "EEEI"])

# s4 range: -2^31 to 2^31-1
S4 = st.integers(min_value=-(2**31), max_value=2**31 - 1)
# s2 range: -2^15 to 2^15-1
S2 = st.integers(min_value=-(2**15), max_value=2**15 - 1)
# f8: finite doubles only (no NaN/Inf to allow == comparison)
F8 = st.floats(allow_nan=False, allow_infinity=False, width=64)

# Valid 2-char ASCII format digraphs
FORMAT_SIZE_CHARS = list("SCVQMT123456789XA")
FORMAT_TYPE_CHARS = list("BILXFDA")
FORMAT_DIGRAPH = st.builds(
    lambda s, t: s + t,
    st.sampled_from(FORMAT_SIZE_CHARS),
    st.sampled_from(FORMAT_TYPE_CHARS),
)

# 92 bytes of random keyword data
KEYWORDS = st.binary(min_size=92, max_size=92)


@st.composite
def midas_blue_header_fields(draw):
    """Generate a dict of all 24 fixed header field values."""
    head_rep = draw(HEAD_REPS)
    data_rep = draw(DATA_REPS)
    return {
        "version": "BLUE",
        "head_rep": head_rep,
        "data_rep": data_rep,
        "detached": draw(S4),
        "protected": draw(S4),
        "pipe": draw(S4),
        "ext_start": draw(S4),
        "ext_size": draw(S4),
        "data_start": draw(F8),
        "data_size": draw(F8),
        "type": draw(S4),
        "format": draw(FORMAT_DIGRAPH),
        "flagmask": draw(S2),
        "timecode": draw(F8),
        "inlet": draw(S2),
        "outlets": draw(S2),
        "outmask": draw(S4),
        "pipeloc": draw(S4),
        "pipesize": draw(S4),
        "in_byte": draw(F8),
        "out_byte": draw(F8),
        "outbytes": [draw(F8) for _ in range(8)],
        "keylength": draw(S4),
        "keywords": draw(KEYWORDS),
    }


def build_midas_blue_bytes(fields):
    """Build a 512-byte Midas BLUE file from field values."""
    endian = ">" if fields["head_rep"] == "IEEE" else "<"
    buf = bytearray(512)

    # Endian-neutral string fields (offsets 0-11)
    buf[0:4] = fields["version"].encode("ASCII")
    buf[4:8] = fields["head_rep"].encode("ASCII")
    buf[8:12] = fields["data_rep"].encode("ASCII")

    # Endian-dependent numeric fields (offsets 12-255)
    struct.pack_into(f"{endian}i", buf, 12, fields["detached"])
    struct.pack_into(f"{endian}i", buf, 16, fields["protected"])
    struct.pack_into(f"{endian}i", buf, 20, fields["pipe"])
    struct.pack_into(f"{endian}i", buf, 24, fields["ext_start"])
    struct.pack_into(f"{endian}i", buf, 28, fields["ext_size"])
    struct.pack_into(f"{endian}d", buf, 32, fields["data_start"])
    struct.pack_into(f"{endian}d", buf, 40, fields["data_size"])
    struct.pack_into(f"{endian}i", buf, 48, fields["type"])
    buf[52:54] = fields["format"].encode("ASCII")
    struct.pack_into(f"{endian}h", buf, 54, fields["flagmask"])
    struct.pack_into(f"{endian}d", buf, 56, fields["timecode"])
    struct.pack_into(f"{endian}h", buf, 64, fields["inlet"])
    struct.pack_into(f"{endian}h", buf, 66, fields["outlets"])
    struct.pack_into(f"{endian}i", buf, 68, fields["outmask"])
    struct.pack_into(f"{endian}i", buf, 72, fields["pipeloc"])
    struct.pack_into(f"{endian}i", buf, 76, fields["pipesize"])
    struct.pack_into(f"{endian}d", buf, 80, fields["in_byte"])
    struct.pack_into(f"{endian}d", buf, 88, fields["out_byte"])
    for i, val in enumerate(fields["outbytes"]):
        struct.pack_into(f"{endian}d", buf, 96 + i * 8, val)
    struct.pack_into(f"{endian}i", buf, 160, fields["keylength"])
    buf[164:256] = fields["keywords"]

    return bytes(buf)


# Feature: midas-blue-ksy, Property 1: Fixed header field round-trip
class TestFixedHeaderRoundTrip:
    """Property 1: Fixed header field round-trip.

    For any valid 256-byte Midas BLUE fixed header, parsing it with the
    generated parser should produce field values identical to the values
    that were written.
    """

    @given(fields=midas_blue_header_fields())
    @settings(max_examples=200)
    def test_fixed_header_roundtrip(self, fields):
        raw = build_midas_blue_bytes(fields)
        parsed = MidasBlue(KaitaiStream(BytesIO(raw)))

        # Top-level string fields
        assert parsed.version == fields["version"]
        assert parsed.head_rep == fields["head_rep"]
        assert parsed.data_rep == fields["data_rep"]

        # Numeric fields in the header subtype
        h = parsed.header
        assert h.detached == fields["detached"]
        assert h.protected == fields["protected"]
        assert h.pipe == fields["pipe"]
        assert h.ext_start == fields["ext_start"]
        assert h.ext_size == fields["ext_size"]
        assert h.data_start == fields["data_start"]
        assert h.data_size == fields["data_size"]
        assert h.type == fields["type"]
        assert h.format == fields["format"]
        assert h.flagmask == fields["flagmask"]
        assert h.timecode == fields["timecode"]
        assert h.inlet == fields["inlet"]
        assert h.outlets == fields["outlets"]
        assert h.outmask == fields["outmask"]
        assert h.pipeloc == fields["pipeloc"]
        assert h.pipesize == fields["pipesize"]
        assert h.in_byte == fields["in_byte"]
        assert h.out_byte == fields["out_byte"]
        for i in range(8):
            assert h.outbytes[i] == fields["outbytes"][i]
        assert h.keylength == fields["keylength"]
        assert h.keywords == fields["keywords"]


# Feature: midas-blue-ksy, Property 2: Header byte order correctness
class TestHeaderByteOrder:
    """Property 2: Header byte order correctness.

    For any valid Midas BLUE file where head_rep is either IEEE or EEEI,
    all numeric fields in the fixed header should be interpreted using the
    byte order indicated by head_rep, regardless of data_rep.
    """

    @given(
        head_rep=HEAD_REPS,
        data_rep=DATA_REPS,
        detached=S4,
        ext_start=S4,
        data_start=F8,
        type_val=S4,
        flagmask=S2,
        timecode=F8,
        keylength=S4,
    )
    @settings(max_examples=200)
    def test_header_byte_order(
        self, head_rep, data_rep, detached, ext_start,
        data_start, type_val, flagmask, timecode, keylength,
    ):
        """Write known values with head_rep endianness, use a different
        data_rep, and verify the parser reads header fields correctly."""
        endian = ">" if head_rep == "IEEE" else "<"
        buf = bytearray(512)

        # String fields (endian-neutral)
        buf[0:4] = b"BLUE"
        buf[4:8] = head_rep.encode("ASCII")
        buf[8:12] = data_rep.encode("ASCII")

        # Write numeric fields using head_rep byte order
        struct.pack_into(f"{endian}i", buf, 12, detached)
        struct.pack_into(f"{endian}i", buf, 24, ext_start)
        struct.pack_into(f"{endian}d", buf, 32, data_start)
        struct.pack_into(f"{endian}i", buf, 48, type_val)
        buf[52:54] = b"SF"
        struct.pack_into(f"{endian}h", buf, 54, flagmask)
        struct.pack_into(f"{endian}d", buf, 56, timecode)
        struct.pack_into(f"{endian}i", buf, 160, keylength)

        parsed = MidasBlue(KaitaiStream(BytesIO(bytes(buf))))
        h = parsed.header

        # Verify values match what was written, proving head_rep
        # controls header byte order independent of data_rep
        assert h.detached == detached
        assert h.ext_start == ext_start
        assert h.data_start == data_start
        assert h.type == type_val
        assert h.flagmask == flagmask
        assert h.timecode == timecode
        assert h.keylength == keylength
