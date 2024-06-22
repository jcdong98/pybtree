// Copyright 2024 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef PYBTREE_BTREE_UTILS_H_
#define PYBTREE_BTREE_UTILS_H_

#include <type_traits>

// It is recommended to always define `PY_SSIZE_T_CLEAN` before including
// Python.h. See also: https://docs.python.org/3/c-api/intro.html#include-files
#define PY_SSIZE_T_CLEAN
#include "Python.h"

namespace djc::btree {

// If `Py_INCREF` or `Py_DECREF` is called when GIL is not held, there will be a
// fatal Python error "PyThreadState_Get: the function must be called with the
// GIL held, but the GIL is released (the current Python thread state is NULL)."
// That's because PyCLIF only ensure the GIL is held when PyObject* are in the
// interface. Thus, we have to manually hold the GIL in the contrary case.
template <bool Enable = true>
class gil_guard {};

template <>
class gil_guard<true> {
 public:
  gil_guard();
  ~gil_guard();

 private:
  PyGILState_STATE gil_state_;
};

namespace btree_internal {

template <typename T>
typename std::add_rvalue_reference_t<T> declval();

}  // namespace btree_internal

}  // namespace djc::btree

#define DJC_BTREE_SINGLE_ARG(...) __VA_ARGS__

#define DJC_BTREE_LAZY_CONDITIONAL_T(condition, true_type, false_type) \
  std::remove_reference_t<decltype([]() consteval {                    \
    if constexpr (condition) {                                         \
      return ::djc::btree::btree_internal::declval<true_type>();       \
    } else {                                                           \
      return ::djc::btree::btree_internal::declval<false_type>();      \
    }                                                                  \
  }())>

#endif  // PYBTREE_BTREE_UTILS_H_
