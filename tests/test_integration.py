"""Integration tests for the Midas BLUE Kaitai Struct parser against real test files."""
import struct
import subprocess
import sys
import os

import pytest
from kaitaistruct import KaitaiStream

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from midas_blue import MidasBlue


FILES_DIR = os.path.join(os.path.dirname(__file__), "..", "files")


def parse_file(name):
    """Parse a Midas BLUE file by name from the files/ directory."""
    path = os.path.join(FILES_DIR, name)
    return MidasBlue(KaitaiStream(open(path, "rb")))


# ---------------------------------------------------------------------------
# sin.tmp: fixed header fields
# ---------------------------------------------------------------------------
class TestSinTmp:
    """Verify all fixed header fields are extracted without error from sin.tmp."""

    @pytest.fixture(autouse=True)
    def parsed(self):
        self.p = parse_file("sin.tmp")

    def test_version(self):
        assert self.p.version == "BLUE"

    def test_head_rep(self):
        assert self.p.head_rep == "EEEI"

    def test_data_rep(self):
        assert self.p.data_rep == "EEEI"

    def test_detached(self):
        assert self.p.header.detached == 0

    def test_protected(self):
        assert self.p.header.protected == 0

    def test_pipe(self):
        assert self.p.header.pipe == 0

    def test_ext_start(self):
        assert self.p.header.ext_start == 0

    def test_ext_size(self):
        assert self.p.header.ext_size == 0

    def test_data_start(self):
        assert self.p.header.data_start == 512.0

    def test_data_size(self):
        assert self.p.header.data_size == 32768.0

    def test_type(self):
        assert self.p.header.type == MidasBlue.FileType.type_1000_1d

    def test_format(self):
        assert self.p.header.format == "SD"

    def test_flagmask(self):
        assert self.p.header.flagmask == 0

    def test_timecode(self):
        assert self.p.header.timecode == 0.0

    def test_inlet(self):
        assert self.p.header.inlet == 0

    def test_outlets(self):
        assert self.p.header.outlets == 0

    def test_outmask(self):
        assert self.p.header.outmask == 0

    def test_pipeloc(self):
        assert self.p.header.pipeloc == 0

    def test_pipesize(self):
        assert self.p.header.pipesize == 0

    def test_in_byte(self):
        assert self.p.header.in_byte == 0.0

    def test_out_byte(self):
        assert self.p.header.out_byte == 0.0

    def test_outbytes(self):
        assert self.p.header.outbytes == [0.0] * 8

    def test_keylength(self):
        assert self.p.header.keylength == 19

    def test_keywords_length(self):
        assert len(self.p.header.keywords) == 92

    def test_format_digraph(self):
        assert self.p.header.format_size == "S"
        assert self.p.header.format_type == "D"

    def test_adjunct_type(self):
        adj = self.p.adjunct
        assert isinstance(adj, MidasBlue.Adjunct1000)
        assert adj.xstart == 0.0
        assert adj.xdelta == 1.0
        assert adj.xunits == MidasBlue.UnitCode.none

    def test_data_block(self):
        assert len(self.p.data_block) == 32768

    def test_no_extended_header(self):
        assert self.p.extended_header is None


# ---------------------------------------------------------------------------
# pulse_cx.tmp: fixed header fields
# ---------------------------------------------------------------------------
class TestPulseCxTmp:
    """Verify all fixed header fields are extracted without error from pulse_cx.tmp."""

    @pytest.fixture(autouse=True)
    def parsed(self):
        self.p = parse_file("pulse_cx.tmp")

    def test_version(self):
        assert self.p.version == "BLUE"

    def test_head_rep(self):
        assert self.p.head_rep == "EEEI"

    def test_data_rep(self):
        assert self.p.data_rep == "EEEI"

    def test_detached(self):
        assert self.p.header.detached == 0

    def test_protected(self):
        assert self.p.header.protected == 0

    def test_pipe(self):
        assert self.p.header.pipe == 0

    def test_ext_start(self):
        assert self.p.header.ext_start == 0

    def test_ext_size(self):
        assert self.p.header.ext_size == 0

    def test_data_start(self):
        assert self.p.header.data_start == 512.0

    def test_data_size(self):
        assert self.p.header.data_size == 1600.0

    def test_type(self):
        assert self.p.header.type == MidasBlue.FileType.type_1000_1d

    def test_format(self):
        assert self.p.header.format == "CF"

    def test_flagmask(self):
        assert self.p.header.flagmask == 0

    def test_timecode(self):
        assert self.p.header.timecode == 0.0

    def test_inlet(self):
        assert self.p.header.inlet == 0

    def test_outlets(self):
        assert self.p.header.outlets == 0

    def test_outmask(self):
        assert self.p.header.outmask == 0

    def test_pipeloc(self):
        assert self.p.header.pipeloc == 0

    def test_pipesize(self):
        assert self.p.header.pipesize == 0

    def test_in_byte(self):
        assert self.p.header.in_byte == 0.0

    def test_out_byte(self):
        assert self.p.header.out_byte == 0.0

    def test_outbytes(self):
        assert self.p.header.outbytes == [0.0] * 8

    def test_keylength(self):
        assert self.p.header.keylength == 19

    def test_keywords_length(self):
        assert len(self.p.header.keywords) == 92

    def test_format_digraph(self):
        assert self.p.header.format_size == "C"
        assert self.p.header.format_type == "F"

    def test_adjunct_type(self):
        adj = self.p.adjunct
        assert isinstance(adj, MidasBlue.Adjunct1000)
        assert adj.xstart == 0.0
        assert adj.xdelta == 1.0
        assert adj.xunits == MidasBlue.UnitCode.time

    def test_data_block(self):
        assert len(self.p.data_block) == 1600

    def test_no_extended_header(self):
        assert self.p.extended_header is None


