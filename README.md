# Description

This project is all about porting
[C++ Abseil B-tree](https://github.com/abseil/abseil-cpp) to Python via
[PyCLIF](https://github.com/google/clif).

Python has no built-in balanced tree data structure. If such a data structure
(e.g. B-tree) is implemented in native Python, its performance will suffer
signaficantly. Luckily, With the assistence of [PyCLIF](https://github.com/google/clif),
it would be easy to transform C++ classes and functions to Python ones. Also,
C++ has a large number of well-known third party libraries implementing
balanced trees. This project chooses [C++ Abseil B-tree](https://github.com/abseil/abseil-cpp)
as its underlying implementation, and implements several wrapper classes for
use in Python.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for details.

## License

Apache 2.0; see [`LICENSE`](LICENSE) for details.

## Disclaimer

This project is not an official Google project. It is not supported by Google
and Google specifically disclaims all warranties as to its quality,
merchantability, or fitness for a particular purpose.
