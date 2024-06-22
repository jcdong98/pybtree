# Copyright 2024 Google LLC
#
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

"""Generates the CLIF file for B-tree."""

import itertools
from typing import TypeAlias, Union

_TEMPLATE_HEADER = """\
from "btree/btree.h":
  namespace `djc::btree`:
"""

_TEMPLATE_SETS = """\
    class `btree_set<{key_c_type}>::iterator` as BtreeSet{KeyType}Iterator:
      def `operator++` as self_inc(self) -> BtreeSet{KeyType}Iterator
      def `operator--` as self_dec(self) -> BtreeSet{KeyType}Iterator
      def `operator*` as deref(self) -> {key_type}
      def `operator==` as __eq__(self, rhs: BtreeSet{KeyType}Iterator) -> bool
      def `operator!=` as __ne__(self, rhs: BtreeSet{KeyType}Iterator) -> bool

    class `btree_set<{key_c_type}>::keys_view_generator` as _BtreeSet{KeyType}KeysView:  # It does not work on `object`.
      class `btree_view` as __iter__:  # It does not work on `object`.
        def __next__(self) -> {key_type}  # It does not work on `object`.

    class `btree_set<{key_c_type}>` as BtreeSet{KeyType}:
      def __init__(self) -> None
      def `_clear` as clear(self) -> None
      def empty(self) -> bool
      def `not_empty` as __bool__(self) -> bool
      def `_contains` as contains(self, key: {key_type}) -> bool
      def `_contains` as __contains__(self, key: {key_type}) -> bool
      def size(self) -> int
      def `size` as __len__(self) -> int
      def `_begin` as begin(self) -> BtreeSet{KeyType}Iterator
      def `_end` as end(self) -> BtreeSet{KeyType}Iterator
      def `_insert` as insert(self, key: {key_type}) -> tuple<BtreeSet{KeyType}Iterator, bool>
      def `_erase` as erase(self, key: {key_type}) -> int
      def remove(self, it: BtreeSet{KeyType}Iterator) -> BtreeSet{KeyType}Iterator
      def `_find` as find(self, key: {key_type}) -> BtreeSet{KeyType}Iterator
      def `_lower_bound` as lower_bound(self, key: {key_type}) -> BtreeSet{KeyType}Iterator
      def `_upper_bound` as upper_bound(self, key: {key_type}) -> BtreeSet{KeyType}Iterator
      class `keys_view` as __iter__:  # It does not work on `object`.
        def __next__(self) -> {key_type}  # It does not work on `object`.
      def keys(self) -> _BtreeSet{KeyType}KeysView  # It does not work on `object`.

    class `btree_multiset<{key_c_type}>::iterator` as BtreeMultiset{KeyType}Iterator:
      def `operator++` as self_inc(self) -> BtreeMultiset{KeyType}Iterator
      def `operator--` as self_dec(self) -> BtreeMultiset{KeyType}Iterator
      def `operator*` as deref(self) -> {key_type}
      def `operator==` as __eq__(self, rhs: BtreeMultiset{KeyType}Iterator) -> bool
      def `operator!=` as __ne__(self, rhs: BtreeMultiset{KeyType}Iterator) -> bool

    class `btree_multiset<{key_c_type}>::keys_view_generator` as _BtreeMultiset{KeyType}KeysView:  # It does not work on `object`.
      class `btree_view` as __iter__:  # It does not work on `object`.
        def __next__(self) -> {key_type}  # It does not work on `object`.

    class `btree_multiset<{key_c_type}>` as BtreeMultiset{KeyType}:
      def __init__(self) -> None
      def `_clear` as clear(self) -> None
      def empty(self) -> bool
      def `not_empty` as __bool__(self) -> bool
      def `_contains` as contains(self, key: {key_type}) -> bool
      def `_contains` as __contains__(self, key: {key_type}) -> bool
      def size(self) -> int
      def `size` as __len__(self) -> int
      def `_begin` as begin(self) -> BtreeMultiset{KeyType}Iterator
      def `_end` as end(self) -> BtreeMultiset{KeyType}Iterator
      def `_insert` as insert(self, key: {key_type}) -> BtreeMultiset{KeyType}Iterator
      def `_erase` as erase(self, key: {key_type}) -> int
      def remove(self, it: BtreeMultiset{KeyType}Iterator) -> BtreeMultiset{KeyType}Iterator
      def `_find` as find(self, key: {key_type}) -> BtreeMultiset{KeyType}Iterator
      def `_lower_bound` as lower_bound(self, key: {key_type}) -> BtreeMultiset{KeyType}Iterator
      def `_upper_bound` as upper_bound(self, key: {key_type}) -> BtreeMultiset{KeyType}Iterator
      class `keys_view` as __iter__:  # It does not work on `object`.
        def __next__(self) -> {key_type}  # It does not work on `object`.
      def keys(self) -> _BtreeMultiset{KeyType}KeysView  # It does not work on `object`.
"""