# ---------------------------------------------------------------------------
# keyword_test_file.tmp fixed header + extended header keywords
# ---------------------------------------------------------------------------
class TestKeywordTestFileTmp:
    """Verify fixed header and extended header keyword entries from keyword_test_file.tmp."""

    @pytest.fixture(autouse=True)
    def parsed(self):
        self.p = parse_file("keyword_test_file.tmp")

    # -- Fixed header --

    def test_version(self):
        assert self.p.version == "BLUE"

    def test_head_rep(self):
        assert self.p.head_rep == "EEEI"

    def test_data_rep(self):
        assert self.p.data_rep == "EEEI"

    def test_ext_start(self):
        assert self.p.header.ext_start == 1

    def test_ext_size(self):
        assert self.p.header.ext_size == 224

    def test_data_start(self):
        assert self.p.header.data_start == 512.0

    def test_data_size(self):
        assert self.p.header.data_size == 0.0

    def test_type(self):
        assert self.p.header.type == MidasBlue.FileType.type_1000_1d

    def test_format(self):
        assert self.p.header.format == "SB"

    def test_adjunct_type(self):
        adj = self.p.adjunct
        assert isinstance(adj, MidasBlue.Adjunct1000)
        assert adj.xstart == 0.0
        assert adj.xdelta == 1.0
        assert adj.xunits == MidasBlue.UnitCode.time

    # -- Extended header --

    def test_extended_header_exists(self):
        assert self.p.extended_header is not None

    def test_keyword_count(self):
        assert len(self.p.extended_header.entries) == 10

    def test_keyword_b_test(self):
        e = self.p.extended_header.entries[0]
        assert e.tag == "B_TEST"
        assert e.kw_type == "B"
        assert e.lkey == 16
        assert e.lext == 15
        assert e.ltag == 6
        # value is 1 byte: 0x7b = 123
        assert e.value == b"{"

    def test_keyword_i_test(self):
        e = self.p.extended_header.entries[1]
        assert e.tag == "I_TEST"
        assert e.kw_type == "I"
        assert e.lkey == 16
        assert e.lext == 14
        assert e.ltag == 6
        # value is 2 bytes LE: 1337
        assert struct.unpack("<h", e.value)[0] == 1337

    def test_keyword_l_test(self):
        e = self.p.extended_header.entries[2]
        assert e.tag == "L_TEST"
        assert e.kw_type == "L"
        assert e.lkey == 24
        assert e.lext == 20
        assert e.ltag == 6
        assert struct.unpack("<i", e.value)[0] == 113355

    def test_keyword_x_test(self):
        e = self.p.extended_header.entries[3]
        assert e.tag == "X_TEST"
        assert e.kw_type == "X"
        assert e.lkey == 24
        assert e.lext == 16
        assert e.ltag == 6
        assert struct.unpack("<q", e.value)[0] == 987654321

    def test_keyword_f_test(self):
        e = self.p.extended_header.entries[4]
        assert e.tag == "F_TEST"
        assert e.kw_type == "F"
        assert e.lkey == 24
        assert e.lext == 20
        assert e.ltag == 6
        assert abs(struct.unpack("<f", e.value)[0] - 0.12345) < 1e-4

    def test_keyword_d_test(self):
        e = self.p.extended_header.entries[5]
        assert e.tag == "D_TEST"
        assert e.kw_type == "D"
        assert e.lkey == 24
        assert e.lext == 16
        assert e.ltag == 6
        assert abs(struct.unpack("<d", e.value)[0] - 9.87654321) < 1e-8

    def test_keyword_o_test(self):
        e = self.p.extended_header.entries[6]
        assert e.tag == "O_TEST"
        assert e.kw_type == "O"
        assert e.lkey == 16
        assert e.lext == 15
        assert e.ltag == 6
        assert e.value == b"\xff"

    def test_keyword_string_test(self):
        e = self.p.extended_header.entries[7]
        assert e.tag == "STRING_TEST"
        assert e.kw_type == "A"
        assert e.value == b"Hello World"

    def test_keyword_b_test2(self):
        e = self.p.extended_header.entries[8]
        assert e.tag == "B_TEST2"
        assert e.kw_type == "B"
        assert e.value == b"c"

    def test_keyword_string_test_goodbye(self):
        e = self.p.extended_header.entries[9]
        assert e.tag == "STRING_TEST"
        assert e.kw_type == "A"
        assert e.value == b"Goodbye World"

    def test_keyword_alignment(self):
        """Verify all keyword entries have proper 8-byte alignment padding."""
        for e in self.p.extended_header.entries:
            total = 4 + 2 + 1 + 1 + (e.lkey - e.lext) + e.ltag
            expected_pad = (8 - (total % 8)) % 8
            assert len(e.padding) == expected_pad


