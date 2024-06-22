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

"""Tests for btree.clif."""

from collections.abc import Callable
import itertools
import sys
from typing import Any

from absl.testing import absltest
from absl.testing import parameterized

from . import btree


class BtreeTest(parameterized.TestCase):

  @parameterized.named_parameters(
      dict(testcase_name='int', btree_type=btree.BtreeSetInt, f=int),
      dict(testcase_name='str', btree_type=btree.BtreeSetStr, f=str),
      dict(
          testcase_name='int_int',
          btree_type=btree.BtreeSetIntInt,
          f=lambda x: (x, x),
      ),
      dict(
          testcase_name='int_str',
          btree_type=btree.BtreeSetIntStr,
          f=lambda x: (x, str(x)),
      ),
      dict(
          testcase_name='str_int',
          btree_type=btree.BtreeSetStrInt,
          f=lambda x: (str(x), x),
      ),
      dict(
          testcase_name='str_str',
          btree_type=btree.BtreeSetStrStr,
          f=lambda x: (str(x), str(x)),
      ),
      dict(
          testcase_name='int_int_int',
          btree_type=btree.BtreeSetIntIntInt,
          f=lambda x: (x, x, x),
      ),
      dict(
          testcase_name='str_int_str',
          btree_type=btree.BtreeSetObject,
          f=lambda x: (str(x), x, str(x)),
      ),
  )
  def test_btree_set(self, btree_type: type[Any], f: Callable[[int], Any]):
    tree = btree_type()
    self.assertTrue(tree.empty())
    self.assertFalse(tree)

    tree.insert(f(123))
    self.assertLen(tree, 1)
    tree.insert(f(456))
    self.assertLen(tree, 2)
    tree.insert(f(123))
    self.assertLen(tree, 2)

    # The elements are {f(123), f(456)} currently.
    self.assertNotIn(f(100), tree)
    it, inserted = tree.insert(f(100))
    self.assertEqual(it.deref(), f(100))
    self.assertTrue(inserted)

    # The elements are {f(100), f(123), f(456)} currently.
    after_inc = it.self_inc()
    self.assertEqual(it, after_inc)
    self.assertEqual(it.deref(), f(123))
    self.assertEqual(it.deref(), f(123))
    self.assertEqual(it.deref(), f(123))
    self.assertEqual(it.deref(), f(123))
    self.assertEqual(it.deref(), f(123))
    self.assertEqual(it.deref(), f(123))
    self.assertEqual(it.deref(), f(123))
    self.assertEqual(it.deref(), f(123))
    self.assertEqual(it.deref(), f(123))
    self.assertEqual(it.deref(), f(123))
    self.assertEqual(it.deref(), f(123))
    self.assertEqual(it.deref(), f(123))
    after_dec = it.self_dec()
    self.assertEqual(it, after_dec)
    self.assertEqual(it.deref(), f(100))

    # The elements are {f(100), f(123), f(456)} currently.
    self.assertIn(f(456), tree)
    it, inserted = tree.insert(f(456))
    self.assertEqual(it.deref(), f(456))
    self.assertFalse(inserted)

    # The elements are {f(100), f(123), f(456)} currently.
    self.assertLen(tree, 3)
    self.assertEqual(tree.remove(tree.find(f(456))), tree.end())
    self.assertLen(tree, 2)
    self.assertEqual(tree.erase(f(678)), 0)
    self.assertLen(tree, 2)

    # The elements are {f(100), f(123)} currently.
    self.assertNotEqual(tree.find(f(100)), tree.end())
    self.assertEqual(tree.find(f(100)), tree.begin())
    self.assertEqual(tree.find(f(234)), tree.end())

    tree.insert(f(456))
    tree.insert(f(567))
    tree.insert(f(678))

    # The elements are {f(100), f(123), f(456), f(567), f(678)} currently.
    self.assertEqual(tree.lower_bound(f(456)).deref(), f(456))
    self.assertEqual(tree.upper_bound(f(456)).deref(), f(567))
    self.assertEqual(tree.lower_bound(f(500)), tree.find(f(567)))
    self.assertEqual(tree.upper_bound(f(500)), tree.find(f(567)))
    self.assertEqual(tree.lower_bound(f(900)), tree.end())
    self.assertEqual(tree.upper_bound(f(900)), tree.end())

    if not isinstance(tree, btree.BtreeSetObject):
      # `__iter__` should be supported for all types except `object`.
      expected_keys = [f(100), f(123), f(456), f(567), f(678)]
      self.assertListEqual(list(tree), expected_keys)
      self.assertListEqual(list(tree.keys()), expected_keys)

    tree.clear()
    self.assertEmpty(tree)
    self.assertEqual(tree.begin(), tree.end())

  @parameterized.named_parameters(
      dict(testcase_name='int', btree_type=btree.BtreeMultisetInt, f=int),
      dict(testcase_name='str', btree_type=btree.BtreeMultisetStr, f=str),
      dict(
          testcase_name='int_int',
          btree_type=btree.BtreeMultisetIntInt,
          f=lambda x: (x, x),
      ),
      dict(
          testcase_name='int_str',
          btree_type=btree.BtreeMultisetIntStr,
          f=lambda x: (x, str(x)),
      ),
      dict(
          testcase_name='str_int',
          btree_type=btree.BtreeMultisetStrInt,
          f=lambda x: (str(x), x),
      ),
      dict(
          testcase_name='str_str',
          btree_type=btree.BtreeMultisetStrStr,
          f=lambda x: (str(x), str(x)),
      ),
      dict(
          testcase_name='int_int_int',
          btree_type=btree.BtreeMultisetIntIntInt,
          f=lambda x: (x, x, x),
      ),
      dict(
          testcase_name='str_int_str',
          btree_type=btree.BtreeMultisetObject,
          f=lambda x: (str(x), x, str(x)),
      ),
  )
  def test_btree_multiset(self, btree_type: type[Any], f: Callable[[int], Any]):
    tree = btree_type()
    tree.insert(f(123))
    it = tree.insert(f(123))
    self.assertLen(tree, 2)
    self.assertEqual(tree.lower_bound(f(100)), tree.upper_bound(f(100)))
    self.assertNotEqual(tree.lower_bound(f(123)), tree.upper_bound(f(123)))

    # The elements are {f(123), f(123)} currently.
    if not isinstance(tree, btree.BtreeMultisetObject):
      # `__iter__` should be supported for all types except `object`.
      expected_keys = [f(123), f(123)]
      self.assertListEqual(list(tree), expected_keys)
      self.assertListEqual(list(tree.keys()), expected_keys)

    tree.remove(it)
    self.assertLen(tree, 1)
    self.assertEqual(tree.begin().deref(), f(123))
    tree.insert(f(123))
    self.assertEqual(tree.erase(f(123)), 2)
    self.assertEmpty(tree)

  @parameterized.named_parameters(
      dict(
          testcase_name='int_to_int',
          btree_type=btree.BtreeMapInt2Int,
          f=int,
          g=int,
      ),
      dict(
          testcase_name='int_to_str',
          btree_type=btree.BtreeMapInt2Str,
          f=int,
          g=str,
      ),
      dict(
          testcase_name='str_int_to_float',
          btree_type=btree.BtreeMapStrInt2Object,
          f=lambda x: (str(x), x),
          g=lambda x=None: float(x) if x is not None else None,
      ),
      dict(
          testcase_name='int_str_to_str_float',
          btree_type=btree.BtreeMapIntStr2Object,
          f=lambda x: (x, str(x)),
          g=lambda x=None: (str(x), [float(x)]) if x is not None else None,
      ),
      dict(
          testcase_name='str_to_int_float_int',
          btree_type=btree.BtreeMapStr2Object,
          f=str,
          g=lambda x=None: [x, float(x), x] if x is not None else None,
      ),
      dict(
          testcase_name='str_int_str_to_int_float_int',
          btree_type=btree.BtreeMapObject2Object,
          f=lambda x: (str(x), x + 1000, str(x)),
          g=lambda x=None: [x, float(x), x] if x is not None else None,
      ),
  )
  def test_btree_map(
      self,
      btree_type: type[Any],
      f: Callable[[int], Any],
      g: Callable[..., Any],
  ):
    tree = btree_type()
    self.assertTrue(tree.empty())
    self.assertFalse(tree)

    tree.insert((f(123), g(321)))
    self.assertLen(tree, 1)
    tree[f(456)] = g(654)
    self.assertLen(tree, 2)
    self.assertEqual(tree[f(1)], g())
    self.assertLen(tree, 3)

    # The elements are {f(1): g(), f(123): g(321), f(456): g(654)} currently.
    self.assertNotIn(f(100), tree)
    it, inserted = tree.insert((f(100), g(1)))
    self.assertTupleEqual(it.deref(), (f(100), g(1)))
    self.assertTrue(inserted)
    tree.insert_or_assign(f(101), g(2))
    self.assertEqual(tree[f(101)], g(2))
    tree.insert_or_assign(f(101), g(3))
    it = tree.find(f(101))
    self.assertTupleEqual(it.deref(), (f(101), g(3)))

    # The elements are{f(1): g(), f(100): g(1), f(101): g(3), f(123): g(321),
    # f(456): g(654)} currently.
    after_inc = it.self_inc()
    self.assertEqual(it, after_inc)
    self.assertTupleEqual(it.deref(), (f(123), g(321)))
    after_dec = it.self_dec()
    self.assertEqual(it, after_dec)
    self.assertTupleEqual(it.deref(), (f(101), g(3)))

    # The elements are {f(1): g(), f(100): g(1), f(101): g(3), f(123): g(321),
    # f(456): g(654)} currently.
    self.assertIn(f(456), tree)
    it, inserted = tree.insert((f(456), g(111)))
    self.assertEqual(it.deref(), (f(456), g(654)))
    self.assertFalse(inserted)

    if isinstance(tree, (btree.BtreeMapInt2Int, btree.BtreeMapInt2Str)):
      # `__iter__` should be supported for all types except `object`.
      expected_keys = [f(1), f(100), f(101), f(123), f(456)]
      self.assertListEqual(list(tree), expected_keys)
      self.assertListEqual(list(tree.keys()), expected_keys)
      expected_values = [g(), g(1), g(3), g(321), g(654)]
      self.assertListEqual(list(tree.values()), expected_values)
      expected_items = [
          (key, value) for key, value in zip(expected_keys, expected_values)
      ]
      self.assertListEqual(list(tree.items()), expected_items)

    # The elements are {f(1): g(), f(100): g(1), f(101): g(3), f(123): g(321),
    # f(456): g(654)} currently.
    self.assertLen(tree, 5)
    self.assertEqual(tree.remove(tree.find(f(101))).deref(), (f(123), g(321)))
    self.assertLen(tree, 4)
    self.assertEqual(tree.erase(f(321)), 0)
    self.assertLen(tree, 4)

    # The elements are {f(1): g(), f(100): g(1), f(123): g(321), f(456): g(654)}
    # currently.
    self.assertNotEqual(tree.find(f(100)), tree.end())
    self.assertEqual(tree.find(f(1)), tree.begin())
    self.assertEqual(tree.find(f(101)), tree.end())

    # The elements are {f(1): g(), f(100): g(1), f(123): g(321), f(456): g(654)}
    # currently.
    self.assertEqual(tree.lower_bound(f(100)).deref(), (f(100), g(1)))
    self.assertEqual(tree.upper_bound(f(100)).deref(), (f(123), g(321)))
    self.assertEqual(tree.lower_bound(f(120)), tree.find(f(123)))
    self.assertEqual(tree.upper_bound(f(120)), tree.find(f(123)))
    self.assertEqual(tree.lower_bound(f(500)), tree.end())
    self.assertEqual(tree.upper_bound(f(500)), tree.end())

    tree.clear()
    self.assertEmpty(tree)
    self.assertEqual(tree.begin(), tree.end())

  @parameterized.named_parameters(
      dict(
          testcase_name='int_to_int',
          btree_type=btree.BtreeMultimapInt2Int,
          f=int,
          g=int,
      ),
      dict(
          testcase_name='str_to_str',
          btree_type=btree.BtreeMultimapStr2Str,
          f=str,
          g=str,
      ),
      dict(
          testcase_name='int_str_to_float',
          btree_type=btree.BtreeMultimapIntStr2Object,
          f=lambda x: (x, str(x)),
          g=lambda x: [([[float(x)]],)],
      ),
      dict(
          testcase_name='str_int_to_float_str',
          btree_type=btree.BtreeMultimapStrInt2Object,
          f=lambda x: (str(x), x),
          g=lambda x: (float(x), str(x)),
      ),
      dict(
          testcase_name='str_to_float_float_int',
          btree_type=btree.BtreeMultimapStr2Object,
          f=str,
          g=lambda x: [float(x), float(x), x],
      ),
      dict(
          testcase_name='str_int_bool_to_int_float_int',
          btree_type=btree.BtreeMultimapObject2Object,
          f=lambda x: (str(x), x, bool(x)),
          g=lambda x: [x, float(x), x] if x is not None else None,
      ),
  )
  def test_btree_multimap(
      self,
      btree_type: type[Any],
      f: Callable[[int], Any],
      g: Callable[[int], Any],
  ):
    tree = btree_type()
    tree.insert((f(123), g(321)))
    it = tree.insert((f(123), g(456)))
    self.assertLen(tree, 2)
    self.assertEqual(tree.lower_bound(f(100)), tree.upper_bound(f(100)))
    self.assertNotEqual(tree.lower_bound(f(123)), tree.upper_bound(f(123)))

    # The elements are {f(123): g(321), f(123): g(456)} currently.
    if isinstance(
        tree, (btree.BtreeMultimapInt2Int, btree.BtreeMultimapStr2Str)
    ):
      # `__iter__` should be supported for all types except `object`.
      expected_keys = [f(123), f(123)]
      self.assertListEqual(list(tree), expected_keys)
      self.assertListEqual(list(tree.keys()), expected_keys)
      expected_values = [g(321), g(456)]
      self.assertListEqual(list(tree.values()), expected_values)
      expected_items = [
          (key, value) for key, value in zip(expected_keys, expected_values)
      ]
      self.assertListEqual(list(tree.items()), expected_items)

    tree.remove(it)
    self.assertLen(tree, 1)
    self.assertEqual(tree.begin().deref(), (f(123), g(321)))
    tree.insert((f(123), g(789)))
    self.assertEqual(tree.erase(f(123)), 2)
    self.assertEmpty(tree)

  def test_no_memory_leak(self):
    # Small integers with the same value correspond to the same object. CPython
    # caches small integers just like Java. Don't use small integers to monitor
    # reference count.
    keys = [100000 + i for i in range(10)]
    values = [200000 + i for i in range(10)]
    original_ref_counts = [
        sys.getrefcount(x) for x in itertools.chain(keys, values)
    ]

    tree = btree.BtreeMapObject2Object()
    for _ in range(100):
      for key, value in zip(keys, values):
        tree.insert((key, key))
        tree[key] = value
        tree.insert((key, key))
        del tree[key]
        tree.insert((key, value))
        tree[key] = value
        tree.insert((key, key))

    # `if`/`for`/`while` blocks in Python do not have scopes. As a result, we
    # need to manually decrease the reference count for the last loop variables.
    key = value = None  # pylint: disable=unused-variable
    self.assertListEqual(
        [sys.getrefcount(x) for x in itertools.chain(keys, values)],
        [x + 1 for x in original_ref_counts],
    )
    tree.clear()
    self.assertListEqual(
        [sys.getrefcount(x) for x in itertools.chain(keys, values)],
        original_ref_counts,
    )

    for key, value in zip(keys, values):
      tree[key] = value
    key = value = None  # pylint: disable=unused-variable
    self.assertListEqual(
        [sys.getrefcount(x) for x in itertools.chain(keys, values)],
        [x + 1 for x in original_ref_counts],
    )
    tree = None  # pylint: disable=unused-variable
    self.assertListEqual(
        [sys.getrefcount(x) for x in itertools.chain(keys, values)],
        original_ref_counts,
    )


if __name__ == '__main__':
  absltest.main()
