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

#ifndef PYBTREE_BTREE_H_
#define PYBTREE_BTREE_H_

#include <concepts>
#include <cstddef>
#include <functional>
#include <iterator>
#include <string>
#include <tuple>
#include <type_traits>
#include <utility>

// It is recommended to always define `PY_SSIZE_T_CLEAN` before including
// Python.h. See also: https://docs.python.org/3/c-api/intro.html#include-files
#define PY_SSIZE_T_CLEAN
#include "Python.h"
#include "third_party/absl/container/btree_map.h"
#include "third_party/absl/container/btree_set.h"
#include "btree_utils.h"

// TODO: Alert! It will export `string` to the global namespace, i.e.
// `::string`, which should not be done in headers. However, due to a known
// PyCLIF bug, any namespace qualified types such as `std::string` cannot be
// used in the template argument. It is unfixable on my side at the moment since
// the template is introduced in the CLIF generated code when defining
// `__iter__`. If we do not put `std::string` in the global namespace, some
// errors will occur.
using string = std::string;

// TODO: Same problem to the following template namespace qualified identifiers.
template <typename... Args>
using pair = std::pair<Args...>;

template <typename... Args>
using tuple = std::tuple<Args...>;

template <typename... Args>
using less = std::less<Args...>;

namespace djc::btree {

namespace btree_internal {

template <typename key_type, typename mapped_type, typename Iterator>
void dec_ref_for_iterator(Iterator it) {
  if constexpr (std::is_same_v<key_type, PyObject*>) {
    if constexpr (std::is_void_v<mapped_type>) {
      Py_DECREF(*it);
    } else {
      Py_DECREF(it->first);
    }
  }
  if constexpr (std::is_same_v<mapped_type, PyObject*>) {
    Py_DECREF(it->second);
  }
}

template <typename Derived, typename Iterator, typename Key,
          typename Data = void>
class btree_container_iterator {
 private:
  Derived* derived() { return static_cast<Derived*>(this); }

  Iterator* iterator() {
    // Static cast is not allowed here because this class is not the "actual"
    // base class of `Iterator`. Reinterpret cast is safe because the derived
    // classes of this abstract class do not introduce any member variables nor
    // virtual functions. The two classes should have the same memory layout.
    return reinterpret_cast<Iterator*>(this);
  }

 public:
  using key_type = Key;
  using mapped_type = Data;
  using value_type = std::conditional_t<std::is_void_v<mapped_type>, key_type,
                                        std::pair<const key_type, mapped_type>>;
  using value_ret_type = std::conditional_t<
      std::is_same_v<value_type, PyObject*> ||
          std::is_same_v<mapped_type, PyObject*>,
      value_type,
      std::conditional_t<std::is_void_v<mapped_type>, const key_type&,
                         const std::pair<const key_type, mapped_type>&>>;

  Derived operator++() {
    ++*iterator();
    return *derived();
  }

  Derived operator--() {
    --*iterator();
    return *derived();
  }

  Derived operator++(int) {
    Derived self = *derived();
    ++*iterator();
    return self;
  }

  Derived operator--(int) {
    Derived self = *derived();
    --*iterator();
    return self;
  }

  // TODO: It does not support `object` in Python because `object` is a special
  // case that `PyObject*&` will not be treated as `object` in PyCLIF, while all
  // other types are supported.
  value_ret_type operator*() {
    if constexpr (std::is_same_v<key_type, PyObject*>) {
      if constexpr (std::is_void_v<mapped_type>) {
        Py_INCREF(**iterator());
      } else {
        Py_INCREF((*iterator())->first);
      }
    }
    if constexpr (std::is_same_v<mapped_type, PyObject*>) {
      Py_INCREF((*iterator())->second);
    }
    return **iterator();
  }

  bool operator==(const btree_container_iterator&) const = default;

