meta:
  id: midas_blue
  file-extension: tmp
seq:
  - id: version
    type: str
    size: 4
    encoding: ASCII
  - id: head_rep
    type: str
    size: 4
    encoding: ASCII
  - id: data_rep
    type: str
    size: 4
    encoding: ASCII
  - id: header
    type: fixed_header_body
    size: 244
instances:
  adjunct:
    pos: 256
    size: 256
    type:
      switch-on: header.type
      cases:
        'file_type::type_1000_1d': adjunct_1000
        'file_type::type_2000_2d_framed': adjunct_2000
        'file_type::type_3000_records': adjunct_3000
        'file_type::type_4000_key_value': adjunct_4000
        'file_type::type_5000_records_mod': adjunct_5000
        'file_type::type_6000_desc_words': adjunct_6000
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
      endian:
        switch-on: _root.head_rep
        cases:
          '"IEEE"': be
          '"EEEI"': le
    seq:
      - id: detached
        type: s4
      - id: protected
        type: s4
      - id: pipe
        type: s4
      - id: ext_start
        type: s4
      - id: ext_size
        type: s4
      - id: data_start
        type: f8
      - id: data_size
        type: f8
      - id: type
        type: s4
        enum: file_type
      - id: format
        type: str
        size: 2
        encoding: ASCII
      - id: flagmask
        type: s2
      - id: timecode
        type: f8
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
      - id: keywords
        size: 92
    instances:
      format_size:
        value: format.substring(0, 1)
      format_type:
        value: format.substring(1, 2)
  adjunct_1000:
    meta:
      endian:
        switch-on: _root.head_rep
        cases:
          '"IEEE"': be
          '"EEEI"': le
    seq:
      - id: xstart
        type: f8
      - id: xdelta
        type: f8
      - id: xunits
        type: s4
        enum: unit_code
  adjunct_2000:
    meta:
      endian:
        switch-on: _root.head_rep
        cases:
          '"IEEE"': be
          '"EEEI"': le
    seq:
      - id: xstart
        type: f8
      - id: xdelta
        type: f8
      - id: xunits
        type: s4
        enum: unit_code
      - id: subsize
        type: s4
      - id: ystart
        type: f8
      - id: ydelta
        type: f8
      - id: yunits
        type: s4
        enum: unit_code
  adjunct_3000:
    meta:
      endian:
        switch-on: _root.head_rep
        cases:
          '"IEEE"': be
          '"EEEI"': le
    seq:
      - id: xstart
        type: f8
      - id: xdelta
        type: f8
      - id: xunits
        type: s4
        enum: unit_code
      - id: subsize
        type: s4
      - id: ystart
        type: f8
      - id: ydelta
        type: f8
      - id: yunits
        type: s4
        enum: unit_code
      - id: record_length
        type: s4
  adjunct_4000:
    meta:
      endian:
        switch-on: _root.head_rep
        cases:
          '"IEEE"': be
          '"EEEI"': le
    seq:
      - id: vrec_size
        type: s4
      - id: reserved
        size: 252
  adjunct_5000:
    meta:
      endian:
        switch-on: _root.head_rep
        cases:
          '"IEEE"': be
          '"EEEI"': le
    seq:
      - id: xstart
        type: f8
      - id: xdelta
        type: f8
      - id: xunits
        type: s4
        enum: unit_code
      - id: subsize
        type: s4
      - id: ystart
        type: f8
      - id: ydelta
        type: f8
      - id: yunits
        type: s4
        enum: unit_code
      - id: record_length
        type: s4
  adjunct_6000:
    meta:
      endian:
        switch-on: _root.head_rep
        cases:
          '"IEEE"': be
          '"EEEI"': le
    seq:
      - id: raw_data
        size: 256
  adjunct_unknown:
    seq:
      - id: raw_data
        size: 256
  extended_header_block:
    meta:
      endian:
        switch-on: _root.head_rep
        cases:
          '"IEEE"': be
          '"EEEI"': le
    seq:
      - id: entries
        type: keyword_entry
        repeat: eos
  keyword_entry:
    meta:
      endian:
        switch-on: _root.head_rep
        cases:
          '"IEEE"': be
          '"EEEI"': le
    seq:
      - id: lkey
        type: u4
      - id: lext
        type: u2
      - id: ltag
        type: u1
      - id: kw_type
        type: str
        size: 1
        encoding: ASCII
      - id: value
        size: lkey - lext
      - id: tag
        type: str
        size: ltag
        encoding: ASCII
      - id: padding
        size: (8 - ((4 + 2 + 1 + 1 + (lkey - lext) + ltag) % 8)) % 8
enums:
  file_type:
    1000: type_1000_1d
    2000: type_2000_2d_framed
    3000: type_3000_records
    4000: type_4000_key_value
    5000: type_5000_records_mod
    6000: type_6000_desc_words
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
    12: latitude
    13: longitude
    14: altitude
    15: power
    16: temperature
    17: density
    18: velocity
    19: angle
    20: phase
    21: weight
    22: voltage
    23: current
    24: pressure
  format_size_code:
    0x53: scalar      # S - 1 element
    0x43: complex      # C - 2 elements
    0x56: vector       # V - 3 elements
    0x51: quad         # Q - 4 elements
    0x4D: matrix       # M - 9 elements (3x3)
    0x54: transform    # T - 16 elements (4x4)
    0x31: n1           # 1
    0x32: n2           # 2
    0x33: n3           # 3
    0x34: n4           # 4
    0x35: n5           # 5
    0x36: n6           # 6
    0x37: n7           # 7
    0x38: n8           # 8
    0x39: n9           # 9
    0x58: n10          # X - 10 elements
    0x41: n32          # A - 32 elements
  format_type_code:
    0x42: int8         # B - 1 byte
    0x49: int16        # I - 2 bytes
    0x4C: int32        # L - 4 bytes
    0x58: int64        # X - 8 bytes
    0x46: float32      # F - 4 bytes
    0x44: float64      # D - 8 bytes
    0x41: ascii        # A - 1 byte
