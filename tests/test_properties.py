"""Property-based tests for the Midas BLUE Kaitai Struct parser."""
import struct
import sys
import os
from io import BytesIO

from hypothesis import given, settings
from hypothesis import strategies as st
from kaitaistruct import KaitaiStream

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


# Fixed header field round-trip
class TestFixedHeaderRoundTrip:
    """Fixed header field round-trip.

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


# Header byte order correctness
class TestHeaderByteOrder:
    """Header byte order correctness.

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


# --- Adjunct header helpers ---

UNIT_CODES = st.integers(min_value=0, max_value=24)
FILE_TYPES = st.sampled_from([1000, 2000, 3000, 4000, 5000, 6000])


def build_adjunct_1000(endian, xstart, xdelta, xunits):
    """Build 256-byte adjunct for type 1000."""
    buf = bytearray(256)
    struct.pack_into(f"{endian}d", buf, 0, xstart)
    struct.pack_into(f"{endian}d", buf, 8, xdelta)
    struct.pack_into(f"{endian}i", buf, 16, xunits)
    return bytes(buf)


def build_adjunct_2000(endian, xstart, xdelta, xunits, subsize, ystart, ydelta, yunits):
    """Build 256-byte adjunct for type 2000."""
    buf = bytearray(256)
    struct.pack_into(f"{endian}d", buf, 0, xstart)
    struct.pack_into(f"{endian}d", buf, 8, xdelta)
    struct.pack_into(f"{endian}i", buf, 16, xunits)
    struct.pack_into(f"{endian}i", buf, 20, subsize)
    struct.pack_into(f"{endian}d", buf, 24, ystart)
    struct.pack_into(f"{endian}d", buf, 32, ydelta)
    struct.pack_into(f"{endian}i", buf, 40, yunits)
    return bytes(buf)


def build_adjunct_3000(endian, xstart, xdelta, xunits, subsize, ystart, ydelta, yunits, record_length):
    """Build 256-byte adjunct for type 3000."""
    buf = bytearray(256)
    struct.pack_into(f"{endian}d", buf, 0, xstart)
    struct.pack_into(f"{endian}d", buf, 8, xdelta)
    struct.pack_into(f"{endian}i", buf, 16, xunits)
    struct.pack_into(f"{endian}i", buf, 20, subsize)
    struct.pack_into(f"{endian}d", buf, 24, ystart)
    struct.pack_into(f"{endian}d", buf, 32, ydelta)
    struct.pack_into(f"{endian}i", buf, 40, yunits)
    struct.pack_into(f"{endian}i", buf, 44, record_length)
    return bytes(buf)


def build_adjunct_4000(endian, vrec_size):
    """Build 256-byte adjunct for type 4000."""
    buf = bytearray(256)
    struct.pack_into(f"{endian}i", buf, 0, vrec_size)
    return bytes(buf)


def build_file_with_adjunct(head_rep, file_type, adjunct_bytes):
    """Build a 512-byte Midas BLUE file with given type and adjunct bytes."""
    endian = ">" if head_rep == "IEEE" else "<"
    buf = bytearray(512)
    buf[0:4] = b"BLUE"
    buf[4:8] = head_rep.encode("ASCII")
    buf[8:12] = b"IEEE"  # data_rep doesn't matter for this test
    # type field at offset 48
    struct.pack_into(f"{endian}i", buf, 48, file_type)
    # format field at offset 52
    buf[52:54] = b"SF"
    # Write adjunct at offset 256
    buf[256:512] = adjunct_bytes
    return bytes(buf)