  bool operator!=(const btree_container_iterator&) const = default;
};

}  // namespace btree_internal

template <typename Key, typename Compare>
class btree_set_iterator
    : public absl::btree_set<Key, Compare>::iterator,
      public btree_internal::btree_container_iterator<
          btree_set_iterator<Key, Compare>,
          typename absl::btree_set<Key, Compare>::iterator, Key> {
 private:
  using base_type = btree_internal::btree_container_iterator<
      btree_set_iterator<Key, Compare>,
      typename absl::btree_set<Key, Compare>::iterator, Key>;

 public:
  using btree_type = absl::btree_set<Key, Compare>;
  using iterator = btree_type::iterator;

  explicit btree_set_iterator(iterator it) : iterator(it) {}

  using base_type::operator++;
  using base_type::operator--;
  using base_type::operator*;

  bool operator==(const btree_set_iterator& rhs) const = default;

  bool operator!=(const btree_set_iterator& rhs) const = default;
};

template <typename Key, typename Compare>
class btree_multiset_iterator
    : public absl::btree_multiset<Key, Compare>::iterator,
      public btree_internal::btree_container_iterator<
          btree_multiset_iterator<Key, Compare>,
          typename absl::btree_multiset<Key, Compare>::iterator, Key> {
 private:
  using base_type = btree_internal::btree_container_iterator<
      btree_multiset_iterator<Key, Compare>,
      typename absl::btree_multiset<Key, Compare>::iterator, Key>;

 public:
  using btree_type = absl::btree_multiset<Key, Compare>;
  using iterator = btree_type::iterator;

  explicit btree_multiset_iterator(iterator it) : iterator(it) {}

  using base_type::operator++;
  using base_type::operator--;
  using base_type::operator*;

  bool operator==(const btree_multiset_iterator& rhs) const = default;

  bool operator!=(const btree_multiset_iterator& rhs) const = default;
};

template <typename Key, typename Data, typename Compare>
class btree_map_iterator
    : public absl::btree_map<Key, Data, Compare>::iterator,
      public btree_internal::btree_container_iterator<
          btree_map_iterator<Key, Data, Compare>,
          typename absl::btree_map<Key, Data, Compare>::iterator, Key, Data> {
 private:
  using base_type = btree_internal::btree_container_iterator<
      btree_map_iterator<Key, Data, Compare>,
      typename absl::btree_map<Key, Data, Compare>::iterator, Key, Data>;

 public:
  using btree_type = absl::btree_map<Key, Data, Compare>;
  using iterator = btree_type::iterator;

  explicit btree_map_iterator(iterator it) : iterator(it) {}

  using base_type::operator++;
  using base_type::operator--;
  using base_type::operator*;

  bool operator==(const btree_map_iterator&) const = default;

  bool operator!=(const btree_map_iterator&) const = default;
};

template <typename Key, typename Data, typename Compare>
class btree_multimap_iterator
    : public absl::btree_multimap<Key, Data, Compare>::iterator,
      public btree_internal::btree_container_iterator<
          btree_multimap_iterator<Key, Data, Compare>,
          typename absl::btree_multimap<Key, Data, Compare>::iterator, Key,
          Data> {
 private:
  using base_type = btree_internal::btree_container_iterator<
      btree_multimap_iterator<Key, Data, Compare>,
      typename absl::btree_multimap<Key, Data, Compare>::iterator, Key, Data>;

 public:
  using btree_type = absl::btree_multimap<Key, Data, Compare>;
  using iterator = btree_type::iterator;

  explicit btree_multimap_iterator(iterator it) : iterator(it) {}

  using base_type::operator++;
  using base_type::operator--;
  using base_type::operator*;

  bool operator==(const btree_multimap_iterator&) const = default;

  bool operator!=(const btree_multimap_iterator&) const = default;
};

namespace btree_internal {

struct btree_view_tag {};
struct btree_keys_view_tag : public btree_view_tag {};
struct btree_values_view_tag : public btree_view_tag {};
struct btree_items_view_tag : public btree_view_tag {};

template <typename Tag, typename Key, typename Data>
  requires(std::derived_from<Tag, btree_view_tag>)
using iterator_value_type = std::conditional_t<
    std::is_same_v<Tag, btree_keys_view_tag>, Key,
    std::conditional_t<std::is_same_v<Tag, btree_values_view_tag>, Data,
                       std::pair<const Key, Data>>>;

template <typename... Args>
using first_type_or_void = DJC_BTREE_LAZY_CONDITIONAL_T(
    sizeof...(Args) == 0, void,
    DJC_BTREE_SINGLE_ARG(std::tuple_element_t<0, std::tuple<Args...>>));

template <typename Tag, template <typename...> typename Iterator,
          typename Compare, typename Key, typename... Data>
  requires(std::derived_from<Tag, btree_view_tag>)
class btree_view {
 private:
  using key_type = Key;
  using mapped_type = first_type_or_void<Data...>;

