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

#include "btree_utils.h"

// It is recommended to always define `PY_SSIZE_T_CLEAN` before including
// Python.h. See also: https://docs.python.org/3/c-api/intro.html#include-files
#define PY_SSIZE_T_CLEAN
#include "Python.h"

namespace djc::btree {

gil_guard<true>::gil_guard() : gil_state_(PyGILState_Ensure()) {}

gil_guard<true>::~gil_guard() { PyGILState_Release(gil_state_); }

}  // namespace djc::btree