_TEMPLATE_MAPS = """\
    class `btree_map<{key_c_type}, {value_c_type}>::iterator` as BtreeMap{KeyType}2{ValueType}Iterator:
      def `operator++` as self_inc(self) -> BtreeMap{KeyType}2{ValueType}Iterator
      def `operator--` as self_dec(self) -> BtreeMap{KeyType}2{ValueType}Iterator
      def `operator*` as deref(self) -> tuple<{key_type}, {value_type}>
      def `operator==` as __eq__(self, rhs: BtreeMap{KeyType}2{ValueType}Iterator) -> bool
      def `operator!=` as __ne__(self, rhs: BtreeMap{KeyType}2{ValueType}Iterator) -> bool

    class `btree_map<{key_c_type}, {value_c_type}>::keys_view_generator` as _BtreeMap{KeyType}2{ValueType}KeysView:  # It does not work on `object`.
      class `btree_view` as __iter__:  # It does not work on `object`.
        def __next__(self) -> {key_type}  # It does not work on `object`.

    class `btree_map<{key_c_type}, {value_c_type}>::values_view_generator` as _Btreemap{KeyType}2{ValueType}ValuesView:  # It does not work on `object`.
      class `btree_view` as __iter__:  # It does not work on `object`.
        def __next__(self) -> {value_type}  # It does not work on `object`.

    class `btree_map<{key_c_type}, {value_c_type}>::items_view_generator` as _Btreemap{KeyType}2{ValueType}ItemsView:  # It does not work on `object`.
      class `btree_view` as __iter__:  # It does not work on `object`.
        def __next__(self) -> tuple<{key_type}, {value_type}>  # It does not work on `object`.

    class `btree_map<{key_c_type}, {value_c_type}>` as BtreeMap{KeyType}2{ValueType}:
      def __init__(self) -> None
      def `_clear` as clear(self) -> None
      def empty(self) -> bool
      def `not_empty` as __bool__(self) -> bool
      def `_contains` as contains(self, key: {key_type}) -> bool
      def `_contains` as __contains__(self, key: {key_type}) -> bool
      def size(self) -> int
      def `size` as __len__(self) -> int
      def `_begin` as begin(self) -> BtreeMap{KeyType}2{ValueType}Iterator
      def `_end` as end(self) -> BtreeMap{KeyType}2{ValueType}Iterator
      def `_insert` as insert(self, value: tuple<{key_type}, {value_type}>) -> tuple<BtreeMap{KeyType}2{ValueType}Iterator, bool>
      def `_erase` as erase(self, key: {key_type}) -> int
      def `_erase` as __delitem__(self, key: {key_type}) -> None
      def remove(self, it: BtreeMap{KeyType}2{ValueType}Iterator) -> BtreeMap{KeyType}2{ValueType}Iterator
      def `_find` as find(self, key: {key_type}) -> BtreeMap{KeyType}2{ValueType}Iterator
      def `_lower_bound` as lower_bound(self, key: {key_type}) -> BtreeMap{KeyType}2{ValueType}Iterator
      def `_upper_bound` as upper_bound(self, key: {key_type}) -> BtreeMap{KeyType}2{ValueType}Iterator
      def insert_or_assign(self, key: {key_type}, value: {value_type}) -> tuple<BtreeMap{KeyType}2{ValueType}Iterator, bool>
      def `get_item` as __getitem__(self, key: {key_type}) -> {value_type}
      def `insert_or_assign` as __setitem__(self, key: {key_type}, value: {value_type}) -> None
      class `keys_view` as __iter__:  # It does not work on `object`.
        def __next__(self) -> {key_type}  # It does not work on `object`.
      def keys(self) -> _BtreeMap{KeyType}2{ValueType}KeysView  # It does not work on `object`.
      def values(self) -> _Btreemap{KeyType}2{ValueType}ValuesView  # It does not work on `object`.
      def items(self) -> _Btreemap{KeyType}2{ValueType}ItemsView  # It does not work on `object`.

    class `btree_multimap<{key_c_type}, {value_c_type}>::iterator` as BtreeMultimap{KeyType}2{ValueType}Iterator:
      def `operator++` as self_inc(self) -> BtreeMultimap{KeyType}2{ValueType}Iterator
      def `operator--` as self_dec(self) -> BtreeMultimap{KeyType}2{ValueType}Iterator
      def `operator*` as deref(self) -> tuple<{key_type}, {value_type}>
      def `operator==` as __eq__(self, rhs: BtreeMultimap{KeyType}2{ValueType}Iterator) -> bool
      def `operator!=` as __ne__(self, rhs: BtreeMultimap{KeyType}2{ValueType}Iterator) -> bool

    class `btree_multimap<{key_c_type}, {value_c_type}>::keys_view_generator` as _BtreeMultimap{KeyType}2{ValueType}KeysView:  # It does not work on `object`.
      class `btree_view` as __iter__:  # It does not work on `object`.
        def __next__(self) -> {key_type}  # It does not work on `object`.

    class `btree_multimap<{key_c_type}, {value_c_type}>::values_view_generator` as _BtreeMultimap{KeyType}2{ValueType}ValuesView:  # It does not work on `object`.
      class `btree_view` as __iter__:  # It does not work on `object`.
        def __next__(self) -> {value_type}  # It does not work on `object`.

    class `btree_multimap<{key_c_type}, {value_c_type}>::items_view_generator` as _BtreeMultimap{KeyType}2{ValueType}ItemsView:  # It does not work on `object`.
      class `btree_view` as __iter__:  # It does not work on `object`.
        def __next__(self) -> tuple<{key_type}, {value_type}>  # It does not work on `object`.

    class `btree_multimap<{key_c_type}, {value_c_type}>` as BtreeMultimap{KeyType}2{ValueType}:
      def __init__(self) -> None
      def `_clear` as clear(self) -> None
      def empty(self) -> bool
      def `not_empty` as __bool__(self) -> bool
      def `_contains` as contains(self, key: {key_type}) -> bool
      def `_contains` as __contains__(self, key: {key_type}) -> bool
      def size(self) -> int
      def `size` as __len__(self) -> int
      def `_begin` as begin(self) -> BtreeMultimap{KeyType}2{ValueType}Iterator
      def `_end` as end(self) -> BtreeMultimap{KeyType}2{ValueType}Iterator
      def `_insert` as insert(self, value: tuple<{key_type}, {value_type}>) -> BtreeMultimap{KeyType}2{ValueType}Iterator
      def `_erase` as erase(self, key: {key_type}) -> int
      def remove(self, it: BtreeMultimap{KeyType}2{ValueType}Iterator) -> BtreeMultimap{KeyType}2{ValueType}Iterator
      def `_find` as find(self, key: {key_type}) -> BtreeMultimap{KeyType}2{ValueType}Iterator
      def `_lower_bound` as lower_bound(self, key: {key_type}) -> BtreeMultimap{KeyType}2{ValueType}Iterator
      def `_upper_bound` as upper_bound(self, key: {key_type}) -> BtreeMultimap{KeyType}2{ValueType}Iterator
      class `keys_view` as __iter__:  # It does not work on `object`.
        def __next__(self) -> {key_type}  # It does not work on `object`.
      def keys(self) -> _BtreeMultimap{KeyType}2{ValueType}KeysView  # It does not work on `object`.
      def values(self) -> _BtreeMultimap{KeyType}2{ValueType}ValuesView  # It does not work on `object`.
      def items(self) -> _BtreeMultimap{KeyType}2{ValueType}ItemsView  # It does not work on `object`.
"""