 public:
  using iterator = Iterator<Key, Data..., Compare>;

  using value_type = iterator_value_type<Tag, key_type, mapped_type>;
  using difference_type = ptrdiff_t;
  using pointer = value_type*;
  using reference = value_type&;
  using iterator_category = std::forward_iterator_tag;

 private:
  using ret_type =
      std::conditional_t<std::is_same_v<key_type, PyObject*> ||
                             std::is_same_v<mapped_type, PyObject*>,
                         value_type, const value_type&>;

 public:
  explicit btree_view(iterator it) : it_(it) {}

  btree_view(const btree_view& rhs) : it_(rhs.it_) {}
  btree_view& operator=(const btree_view& rhs) = default;

  btree_view(btree_view&& rhs) : it_(std::move(rhs.it_)) {}
  btree_view& operator=(btree_view&& rhs) = default;

  btree_view& operator++() {
    ++it_;
    return *this;
  }

  btree_view& operator--() {
    --it_;
    return *this;
  }

  btree_view operator++(int) {
    btree_view self = *this;
    ++it_;
    return self;
  }

  btree_view operator--(int) {
    btree_view self = *this;
    --it_;
    return self;
  }

  ret_type operator*() {
    if constexpr (std::is_same_v<Tag, btree_keys_view_tag>) {
      if constexpr (std::is_void_v<mapped_type>) {
        return *it_;
      } else {
        return it_->first;
      }
    }
    if constexpr (std::is_same_v<Tag, btree_values_view_tag>) {
      static_assert(!std::is_void_v<mapped_type>);
      return it_->second;
    }
    if constexpr (std::is_same_v<Tag, btree_items_view_tag>) {
      static_assert(!std::is_void_v<mapped_type>);
      return *it_;
    }
  }

  bool operator==(const btree_view& rhs) const { return it_ == rhs.it_; };

  bool operator!=(const btree_view& rhs) const { return it_ != rhs.it_; };

 private:
  iterator it_;
};

template <template <typename...> typename Btree,
          template <typename...> typename View, typename... Args>
class btree_view_generator {
 public:
  using btree_type = Btree<Args...>;
  using btree_view = View<Args...>;
  using iterator = btree_type::iterator;

  explicit btree_view_generator(btree_type& btree)
      : begin_(btree._begin()), end_(btree._end()) {}

  btree_view begin() { return begin_; }

  btree_view end() { return end_; }

 private:
  btree_view begin_;
  btree_view end_;
};

}  // namespace btree_internal

template <typename Key, typename Compare>
using btree_set_keys_view =
    btree_internal::btree_view<btree_internal::btree_keys_view_tag,
                               btree_set_iterator, Compare, Key>;

template <typename Key, typename Compare>
using btree_multiset_keys_view =
    btree_internal::btree_view<btree_internal::btree_keys_view_tag,
                               btree_multiset_iterator, Compare, Key>;

template <typename Key, typename Data, typename Compare>
using btree_map_keys_view =
    btree_internal::btree_view<btree_internal::btree_keys_view_tag,
                               btree_map_iterator, Compare, Key, Data>;

template <typename Key, typename Data, typename Compare>
using btree_multimap_keys_view =
    btree_internal::btree_view<btree_internal::btree_keys_view_tag,
                               btree_multimap_iterator, Compare, Key, Data>;

template <typename Key, typename Data, typename Compare>
using btree_map_values_view =
    btree_internal::btree_view<btree_internal::btree_values_view_tag,
                               btree_map_iterator, Compare, Key, Data>;

template <typename Key, typename Data, typename Compare>
using btree_multimap_values_view =
    btree_internal::btree_view<btree_internal::btree_values_view_tag,
                               btree_multimap_iterator, Compare, Key, Data>;

template <typename Key, typename Data, typename Compare>
using btree_map_items_view =
    btree_internal::btree_view<btree_internal::btree_items_view_tag,
                               btree_map_iterator, Compare, Key, Data>;

template <typename Key, typename Data, typename Compare>
using btree_multimap_items_view =
    btree_internal::btree_view<btree_internal::btree_items_view_tag,
                               btree_multimap_iterator, Compare, Key, Data>;

namespace btree_internal {

template <typename, class = void>
struct get_mapped_type_or_void {
  using type = void;
};

template <typename T>
struct get_mapped_type_or_void<T, std::void_t<typename T::mapped_type>> {
  using type = typename T::mapped_type;
};

template <typename T>
using get_mapped_type_or_void_t = get_mapped_type_or_void<T>::type;

template <typename Btree, typename KeyView>
class btree_container {
 public:
  using btree_type = Btree;
  using keys_view = KeyView;
  using iterator = keys_view::iterator;
  using size_type = btree_type::size_type;
  using key_type = btree_type::key_type;
  using mapped_type = get_mapped_type_or_void_t<btree_type>;
  using value_type = btree_type::value_type;