# ---------------------------------------------------------------------------
# Cross-validation against MATLAB reference reader
# ---------------------------------------------------------------------------
class TestCrossValidation:
    """Compare parser output against expected values derived from the MATLAB
    reference reader (XMidasBlueReader.m) for each test file.

    The MATLAB reader reads fields using native fread calls with the same
    types and offsets. Expected values here are the ground truth from
    parsing these files with the MATLAB reader.
    """

    def test_sin_tmp_cross_validation(self):
        """Cross-validate sin.tmp: type 1000, SD format, LE."""
        p = parse_file("sin.tmp")
        h = p.header
        # MATLAB: hcb.version = 'BLUE', hcb.head_rep = 'EEEI', hcb.data_rep = 'EEEI'
        assert p.version == "BLUE"
        assert p.head_rep == "EEEI"
        assert p.data_rep == "EEEI"
        # MATLAB: hcb.type = 1000, hcb.format = 'SD'
        assert h.type == MidasBlue.FileType.type_1000_1d
        assert h.format == "SD"
        # MATLAB: hcb.data_start = 512, hcb.data_size = 32768
        assert h.data_start == 512.0
        assert h.data_size == 32768.0
        # MATLAB: hcb.ext_start = 0, hcb.ext_size = 0
        assert h.ext_start == 0
        assert h.ext_size == 0
        # MATLAB: adjunct.xstart = 0, adjunct.xdelta = 1, adjunct.xunits = 0
        adj = p.adjunct
        assert adj.xstart == 0.0
        assert adj.xdelta == 1.0
        assert adj.xunits == MidasBlue.UnitCode.none
        # Data block: 32768 bytes = 4096 SD (scalar double) samples
        assert len(p.data_block) == 32768
        # Verify first sample is a double, sin wave data starts at 1.0
        first_sample = struct.unpack("<d", p.data_block[:8])[0]
        assert abs(first_sample - 1.0) < 1e-10

    def test_pulse_cx_cross_validation(self):
        """Cross-validate pulse_cx.tmp: type 1000, CF format, LE."""
        p = parse_file("pulse_cx.tmp")
        h = p.header
        assert p.version == "BLUE"
        assert p.head_rep == "EEEI"
        assert p.data_rep == "EEEI"
        assert h.type == MidasBlue.FileType.type_1000_1d
        assert h.format == "CF"
        assert h.data_start == 512.0
        assert h.data_size == 1600.0
        assert h.ext_start == 0
        assert h.ext_size == 0
        # MATLAB: adjunct.xstart = 0, adjunct.xdelta = 1, adjunct.xunits = 1 (time)
        adj = p.adjunct
        assert adj.xstart == 0.0
        assert adj.xdelta == 1.0
        assert adj.xunits == MidasBlue.UnitCode.time
        # Data block: 1600 bytes = 200 CF (complex float32) samples (2 floats each)
        assert len(p.data_block) == 1600
        # Pulse signal: first 100 samples are zero, sample 100 is (1.0, 1.0)
        real_0 = struct.unpack("<f", p.data_block[:4])[0]
        imag_0 = struct.unpack("<f", p.data_block[4:8])[0]
        assert real_0 == 0.0
        assert imag_0 == 0.0
        # Sample 100 (offset 800 bytes = 100 * 8)
        real_100 = struct.unpack("<f", p.data_block[800:804])[0]
        imag_100 = struct.unpack("<f", p.data_block[804:808])[0]
        assert abs(real_100 - 1.0) < 1e-6
        assert abs(imag_100 - 1.0) < 1e-6

    def test_keyword_file_cross_validation(self):
        """Cross-validate keyword_test_file.tmp: type 1000, SB format, LE, with keywords."""
        p = parse_file("keyword_test_file.tmp")
        h = p.header
        assert p.version == "BLUE"
        assert p.head_rep == "EEEI"
        assert p.data_rep == "EEEI"
        assert h.type == MidasBlue.FileType.type_1000_1d
        assert h.format == "SB"
        assert h.data_start == 512.0
        assert h.data_size == 0.0
        assert h.ext_start == 1
        assert h.ext_size == 224
        # MATLAB: 10 keyword entries
        ext = p.extended_header
        assert ext is not None
        assert len(ext.entries) == 10
        # MATLAB cross-validation of interpreted keyword values:
        # B_TEST = 123 (int8)
        assert struct.unpack("<b", ext.entries[0].value)[0] == 123
        # I_TEST = 1337 (int16)
        assert struct.unpack("<h", ext.entries[1].value)[0] == 1337
        # L_TEST = 113355 (int32)
        assert struct.unpack("<i", ext.entries[2].value)[0] == 113355
        # X_TEST = 987654321 (int64)
        assert struct.unpack("<q", ext.entries[3].value)[0] == 987654321
        # F_TEST ≈ 0.12345 (float32)
        assert abs(struct.unpack("<f", ext.entries[4].value)[0] - 0.12345) < 1e-4
        # D_TEST ≈ 9.87654321 (float64)
        assert abs(struct.unpack("<d", ext.entries[5].value)[0] - 9.87654321) < 1e-8
        # STRING_TEST = "Hello World" (ASCII)
        assert ext.entries[7].value == b"Hello World"
        # STRING_TEST = "Goodbye World" (ASCII)
        assert ext.entries[9].value == b"Goodbye World"


