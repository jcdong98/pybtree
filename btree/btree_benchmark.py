# Copyright 2024 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Performance benchmark on B-tree in Python.

Expected time complexity (n is the size of the dictionary):

| Dict Type |  Insert   |  Delete   |   Find    | Upper Bound | Iterate |
|:---------:|:---------:|:---------:|:---------:|:-----------:|:-------:|
|  B-tree   | O(log(n)) | O(log(n)) | O(log(n)) |  O(log(n))  |  O(n)   |
|  RBtree   | O(log(n)) | O(log(n)) | O(log(n)) |  O(log(n))  |  O(n)   |
|   Hash    |   O(1)    |   O(1)    |   O(1)    |    O(n)     |  O(n)   |

Elapsed time (Unit: second) on the following benchmark, tested on my personal
work station:

|     Dict Type      |  Insert  |  Delete |   Find  | Upper Bound | Iterate* |
|:------------------:|:--------:|:-------:|:-------:|:-----------:|:--------:|
| Btree (int to int) |   3.8065 |  1.4116 |  4.4989 |    6.3930   |  4.6000  |
| Btree (int to obj) |   4.1142 |  4.4078 |  5.8344 |    6.9809   |  6.8773  |
| Btree (obj to obj) |  13.4077 |  5.0039 | 15.4327 |   15.9843   | 14.1081  |
|  RBtree in Python  | 152.3779 | 11.6077 | 62.7677 |  139.6448   | 71.3978  |
|   Built-in dict    |   2.0906 |  1.3000 |  5.1655 | Unsupported |  4.8435  |

*: For balanced trees (B-tree and red black tree), iteration is ordered by key,
while iterating over built-in dicts is unordered.
**: Btree involving object is slower than that not involving. That's because
object related operation will be done by Python interpreter instead of C++
native code.

The result shows that:
1. B-tree (implemented in C++, invoked in Python via CLIF) has significant
performance advantages over red black tree (implemented in native Python).
2. B-tree can have similar performance to built-in dict even if the theoretical
time complexity of some operations is worse.
3. As a balanced tree, B-tree can support more different operations than
built-in dict (implemented via a hash table). For example, lower bound, upper
bound, range query and selection, etc. are all operations supported by B-tree
but not supported by built-in dict.
"""

from collections.abc import Iterator, Sequence
import contextlib
import random
import time
from typing import Any

from absl import app
from absl import logging

from python import btree

_MAX_RAND_NUM = 10**9
_TEST_SIZE = 10**7


@contextlib.contextmanager
def _time_it(task_name: str) -> Iterator[None]:
  logging.info('%s: Started...', task_name)
  start_time = time.time()
  try:
    yield
  finally:
    logging.info(
        '%s: Completed. Elapsed time = %.4f s.',
        task_name,
        time.time() - start_time,
    )


def _rand_int(max_value: int = _MAX_RAND_NUM) -> int:
  return random.randint(0, max_value)


def _gen_dicts() -> btree.BtreeMapStr2Object:
  """Generates dictionaries for performance benchmark."""
  btree_int2int = btree.BtreeMapInt2Int()
  btree_int2obj = btree.BtreeMapInt2Object()
  btree_obj2obj = btree.BtreeMapObject2Object()
  builtin_dict = {}

  dict_by_label = btree.BtreeMapStr2Object()
  dict_by_label['B-tree (int to int)'] = btree_int2int
  dict_by_label['B-tree (int to object)'] = btree_int2obj
  dict_by_label['B-tree (object to object)'] = btree_obj2obj
  dict_by_label['Built-in dict'] = builtin_dict
  return dict_by_label


def _iter_items(tree: Any) -> Iterator[Any]:
  it = tree.begin()
  end = tree.end()
  while it != end:
    yield it.deref()
    it.self_inc()


def _bench_insert(dict_by_label: btree.BtreeMapStr2Object):
  """Benchmark on inserting random keys and pairs into the dictionaries."""
  pairs = [(_rand_int(), _rand_int()) for _ in range(_TEST_SIZE)]
  for label, dict_tested in _iter_items(dict_by_label):
    with _time_it(f'Insert - {label}'):
      for key, value in pairs:
        dict_tested[key] = value


def _bench_iter(dict_by_label: btree.BtreeMapStr2Object) -> None:
  """Benchmark on iterating over the dictionaries."""
  for label, dict_tested in _iter_items(dict_by_label):
    if label.endswith('to object)'):
      with _time_it(f'Iterate - {label}'):
        _ = list(_iter_items(dict_tested))
    else:
      with _time_it(f'Iterate - {label}'):
        _ = list(dict_tested.items())


def _bench_find(
    dict_by_label: btree.BtreeMapStr2Object, keys: Sequence[int]
) -> None:
  """Benchmark on finding keys in the dictionaries."""
  for label, dict_tested in _iter_items(dict_by_label):
    with _time_it(f'Find - {label}'):
      _ = [dict_tested[key] for key in keys]


def _bench_upper_bound(
    dict_by_label: btree.BtreeMapStr2Object, keys: Sequence[int]
) -> None:
  """Benchmark on finding the pair with smallest key larger than the give key."""
  for label, dict_tested in _iter_items(dict_by_label):
    if label.startswith('B-tree'):
      with _time_it(f'Upper Bound - {label}'):
        _ = [dict_tested.upper_bound(key).deref() for key in keys]
    # Built-in `dict` does not support upper bound operation within a reasonable
    # time.


def _bench_delete(
    dict_by_label: btree.BtreeMapStr2Object, keys: Sequence[int]
) -> None:
  """Benchmark on deleting keys from the dictionaries."""
  for label, dict_tested in _iter_items(dict_by_label):
    with _time_it(f'Delete - {label}'):
      for key in keys:
        del dict_tested[key]


def main(argv: Sequence[str]) -> None:
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')

  dict_by_label = _gen_dicts()

  # Benchmark on insertion.
  _bench_insert(dict_by_label)

  # Benchmark on iteration.
  _bench_iter(dict_by_label)

  # Benchmark on getting values.
  keys = list(dict_by_label['B-tree (int to int)'].keys())
  random.shuffle(keys)
  _bench_find(dict_by_label, keys)

  # Benchmark on query on closest elements.
  max_key = max(keys)
  _bench_upper_bound(
      dict_by_label, [_rand_int(max_key - 1) for _ in range(_TEST_SIZE)]
  )

  # Benchmark on deletion.
  random.shuffle(keys)
  _bench_delete(dict_by_label, keys)


if __name__ == '__main__':
  app.run(main)
