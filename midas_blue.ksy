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
        1000: adjunct_1000
        2000: adjunct_2000
        3000: adjunct_3000
        4000: adjunct_4000
        5000: adjunct_5000
        6000: adjunct_6000
        _: adjunct_unknown
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
enums:
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
