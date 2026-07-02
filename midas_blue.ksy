meta:
  id: midas_blue
  title: Midas BLUE File Format
  file-extension:
    - tmp
    - blue
    - cdif
    - prm
  # NOTE on byte order: the head_rep field chooses header endianness (IEEE = big,
  # EEEI = little). It cannot be set as a top-level default because Kaitai resolves
  # the root default endian before head_rep is read, so each endian-sensitive type
  # declares it explicitly.
seq:
  - id: version
    type: str
    size: 4
    encoding: ASCII
    doc: File version string; should be "BLUE" (legacy "GOLD" is unsupported).
  - id: head_rep
    type: str
    size: 4
    encoding: ASCII
    doc: Header representation / byte order; e.g. "IEEE" (big) or "EEEI" (little).
  - id: data_rep
    type: str
    size: 4
    encoding: ASCII
    doc: Data-block representation / byte order (independent of head_rep).
  - id: header
    type: fixed_header_body
    size: 244
instances:
  adjunct:
    pos: 256
    size: 256
    doc: |
      Type-specific adjunct header. Dispatched on the file-structure class
      (type / 1000) so that subtypes such as 1001, 2001, 5001, 5010 or 6080
      are parsed with the correct family layout.
    type:
      switch-on: header.type_class
      cases:
        1: adjunct_1000
        2: adjunct_2000
        3: adjunct_3000
        4: adjunct_4000
        5: adjunct_5000
        6: adjunct_6000
        _: adjunct_unknown
  data_block:
    pos: header.data_start.to_i
    size: header.data_size.to_i
  extended_header:
    pos: header.ext_start * 512
    size: header.ext_size
    type: extended_header_block
    if: header.ext_start > 0 and header.ext_size > 0