 private:
  using key_arg_type = std::conditional_t<std::is_pointer_v<key_type>, key_type,
                                          const key_type&>;
  using value_arg_type = std::conditional_t<std::is_pointer_v<value_type>,
                                            value_type, const value_type&>;

 protected:
  btree_type* btree() {
    // Static cast is not allowed here because this class is not the "actual"
    // base class of `btree_type`. Reinterpret cast is safe because the derived
    // classes of this abstract class do not introduce any member variables nor
    // virtual functions. The two classes should have the same memory layout.
    return reinterpret_cast<btree_type*>(this);
  }

 public:
  bool not_empty() { return !btree()->empty(); }

  iterator _begin() { return iterator(btree()->begin()); }

  iterator _end() { return iterator(btree()->end()); }

  keys_view begin() { return keys_view(_begin()); }

  keys_view end() { return keys_view(_end()); }

  // Avoid heterogeneous lookup since Python does not support overloads.
  bool _contains(key_arg_type key) { return btree()->contains(key); }

  iterator _find(key_arg_type key) { return iterator(btree()->find(key)); }

  iterator _lower_bound(key_arg_type key) {
    return iterator(btree()->lower_bound(key));
  }

  iterator _upper_bound(key_arg_type key) {
    return iterator(btree()->upper_bound(key));
  }

  std::pair<iterator, bool> _insert(value_arg_type value) {
    auto [it, inserted] = btree()->insert(value);
    if (inserted) {
      if constexpr (std::is_same_v<key_type, PyObject*>) {
        if constexpr (std::is_void_v<mapped_type>) {
          Py_INCREF(*it);
        } else {
          Py_INCREF(it->first);
        }
      }
      if constexpr (std::is_same_v<mapped_type, PyObject*>) {
        Py_INCREF(it->second);
      }
    }
    return std::make_pair(iterator(it), inserted);
  }

  size_type _erase(key_arg_type key) {
    if constexpr (!std::is_same_v<key_type, PyObject*> &&
                  !std::is_same_v<mapped_type, PyObject*>) {
      return btree()->erase(key);
    } else if (auto it = btree()->find(key); it == btree()->end()) {
      return 0;
    } else {
      {
        gil_guard<> _;
        btree_internal::dec_ref_for_iterator<key_type, mapped_type>(it);
      }
      btree()->erase(it);
      return 1;
    }
  }

  iterator remove(iterator it) {
    if constexpr (std::is_same_v<key_type, PyObject*> ||
                  std::is_same_v<mapped_type, PyObject*>) {
      gil_guard<> _;
      btree_internal::dec_ref_for_iterator<key_type, mapped_type>(it);
    }
    return iterator(btree()->erase(static_cast<btree_type::iterator>(it)));
  }

  void _clear() {
    release();
    btree()->clear();
  }

  ~btree_container() { release(); }

 private:
  void release() {
    if constexpr (std::is_same_v<key_type, PyObject*> ||
                  std::is_same_v<mapped_type, PyObject*>) {
      gil_guard<> _;
      if constexpr (std::is_void_v<mapped_type>) {
        for (auto&& key : *btree()) {
          Py_DECREF(key);
        }
      } else {
        for (auto&& [key, value] : *btree()) {
          if constexpr (std::is_same_v<key_type, PyObject*>) {
            Py_DECREF(key);
          }
          if constexpr (std::is_same_v<mapped_type, PyObject*>) {
            Py_DECREF(value);
          }
        }
      }
    }
  }
};

template <typename Btree, typename KeyView>
class btree_multi_container : public btree_container<Btree, KeyView> {
 public:
  using btree_type = Btree;
  using keys_view = KeyView;
  using iterator = keys_view::iterator;
  using size_type = btree_type::size_type;
  using key_type = btree_type::key_type;
  using mapped_type = get_mapped_type_or_void_t<btree_type>;
  using value_type = btree_type::value_type;