_ELEMENTARY_TYPES = (int, float, str)
_ElementaryTypes: TypeAlias = Union[object, *_ELEMENTARY_TYPES]

_MAX_KEY_TUPLE_LEN = 3


def _convert_to_c_type(tp: type[_ElementaryTypes]) -> str:
  if tp is float:
    return 'double'
  if tp is str:
    return 'std::string'
  if tp is object:
    return 'PyObject*'
  return tp.__name__


def _get_c_type_repr(types: tuple[type[_ElementaryTypes], ...]) -> str:
  match len(types):
    case 1:
      return _convert_to_c_type(types[0])
    case 2:
      return f'std::pair<{", ".join(_convert_to_c_type(tp) for tp in types)}>'
    case _:
      return f'std::tuple<{", ".join(_convert_to_c_type(tp) for tp in types)}>'


def _get_type_repr(types: tuple[type[_ElementaryTypes], ...]) -> str:
  match len(types):
    case 1:
      return types[0].__name__
    case 2:
      return f'tuple<{", ".join(tp.__name__ for tp in types)}>'
    case _:
      return f'`std::tuple` as tuple<{", ".join(tp.__name__ for tp in types)} >'


def _get_capitalized_type_repr(
    types: tuple[type[_ElementaryTypes], ...]
) -> str:
  return ''.join(tp.__name__.capitalize() for tp in types)


