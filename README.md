# midas_blue.ksy

Kaitai Struct definition for the Midas BLUE binary file format. Handles type 1000–6000 files, both IEEE (big-endian) and EEEI (little-endian) byte orders, extended header keyword parsing with 8-byte alignment, and all the standard adjunct subtypes.

## Usage

Compile the `.ksy` to your target language with `ksc`:

```
ksc -t python midas_blue.ksy
```

Then use the generated parser:

```python
from kaitaistruct import KaitaiStream
from midas_blue import MidasBlue

with open("myfile.tmp", "rb") as f:
    m = MidasBlue(KaitaiStream(f))

print(m.header.type)       # e.g. file_type.type_1000_1d
print(m.header.format)     # e.g. "CF"
print(m.adjunct.xstart)    # adjunct fields vary by type
```

## Tests

Requires Python 3, pytest, hypothesis, and the [kaitaistruct runtime:](https://kaitai.io/)

```
pip install kaitaistruct pytest hypothesis
ksc -t python midas_blue.ksy
pytest
```

Integration tests run against the sample files in `files/`. Property-based tests use Hypothesis to fuzz the parser against randomly generated headers, adjuncts, keyword entries, and data blocks.

## File types

| Type | Description |
|------|-------------|
| 1000 | 1-D data (waveforms, time series) |
| 2000 | 2-D framed data |
| 3000 | Record-oriented data |
| 4000 | Key-value pairs |
| 5000 | Modified records |
| 6000 | Descriptor words |

## Format digraph

The two-character `format` field encodes element layout (S=scalar, C=complex, V=vector, …) and data type (B=int8, I=int16, L=int32, F=float32, D=float64, …). For example, `SD` is scalar double, `CF` is complex float.