 private:
  using key_arg_type = std::conditional_t<std::is_pointer_v<key_type>, key_type,
                                          const key_type&>;
  using value_arg_type = std::conditional_t<std::is_pointer_v<value_type>,
                                            value_type, const value_type&>;

 protected:
  using btree_container<btree_type, keys_view>::btree;

 public:
  iterator _insert(value_arg_type value) {
    if constexpr (std::is_same_v<key_type, PyObject*>) {
      if constexpr (std::is_void_v<mapped_type>) {
        Py_INCREF(value);
      } else {
        Py_INCREF(value.first);
      }
    }
    if constexpr (std::is_same_v<mapped_type, PyObject*>) {
      Py_INCREF(value.second);
    }
    return iterator(btree()->insert(value));
  }

  size_type _erase(key_arg_type key) {
    if constexpr (!std::is_same_v<key_type, PyObject*> &&
                  !std::is_same_v<mapped_type, PyObject*>) {
      return btree()->erase(key);
    } else {
      size_type removed_count = 0;
      auto [first, last] = btree()->equal_range(key);
      {
        gil_guard<> _;
        for (auto it = first; it != last; ++it) {
          ++removed_count;
          btree_internal::dec_ref_for_iterator<key_type, mapped_type>(it);
        }
      }
      btree()->erase(first, last);
      return removed_count;
    }
  }
};

template <int OpCode>
class pyobject_cmp {
 public:
  bool operator()(PyObject* lhs, PyObject* rhs) const {
    return PyObject_RichCompareBool(lhs, rhs, OpCode);
  }
};

template <typename Key>
using default_comparator =
    std::conditional_t<std::is_same_v<std::remove_cv_t<Key>, PyObject*>,
                       btree_internal::pyobject_cmp<Py_LT>, std::less<Key>>;

}  // namespace btree_internal

template <typename Key,
          typename Compare = btree_internal::default_comparator<Key>>
class btree_set
    : public absl::btree_set<Key, Compare>,
      public btree_internal::btree_container<
          absl::btree_set<Key, Compare>, btree_set_keys_view<Key, Compare>> {
 public:
  using btree_type = absl::btree_set<Key, Compare>;
  using key_type = btree_type::key_type;
  using value_type = btree_type::value_type;
  using size_type = btree_type::size_type;
  using keys_view = btree_set_keys_view<key_type, Compare>;
  using iterator = keys_view::iterator;

 private:
  using btree_container =
      btree_internal::btree_container<absl::btree_set<Key, Compare>,
                                      btree_set_keys_view<Key, Compare>>;

 public:
  using btree_container::begin;
  using btree_container::end;

  using keys_view_generator =
      btree_internal::btree_view_generator<btree_set, btree_set_keys_view, Key,
                                           Compare>;

  keys_view_generator keys() { return keys_view_generator(*this); }
};

template <typename Key,
          typename Compare = btree_internal::default_comparator<Key>>
class btree_multiset : public absl::btree_multiset<Key, Compare>,
                       public btree_internal::btree_multi_container<
                           absl::btree_multiset<Key, Compare>,
                           btree_multiset_keys_view<Key, Compare>> {
 public:
  using btree_type = absl::btree_multiset<Key, Compare>;
  using key_type = btree_type::key_type;
  using value_type = btree_type::value_type;
  using size_type = btree_type::size_type;
  using keys_view = btree_multiset_keys_view<key_type, Compare>;
  using iterator = keys_view::iterator;

 private:
  using btree_container = btree_internal::btree_multi_container<
      absl::btree_multiset<Key, Compare>,
      btree_multiset_keys_view<Key, Compare>>;

 public:
  using btree_container::begin;
  using btree_container::end;

  using keys_view_generator = btree_internal::btree_view_generator<
      btree_multiset, btree_multiset_keys_view, Key, Compare>;

  keys_view_generator keys() { return keys_view_generator(*this); }
};

template <typename Key, typename Data,
          typename Compare = btree_internal::default_comparator<Key>>
class btree_map : public absl::btree_map<Key, Data, Compare>,
                  public btree_internal::btree_container<
                      absl::btree_map<Key, Data, Compare>,
                      btree_map_keys_view<Key, Data, Compare>> {
 public:
  using btree_type = absl::btree_map<Key, Data, Compare>;
  using key_type = btree_type::key_type;
  using mapped_type = btree_type::mapped_type;
  using value_type = btree_type::value_type;
  using size_type = btree_type::size_type;
  using keys_view = btree_map_keys_view<key_type, mapped_type, Compare>;
  using iterator = keys_view::iterator;

 private:
  using btree_container =
      btree_internal::btree_container<absl::btree_map<Key, Data, Compare>,
                                      btree_map_keys_view<Key, Data, Compare>>;
  using key_arg_type = std::conditional_t<std::is_pointer_v<key_type>, key_type,
                                          const key_type&>;
  using mapped_arg_type = std::conditional_t<std::is_pointer_v<mapped_type>,
                                             mapped_type, const mapped_type&>;

 public:
  using btree_container::begin;
  using btree_container::end;

  using keys_view_generator =
      btree_internal::btree_view_generator<btree_map, btree_map_keys_view, Key,
                                           Data, Compare>;
  using values_view_generator =
      btree_internal::btree_view_generator<btree_map, btree_map_values_view,
                                           Key, Data, Compare>;
  using items_view_generator =
      btree_internal::btree_view_generator<btree_map, btree_map_items_view, Key,
                                           Data, Compare>;

  keys_view_generator keys() { return keys_view_generator(*this); }
  values_view_generator values() { return values_view_generator(*this); }
  items_view_generator items() { return items_view_generator(*this); }

  std::pair<iterator, bool> insert_or_assign(key_arg_type key,
                                             mapped_arg_type data) {
    if constexpr (std::is_same_v<mapped_type, PyObject*>) {
      Py_INCREF(data);
    }
    auto [it, inserted] = btree_type::try_emplace(key, data);
    if (inserted) {
      if constexpr (std::is_same_v<key_type, PyObject*>) {
        Py_INCREF(key);
      }
    } else {
      if constexpr (std::is_same_v<mapped_type, PyObject*>) {
        Py_DECREF(it->second);
      }
      it->second = data;
    }
    return std::make_pair(iterator(it), inserted);
  }

  mapped_type get_item(key_arg_type key) {
    auto [it, inserted] = btree_type::try_emplace(key);
    gil_guard<!std::is_same_v<key_type, PyObject*> &&
              std::is_same_v<mapped_type, PyObject*>>
        _;
    if (inserted) {
      if constexpr (std::is_same_v<key_type, PyObject*>) {
        Py_INCREF(key);
      }
      if constexpr (std::is_same_v<mapped_type, PyObject*>) {
        it->second = Py_None;
        Py_INCREF(it->second);
      }
    }
    if constexpr (std::is_same_v<mapped_type, PyObject*>) {
      Py_INCREF(it->second);
    }
    return it->second;
  }
};

template <typename Key, typename Data,
          typename Compare = btree_internal::default_comparator<Key>>
class btree_multimap : public absl::btree_multimap<Key, Data, Compare>,
                       public btree_internal::btree_multi_container<
                           absl::btree_multimap<Key, Data, Compare>,
                           btree_multimap_keys_view<Key, Data, Compare>> {
 public:
  using btree_type = absl::btree_multimap<Key, Data, Compare>;
  using key_type = btree_type::key_type;
  using mapped_type = btree_type::mapped_type;
  using value_type = btree_type::value_type;
  using size_type = btree_type::size_type;
  using keys_view = btree_multimap_keys_view<key_type, mapped_type, Compare>;
  using iterator = keys_view::iterator;

 private:
  using btree_container = btree_internal::btree_multi_container<
      absl::btree_multimap<Key, Data, Compare>,
      btree_multimap_keys_view<Key, Data, Compare>>;

 public:
  using btree_container::begin;
  using btree_container::end;

  using keys_view_generator = btree_internal::btree_view_generator<
      btree_multimap, btree_multimap_keys_view, Key, Data, Compare>;
  using values_view_generator = btree_internal::btree_view_generator<
      btree_multimap, btree_multimap_values_view, Key, Data, Compare>;
  using items_view_generator = btree_internal::btree_view_generator<
      btree_multimap, btree_multimap_items_view, Key, Data, Compare>;

  keys_view_generator keys() { return keys_view_generator(*this); }
  values_view_generator values() { return values_view_generator(*this); }
  items_view_generator items() { return items_view_generator(*this); }
};

}  // namespace djc::btree

#endif  // PYBTREE_BTREE_H_