# Adjunct header dispatch by file type
class TestAdjunctDispatch:
    """Adjunct header dispatch by file type.

    For any valid Midas BLUE file with a type field in {1000, 2000, 3000,
    4000, 5000, 6000}, the parser should read the adjunct header using the
    subtype corresponding to that file type, and all fields within that
    subtype should match the values written.
    """

    @given(head_rep=HEAD_REPS, xstart=F8, xdelta=F8, xunits=UNIT_CODES)
    @settings(max_examples=200)
    def test_adjunct_1000(self, head_rep, xstart, xdelta, xunits):
        """Type 1000: xstart, xdelta, xunits."""
        endian = ">" if head_rep == "IEEE" else "<"
        adjunct = build_adjunct_1000(endian, xstart, xdelta, xunits)
        raw = build_file_with_adjunct(head_rep, 1000, adjunct)
        parsed = MidasBlue(KaitaiStream(BytesIO(raw)))
        adj = parsed.adjunct
        assert isinstance(adj, MidasBlue.Adjunct1000)
        assert adj.xstart == xstart
        assert adj.xdelta == xdelta
        assert adj.xunits == MidasBlue.UnitCode(xunits)

    @given(
        head_rep=HEAD_REPS, xstart=F8, xdelta=F8, xunits=UNIT_CODES,
        subsize=S4, ystart=F8, ydelta=F8, yunits=UNIT_CODES,
    )
    @settings(max_examples=200)
    def test_adjunct_2000(self, head_rep, xstart, xdelta, xunits, subsize, ystart, ydelta, yunits):
        """Type 2000: xstart, xdelta, xunits, subsize, ystart, ydelta, yunits."""
        endian = ">" if head_rep == "IEEE" else "<"
        adjunct = build_adjunct_2000(endian, xstart, xdelta, xunits, subsize, ystart, ydelta, yunits)
        raw = build_file_with_adjunct(head_rep, 2000, adjunct)
        parsed = MidasBlue(KaitaiStream(BytesIO(raw)))
        adj = parsed.adjunct
        assert isinstance(adj, MidasBlue.Adjunct2000)
        assert adj.xstart == xstart
        assert adj.xdelta == xdelta
        assert adj.xunits == MidasBlue.UnitCode(xunits)
        assert adj.subsize == subsize
        assert adj.ystart == ystart
        assert adj.ydelta == ydelta
        assert adj.yunits == MidasBlue.UnitCode(yunits)

    @given(
        head_rep=HEAD_REPS, xstart=F8, xdelta=F8, xunits=UNIT_CODES,
        subsize=S4, ystart=F8, ydelta=F8, yunits=UNIT_CODES, record_length=S4,
    )
    @settings(max_examples=200)
    def test_adjunct_3000(self, head_rep, xstart, xdelta, xunits, subsize, ystart, ydelta, yunits, record_length):
        """Type 3000: xstart, xdelta, xunits, subsize, ystart, ydelta, yunits, record_length."""
        endian = ">" if head_rep == "IEEE" else "<"
        adjunct = build_adjunct_3000(endian, xstart, xdelta, xunits, subsize, ystart, ydelta, yunits, record_length)
        raw = build_file_with_adjunct(head_rep, 3000, adjunct)
        parsed = MidasBlue(KaitaiStream(BytesIO(raw)))
        adj = parsed.adjunct
        assert isinstance(adj, MidasBlue.Adjunct3000)
        assert adj.xstart == xstart
        assert adj.xdelta == xdelta
        assert adj.xunits == MidasBlue.UnitCode(xunits)
        assert adj.subsize == subsize
        assert adj.ystart == ystart
        assert adj.ydelta == ydelta
        assert adj.yunits == MidasBlue.UnitCode(yunits)
        assert adj.record_length == record_length

    @given(head_rep=HEAD_REPS, vrec_size=S4)
    @settings(max_examples=200)
    def test_adjunct_4000(self, head_rep, vrec_size):
        """Type 4000: vrec_size and reserved."""
        endian = ">" if head_rep == "IEEE" else "<"
        adjunct = build_adjunct_4000(endian, vrec_size)
        raw = build_file_with_adjunct(head_rep, 4000, adjunct)
        parsed = MidasBlue(KaitaiStream(BytesIO(raw)))
        adj = parsed.adjunct
        assert isinstance(adj, MidasBlue.Adjunct4000)
        assert adj.vrec_size == vrec_size
        assert len(adj.reserved) == 252

    @given(
        head_rep=HEAD_REPS, xstart=F8, xdelta=F8, xunits=UNIT_CODES,
        subsize=S4, ystart=F8, ydelta=F8, yunits=UNIT_CODES, record_length=S4,
    )
    @settings(max_examples=200)
    def test_adjunct_5000(self, head_rep, xstart, xdelta, xunits, subsize, ystart, ydelta, yunits, record_length):
        """Type 5000: same layout as 3000."""
        endian = ">" if head_rep == "IEEE" else "<"
        adjunct = build_adjunct_3000(endian, xstart, xdelta, xunits, subsize, ystart, ydelta, yunits, record_length)
        raw = build_file_with_adjunct(head_rep, 5000, adjunct)
        parsed = MidasBlue(KaitaiStream(BytesIO(raw)))
        adj = parsed.adjunct
        assert isinstance(adj, MidasBlue.Adjunct5000)
        assert adj.xstart == xstart
        assert adj.xdelta == xdelta
        assert adj.xunits == MidasBlue.UnitCode(xunits)
        assert adj.subsize == subsize
        assert adj.ystart == ystart
        assert adj.ydelta == ydelta
        assert adj.yunits == MidasBlue.UnitCode(yunits)
        assert adj.record_length == record_length

    @given(head_rep=HEAD_REPS, raw_data=st.binary(min_size=256, max_size=256))
    @settings(max_examples=200)
    def test_adjunct_6000(self, head_rep, raw_data):
        """Type 6000: 256 bytes of raw data."""
        raw = build_file_with_adjunct(head_rep, 6000, raw_data)
        parsed = MidasBlue(KaitaiStream(BytesIO(raw)))
        adj = parsed.adjunct
        assert isinstance(adj, MidasBlue.Adjunct6000)
        assert adj.raw_data == raw_data


