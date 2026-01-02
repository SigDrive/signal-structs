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