types:
  fixed_header_body:
    meta:
      endian: &head_endian
        switch-on: _root.head_rep
        cases:
          '"IEEE"': be
          '"EEEI"': le
          '"VAX "': le
          '"CRAY"': be
    seq:
      - id: detached
        type: s4
        doc: Non-zero if the data lives in a separate (detached) file.
      - id: protected
        type: s4
        doc: Non-zero marks the file read-only (soft flag).
      - id: pipe
        type: s4
      - id: ext_start
        type: s4
        doc: Extended-header start, in 512-byte blocks (0 = no extended header).
      - id: ext_size
        type: s4
        doc: Extended-header size in bytes (0 = no extended header).
      - id: data_start
        type: f8
        doc: Data-block offset from start of file, in bytes.
      - id: data_size
        type: f8
        doc: Data-block size in bytes.
      - id: type
        type: s4
        enum: file_type
        doc: File type code; see file_type. type / 1000 gives the structure class.
      - id: format
        type: str
        size: 2
        encoding: ASCII
        doc: Two-character data format digraph (size code + type code).
      - id: flagmask
        type: s2
      - id: timecode
        type: f8
        doc: Epoch time for file data, seconds since 1 Jan 1950.
      - id: inlet
        type: s2
      - id: outlets
        type: s2
      - id: outmask
        type: s4
      - id: pipeloc
        type: s4
      - id: pipesize
        type: s4
      - id: in_byte
        type: f8
      - id: out_byte
        type: f8
      - id: outbytes
        type: f8
        repeat: expr
        repeat-expr: 8
      - id: keylength
        type: s4
        doc: Valid length, in bytes, of the main-header keyword region.
      - id: keywords
        size: 92
        doc: Raw main-header keyword region (ASCII "tag=value\0" pairs).
    instances:
      # Re-read the raw integer type (fixed-header-relative offset 36 = file
      # offset 48) so the structure class can be computed even for type codes
      # that are not named in the file_type enum.
      type_raw:
        pos: 36
        type: s4
      type_class:
        value: type_raw / 1000
        doc: File structure class (type / 1000), selects the adjunct layout.
      format_size:
        value: format.substring(0, 1)
        doc: First format character - element size / multiplier code.
      format_type:
        value: format.substring(1, 2)
        doc: Second format character - atomic data type code.
      keywords_parsed:
        pos: 152
        size: keylength
        type: main_keyword_list
        if: keylength > 0
        doc: |
          Main-header keywords parsed into tag/value string pairs. Each pair is
          stored in the HCB as ASCII "TAG=VALUE" terminated by a NULL byte.
  main_keyword_list:
    seq:
      - id: entries
        type: main_keyword_entry
        repeat: eos
  main_keyword_entry:
    seq:
      - id: tag
        type: str
        encoding: ASCII
        terminator: 0x3d
        doc: Keyword name (text before the first '=').
      - id: value
        type: str
        encoding: ASCII
        terminator: 0
        eos-error: false
        doc: Keyword value (text after '=', up to the NUL terminator).
  adjunct_1000:
    meta:
      endian: *head_endian
    doc: Type 1000 family - one-dimensional homogeneous samples.
    seq:
      - id: xstart
        type: f8
        doc: Abscissa value for the first sample.
      - id: xdelta
        type: f8
        doc: Abscissa interval between samples (1 / sample rate).
      - id: xunits
        type: s4
        enum: unit_code
        doc: Units for xstart / xdelta.
  adjunct_2000:
    meta:
      endian: *head_endian
    doc: Type 2000 family - two-dimensional (framed) homogeneous data.
    seq:
      - id: xstart
        type: f8
        doc: Frame (row) starting value.
      - id: xdelta
        type: f8
        doc: Increment between samples within a frame.
      - id: xunits
        type: s4
        enum: unit_code
      - id: subsize
        type: s4
        doc: Number of data points per frame (row length).
      - id: ystart
        type: f8
        doc: Abscissa (column) start.
      - id: ydelta
        type: f8
        doc: Increment between frames.
      - id: yunits
        type: s4
        enum: unit_code
  adjunct_3000:
    meta:
      endian: *head_endian
    doc: Type 3000 family - record-structured (non-homogeneous) data.
    seq:
      - id: rstart
        type: f8
        doc: Abscissa value for the first record.
      - id: rdelta
        type: f8
        doc: Abscissa distance between records.
      - id: runits
        type: s4
        enum: unit_code
        doc: Units for record abscissa values.
      - id: subrecords
        type: s4
        doc: Number of columns per record (max 26 for the standard adjunct).
      - id: r2start
        type: f8
        doc: Abscissa value for the first column in a record.
      - id: r2delta
        type: f8
        doc: Abscissa distance between record columns.
      - id: r2units
        type: s4
        enum: unit_code
        doc: Units for column abscissa values.
      - id: record_length
        type: s4
        doc: Length of each record in bytes.
      - id: subr
        type: subrec_struct
        repeat: expr
        repeat-expr: 26
        doc: Record column definitions (only the first `subrecords` are valid).
  subrec_struct:
    meta:
      endian: *head_endian
    doc: Type 3000 SUBRECSTRUCT - one record column definition (8 bytes).
    seq:
      - id: name
        type: str
        size: 4
        encoding: ASCII
        doc: Column name (space padded).
      - id: format
        type: str
        size: 2
        encoding: ASCII
        doc: Column data format digraph.
      - id: offset
        type: s2
        doc: Byte offset of the column within the record.
  adjunct_4000:
    meta:
      endian: *head_endian
    doc: |
      Type 4000 - key/value record streams. The abscissa-style fields exist only
      for structural compatibility with other adjuncts and are unused here.
    seq:
      - id: vrstart
        type: f8
        doc: Unused (structural compatibility).
      - id: vrdelta
        type: f8
        doc: Unused (structural compatibility).
      - id: vrunits
        type: s4
        doc: Unused (structural compatibility).
      - id: nrecords
        type: s4
        doc: Number of records; may be <= 0 for fixed-length records.
      - id: vr2start
        type: f8
        doc: Unused (structural compatibility).
      - id: vr2delta
        type: f8
        doc: Unused (structural compatibility).
      - id: vr2units
        type: s4
        doc: Unused (structural compatibility).
      - id: vrecord_length
        type: s4
        doc: |
          Fixed record length. >0: every record has this length; 0: variable,
          scan sequentially; <0: variable, T4INDEX keyword provides offsets.
  adjunct_5000:
    meta:
      endian: *head_endian
    doc: |
      Type 5000 family - record-structured data plus system-modeling parameters
      (state vectors, geodetic positions).
    seq:
      - id: tstart
        type: f8
        doc: Abscissa value for the first record.
      - id: tdelta
        type: f8
        doc: Abscissa distance between records.
      - id: tunits
        type: s4
        enum: unit_code
        doc: Units for record abscissa values.
      - id: components
        type: s4
        doc: Number of columns per record (max 14 for the standard adjunct).
      - id: t2start
        type: f8
        doc: Unused (structural compatibility).
      - id: t2delta
        type: f8
        doc: Unused (structural compatibility).
      - id: t2units
        type: s4
        doc: Unused (structural compatibility).
      - id: record_length
        type: s4
        doc: Length of each record in bytes (sum of component byte sizes).
      - id: comp
        type: comp_struct
        repeat: expr
        repeat-expr: 14
        doc: Record column definitions (only the first `components` are valid).
      - id: quadwords
        type: f8
        repeat: expr
        repeat-expr: 12
        doc: System-modeling frame info; interpretation depends on subtype.
  comp_struct:
    doc: Type 5000 COMPSTRUCT - one record column definition (8 bytes).
    seq:
      - id: name
        type: str
        size: 4
        encoding: ASCII
        doc: Column name (space padded).
      - id: format
        type: str
        size: 2
        encoding: ASCII
        doc: Column data format digraph.
      - id: comp_type
        type: s1
        enum: comp_type_code
        doc: Type of measurement (coordinate system for positional fields).
      - id: units
        type: s1
        enum: unit_code
        doc: Column units.
  adjunct_6000:
    meta:
      endian: *head_endian
    doc: |
      Type 6000 family - record-structured data with fewer restrictions than
      type 3000. The adjunct reuses the type 3000 numeric layout, but its column 
      table is unreliable: the authoritative record layout is carried in the
      SUBREC_DEF extended-header keyword. The raw column region is therefore 
      left undecoded.
    seq:
      - id: rstart
        type: f8
        doc: Abscissa value for the first record.
      - id: rdelta
        type: f8
        doc: Abscissa distance between records.
      - id: runits
        type: s4
        enum: unit_code
      - id: subrecords
        type: s4
        doc: Number of columns per record.
      - id: r2start
        type: f8
      - id: r2delta
        type: f8
      - id: r2units
        type: s4
        enum: unit_code
      - id: record_length
        type: s4
        doc: Length of each record in bytes.
      - id: subr_raw
        size: 208
        doc: Raw column-definition region (see SUBREC_DEF keyword for the truth).
  adjunct_unknown:
    doc: Fallback for unrecognised structure classes.
    seq:
      - id: raw_data
        size: 256
  extended_header_block:
    seq:
      - id: entries
        type: keyword_entry
        repeat: eos
  keyword_entry:
    meta:
      endian: *head_endian
    doc: X-Midas binary extended-header keyword
    seq:
      - id: lkey
        type: u4
        doc: Total length of this keyword entry (header + value + tag + padding).
      - id: lext
        type: u2
        doc: Length of the non-value part (8-byte header + tag + padding).
      - id: ltag
        type: u1
        doc: Length of the keyword tag.
      - id: kw_type
        type: str
        size: 1
        encoding: ASCII
        doc: Data format type of the value; e.g. A, B, I, L, X, F, D.
      - id: value
        size: lkey - lext
        doc: |
          Keyword value, interpreted per kw_type: string types expose `.text`,
          numeric types expose `.values` (an array). The raw bytes remain
          available as `_raw_value`. Unrecognised types stay as raw bytes.
        type:
          switch-on: kw_type
          cases:
            '"A"': kw_value_text
            '"B"': kw_value_s1
            '"I"': kw_value_s2
            '"L"': kw_value_s4
            '"T"': kw_value_s4
            '"X"': kw_value_s8
            '"F"': kw_value_f4
            '"D"': kw_value_f8
      - id: tag
        type: str
        size: ltag
        encoding: ASCII
        doc: Keyword name.
      - id: padding
        size: (8 - ((4 + 2 + 1 + 1 + (lkey - lext) + ltag) % 8)) % 8
        doc: Alignment padding so each entry ends on an 8-byte boundary.
  kw_value_text:
    seq:
      - id: text
        type: str
        size-eos: true
        encoding: ASCII
  kw_value_s1:
    seq:
      - id: values
        type: s1
        repeat: eos
  kw_value_s2:
    meta:
      endian: *head_endian
    seq:
      - id: values
        type: s2
        repeat: expr
        repeat-expr: _io.size / 2
  kw_value_s4:
    meta:
      endian: *head_endian
    seq:
      - id: values
        type: s4
        repeat: expr
        repeat-expr: _io.size / 4
  kw_value_s8:
    meta:
      endian: *head_endian
    seq:
      - id: values
        type: s8
        repeat: expr
        repeat-expr: _io.size / 8
  kw_value_f4:
    meta:
      endian: *head_endian
    seq:
      - id: values
        type: f4
        repeat: expr
        repeat-expr: _io.size / 4
  kw_value_f8:
    meta:
      endian: *head_endian
    seq:
      - id: values
        type: f8
        repeat: expr
        repeat-expr: _io.size / 8