# Cannot use the namespace qualified type `std::string` in the template argument
# `std::tuple<...>` due to a known PyCLIF bug.
def _is_clif_bug_type(types: tuple[type[_ElementaryTypes], ...]) -> bool:
  return len(types) > 2 and str in types


def _remove_unsupported_lines(text: str) -> str:
  lines = text.split('\n')
  lines = [
      line
      for line in lines
      if not line.endswith('# It does not work on `object`.')
  ]
  return '\n'.join(lines)


def main() -> None:
  print(_TEMPLATE_HEADER)

  for key_tuple_len in range(1, _MAX_KEY_TUPLE_LEN + 1):
    # The type `float` is not considered as keys since it will lose precision
    # after calculation.
    for key_types in (
        types
        for types in itertools.product(*((_ELEMENTARY_TYPES,) * key_tuple_len))
        if not _is_clif_bug_type(types) and float not in types
    ):
      print(
          _TEMPLATE_SETS.format(
              key_type=_get_type_repr(key_types),
              key_c_type=_get_c_type_repr(key_types),
              KeyType=_get_capitalized_type_repr(key_types),
          )
      )
      print(
          _remove_unsupported_lines(
              _TEMPLATE_MAPS.format(
                  key_type=_get_type_repr(key_types),
                  key_c_type=_get_c_type_repr(key_types),
                  KeyType=_get_capitalized_type_repr(key_types),
                  value_type=_get_type_repr((object,)),
                  value_c_type=_get_c_type_repr((object,)),
                  ValueType=_get_capitalized_type_repr((object,)),
              )
          )
      )

  for key_type, value_type in itertools.product(
      (tp for tp in _ELEMENTARY_TYPES if tp is not float),
      _ELEMENTARY_TYPES,
  ):
    print(
        _TEMPLATE_MAPS.format(
            key_type=_get_type_repr((key_type,)),
            key_c_type=_get_c_type_repr((key_type,)),
            KeyType=_get_capitalized_type_repr((key_type,)),
            value_type=_get_type_repr((value_type,)),
            value_c_type=_get_c_type_repr((value_type,)),
            ValueType=_get_capitalized_type_repr((value_type,)),
        )
    )

  print(
      _remove_unsupported_lines(
          _TEMPLATE_SETS.format(
              key_type=_get_type_repr((object,)),
              key_c_type=_get_c_type_repr((object,)),
              KeyType=_get_capitalized_type_repr((object,)),
          )
      )
  )
  print(
      _remove_unsupported_lines(
          _TEMPLATE_MAPS.format(
              key_type=_get_type_repr((object,)),
              key_c_type=_get_c_type_repr((object,)),
              KeyType=_get_capitalized_type_repr((object,)),
              value_type=_get_type_repr((object,)),
              value_c_type=_get_c_type_repr((object,)),
              ValueType=_get_capitalized_type_repr((object,)),
          )
      )
  )


if __name__ == '__main__':
  main()