# ---------------------------------------------------------------------------
# cdif file: type 1001 (non-standard), CF format, with extended header
# ---------------------------------------------------------------------------
class TestCdifFile:
    """Verify the .cdif Midas BLUE file parses correctly."""

    @pytest.fixture(autouse=True)
    def parsed(self):
        self.p = parse_file("2025-06-20_18-35-52_906858500hz.cdif")

    def test_version(self):
        assert self.p.version == "BLUE"

    def test_head_rep(self):
        assert self.p.head_rep == "EEEI"

    def test_data_rep(self):
        assert self.p.data_rep == "EEEI"

    def test_type(self):
        # type 1001 is not in the standard enum, raw int value
        assert self.p.header.type == 1001

    def test_format(self):
        assert self.p.header.format == "CF"

    def test_data_start(self):
        assert self.p.header.data_start == 512.0

    def test_data_size(self):
        assert self.p.header.data_size == 9034936.0

    def test_data_block(self):
        assert len(self.p.data_block) == 9034936

    def test_ext_start(self):
        assert self.p.header.ext_start == 17648

    def test_ext_size(self):
        assert self.p.header.ext_size == 2056

    def test_extended_header_exists(self):
        ext = self.p.extended_header
        assert ext is not None

    def test_keyword_count(self):
        assert len(self.p.extended_header.entries) == 62

    def test_adjunct_is_unknown(self):
        """Type 1001 should fall through to the default adjunct case."""
        adj = self.p.adjunct
        # Should be raw bytes (unknown type), not a named adjunct subtype
        assert hasattr(adj, 'raw_data') or isinstance(adj, bytes) or type(adj).__name__ == 'AdjunctUnknown'

    def test_timecode(self):
        assert self.p.header.timecode == 2381596552.0


# ---------------------------------------------------------------------------
# 9.5  KSY compiles to all targets
# ---------------------------------------------------------------------------
class TestKscCompilation:
    """Validate KSY compiles to all targets with ksc."""

    def test_ksc_all_targets(self):
        """Compile midas_blue.ksy to each supported target and verify exit code 0.

        The 'construct' target is excluded because it does not support
        conditional endianness (switch-on), which is a known ksc limitation.
        """
        ksy_path = os.path.join(os.path.dirname(__file__), "..", "midas_blue.ksy")
        targets = [
            "python", "java", "csharp", "ruby", "go", "javascript",
            "lua", "perl", "php", "nim", "rust", "graphviz", "cpp_stl", "html",
        ]
        failures = []
        for target in targets:
            result = subprocess.run(
                ["ksc", "-t", target, ksy_path],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                failures.append(f"{target}: {result.stderr.strip()}")
        assert not failures, "ksc compilation failures:\n" + "\n".join(failures)