enums:
  # File type codes. type / 1000 gives the structure class.
  file_type:
    1000: type_1000_scalar_1d
    1001: type_1001_amplitude
    1002: type_1002_toa
    1003: type_1003_histogram
    1004: type_1004_burst
    1005: type_1005_multipoint
    1200: type_1200_packetized_1d
    1999: type_1999_connected_points
    2000: type_2000_scalar_2d
    2001: type_2001_frame
    2004: type_2004_burst_2d
    2200: type_2200_packetized_2d
    3000: type_3000_records
    3999: type_3999_param_records
    4000: type_4000_key_value
    5000: type_5000_records_mod
    5001: type_5001_state_vector
    5010: type_5010_geodetic
    6000: type_6000_desc_words
    6001: type_6001_uniform_records
    6002: type_6002_multipoint_records
    6003: type_6003_time_based
    6004: type_6004_time_burst
    6005: type_6005_index
    6080: type_6080_sdds
  # Value unit codes.
  unit_code:
    0: none
    1: time
    2: delay
    3: frequency
    4: time_code
    5: distance
    6: speed
    7: acceleration
    8: jerk
    9: doppler
    10: doppler_rate
    11: energy
    12: power
    13: mass
    14: volume
    15: angular_power_density
    16: integrated_power_density_rad
    17: spatial_power_density
    18: integrated_power_density_m
    19: spectral_power_density
    30: unknown
    31: dimensionless
    32: counts
    33: angle_radians
    34: angle_degrees
    35: relative_power_db
    36: relative_power_dbm
    37: relative_power_dbw
    38: solid_angle
    40: distance_feet
    41: distance_nmi
    42: speed_fps
    43: speed_nmi_s
    44: speed_knots
    45: acceleration_fps2
    46: acceleration_nmi_s2
    47: acceleration_knots_s
    48: acceleration_g
    49: jerk_g_s
    50: rotation_rps
    51: rotation_rpm
    52: angular_velocity_rad_s
    53: angular_velocity_deg_s
    54: angular_acceleration_rad_s2
    55: angular_acceleration_deg_s2
    56: percent
    57: pressure_psi
    58: reserved_58
    59: reserved_59
    60: latitude
    61: longitude
    62: altitude_feet
    63: altitude_meters
  # Type 5000 COMPSTRUCT column type codes.
  comp_type_code:
    0: none
    1: scalar
    2: cartesian
    3: spherical
    4: cylindric
    5: ellipsoid
    6: geodetic
    10: matrix
  # Format size / multiplier codes. Provided for reference;
  # the format field itself is read as a 2-character string.
  format_size_code:
    0x53: scalar      # S - 1 element
    0x43: complex     # C - 2 elements
    0x56: vector      # V - 3 elements
    0x51: quad        # Q - 4 elements
    0x4d: matrix      # M - 9 elements (3x3)
    0x54: transform   # T - 16 elements (4x4)
    0x55: user        # U - user defined (deprecated)
    0x31: n1
    0x32: n2
    0x33: n3
    0x34: n4
    0x35: n5
    0x36: n6
    0x37: n7
    0x38: n8
    0x39: n9
    0x58: n10         # X - 10 elements
    0x41: n32         # A - 32 elements
  # Format atomic type codes.
  format_type_code:
    0x42: int8        # B - 8-bit integer
    0x49: int16       # I - 16-bit integer
    0x4c: int32       # L - 32-bit integer
    0x58: int64       # X - 64-bit integer
    0x46: float32     # F - 32-bit float
    0x44: float64     # D - 64-bit float
    0x50: packed_bits # P - packed bits
    0x4e: nibble      # N - 4-bit integer
    0x4f: offset_byte # O - offset binary
    0x41: ascii       # A - ASCII text
    0x53: utf8        # S - modified UTF-8 (reserved)
    0x54: kw_int32    # T - 32-bit integer (keyword, deprecated)