# Format digraph extraction
class TestFormatDigraphExtraction:
    """Format digraph extraction.

    For any valid 2-character format digraph string, the parser should
    extract the first character as the size code and the second character
    as the type code, such that recombining them produces the original
    digraph.
    """

    @given(
        head_rep=HEAD_REPS,
        size_char=st.sampled_from(FORMAT_SIZE_CHARS),
        type_char=st.sampled_from(FORMAT_TYPE_CHARS),
    )
    @settings(max_examples=200)
    def test_format_digraph_extraction(
        self, head_rep, size_char, type_char
    ):
        """Generate files with random format digraphs, verify
        format_size and format_type extract the correct characters."""
        digraph = size_char + type_char
        endian = ">" if head_rep == "IEEE" else "<"
        buf = bytearray(512)
        buf[0:4] = b"BLUE"
        buf[4:8] = head_rep.encode("ASCII")
        buf[8:12] = b"IEEE"
        struct.pack_into(f"{endian}i", buf, 48, 1000)
        buf[52:54] = digraph.encode("ASCII")

        parsed = MidasBlue(KaitaiStream(BytesIO(bytes(buf))))
        h = parsed.header

        assert h.format == digraph
        assert h.format_size == size_char
        assert h.format_type == type_char
        assert h.format_size + h.format_type == digraph


# Data block positioning and content
class TestDataBlockPositioning:
    """Data block positioning and content.

    For any valid Midas BLUE file with known data_start, data_size, and
    data content, the parser's data block should start at exactly
    data_start bytes from the beginning of the file, have a length of
    exactly data_size bytes, and contain byte content identical to what
    was written at that region.
    """

    @given(
        head_rep=HEAD_REPS,
        data_content=st.binary(min_size=1, max_size=1024),
        data_start_offset=st.integers(min_value=512, max_value=2048),  
    )
    @settings(max_examples=200)
    def test_data_block_positioning(
        self, head_rep, data_content, data_start_offset
    ):
        """Generate files with known data_start, data_size, and data
        content, parse and verify data_block bytes match."""
        endian = ">" if head_rep == "IEEE" else "<"
        data_size = len(data_content)
        total_size = data_start_offset + data_size

        buf = bytearray(total_size)
        # Fixed header
        buf[0:4] = b"BLUE"
        buf[4:8] = head_rep.encode("ASCII")
        buf[8:12] = b"IEEE"
        struct.pack_into(f"{endian}i", buf, 48, 1000)
        buf[52:54] = b"SF"
        struct.pack_into(
            f"{endian}d", buf, 32, float(data_start_offset)
        )
        struct.pack_into(
            f"{endian}d", buf, 40, float(data_size)
        )

        # Write known data content at data_start_offset
        buf[data_start_offset:data_start_offset + data_size] = (
            data_content
        )

        parsed = MidasBlue(KaitaiStream(BytesIO(bytes(buf))))
        assert parsed.data_block == data_content
        assert len(parsed.data_block) == data_size


# --- Extended header helpers ---

# Valid ASCII chars for keyword type field
KW_TYPE_CHARS = list("ABCDILFX")


def build_keyword_entry(endian, tag_str, kw_type_char, value_bytes):
    """Build a single keyword entry with proper 8-byte alignment.

    Returns the raw bytes for one keyword entry.
    """
    ltag = len(tag_str)
    lext = len(value_bytes) + 8  # lext = value_len + fixed portion (4+2+1+1)
    # Wait per the spec: lkey is total keyword length, lext is length of
    # the fixed portion. value size = lkey - lext.
    # So: lkey = lext + len(value_bytes), and lext >= 8 (the fixed 4+2+1+1).
    # The design says: lext (length of fixed portion: 4+2+1+1 = 8)
    # value = lkey - lext bytes
    # So lext = 8 (always), lkey = 8 + len(value_bytes)
    lext = 8
    lkey = lext + len(value_bytes)

    # Build the entry
    buf = bytearray()
    buf += struct.pack(f"{endian}I", lkey)       # lkey: u4
    buf += struct.pack(f"{endian}H", lext)       # lext: u2
    buf += struct.pack("B", ltag)                # ltag: u1
    buf += kw_type_char.encode("ASCII")          # type: 1 byte ASCII
    buf += value_bytes                           # value: lkey - lext bytes
    buf += tag_str.encode("ASCII")               # tag: ltag bytes

    # Padding to 8-byte alignment
    total = 4 + 2 + 1 + 1 + len(value_bytes) + ltag
    pad = (8 - (total % 8)) % 8
    buf += b'\x00' * pad

    return bytes(buf)


@st.composite
def keyword_entries_list(draw):
    """Generate a list of 1-5 keyword entries with random valid fields."""
    n = draw(st.integers(min_value=1, max_value=5))
    entries = []
    for _ in range(n):
        # Tag: 1-20 ASCII uppercase letters
        tag_str = draw(st.text(
            alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            min_size=1, max_size=20,
        ))
        kw_type_char = draw(st.sampled_from(KW_TYPE_CHARS))
        # Value: 1-50 random bytes
        value_bytes = draw(st.binary(min_size=1, max_size=50))
        entries.append((tag_str, kw_type_char, value_bytes))
    return entries


def build_file_with_extended_header(head_rep, entries_data):
    """Build a Midas BLUE file with an extended header containing keyword entries.

    entries_data: list of (tag_str, kw_type_char, value_bytes) tuples
    Returns (file_bytes, entries_data) for verification.
    """
    endian = ">" if head_rep == "IEEE" else "<"

    # Build extended header bytes
    ext_bytes = bytearray()
    for tag_str, kw_type_char, value_bytes in entries_data:
        ext_bytes += build_keyword_entry(endian, tag_str, kw_type_char, value_bytes)

    ext_size = len(ext_bytes)
    # Extended header starts at ext_start * 512. Put it right after HCB.
    ext_start = 1  # = 512 bytes offset
    ext_offset = ext_start * 512

    # data_start after extended header (not accessed in this test)
    data_start = ext_offset + ext_size
    # Align data_start to next byte (no alignment needed, just after ext)
    data_size = 0

    total_size = ext_offset + ext_size
    buf = bytearray(total_size)

    # Fixed header
    buf[0:4] = b"BLUE"
    buf[4:8] = head_rep.encode("ASCII")
    buf[8:12] = b"IEEE"
    struct.pack_into(f"{endian}i", buf, 24, ext_start)
    struct.pack_into(f"{endian}i", buf, 28, ext_size)
    struct.pack_into(f"{endian}d", buf, 32, float(data_start))
    struct.pack_into(f"{endian}d", buf, 40, float(data_size))
    struct.pack_into(f"{endian}i", buf, 48, 1000)
    buf[52:54] = b"SF"

    # Write extended header at offset 512
    buf[ext_offset:ext_offset + ext_size] = ext_bytes

    return bytes(buf)


# Keyword entry parsing with 8-byte alignment
class TestKeywordEntryParsing:
    """Keyword entry parsing with 8-byte alignment.

    For any valid extended header containing a sequence of keyword entries
    (each with random valid lkey, lext, ltag, type, value, and tag), the
    parser should read each entry's fields correctly and advance to the
    next 8-byte-aligned boundary, consuming exactly ext_size bytes total.
    """

    @given(head_rep=HEAD_REPS, entries_data=keyword_entries_list())
    @settings(max_examples=200)
    def test_keyword_entry_alignment(self, head_rep, entries_data):
        """Generate extended headers with random keyword entries, parse
        and verify each entry's fields and 8-byte alignment."""
        raw = build_file_with_extended_header(head_rep, entries_data)
        parsed = MidasBlue(KaitaiStream(BytesIO(raw)))

        ext = parsed.extended_header
        assert ext is not None
        assert len(ext.entries) == len(entries_data)

        for i, (tag_str, kw_type_char, value_bytes) in enumerate(entries_data):
            entry = ext.entries[i]

            # Verify field values match what was written
            lext_expected = 8
            lkey_expected = lext_expected + len(value_bytes)

            assert entry.lkey == lkey_expected
            assert entry.lext == lext_expected
            assert entry.ltag == len(tag_str)
            assert entry.kw_type == kw_type_char
            assert entry.value == value_bytes
            assert entry.tag == tag_str

            # Verify padding achieves 8-byte alignment
            total = 4 + 2 + 1 + 1 + len(value_bytes) + len(tag_str)
            expected_pad = (8 - (total % 8)) % 8
            assert len(entry.padding) == expected_pad
