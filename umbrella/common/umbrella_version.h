// Copyright 2026 The Umbrella Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef CHROME_BROWSER_UMBRELLA_COMMON_UMBRELLA_VERSION_H_
#define CHROME_BROWSER_UMBRELLA_COMMON_UMBRELLA_VERSION_H_

#include <string>
#include <string_view>

namespace umbrella {

// Devono restare allineate a VERSION e versions.json: il test
// tests/test_versions.py fallisce se divergono.
inline constexpr std::string_view kVersion = "0.1.0";
inline constexpr std::string_view kChromiumMilestone = "158";
inline constexpr std::string_view kChromiumVersion = "158.0.8127.37";
inline constexpr std::string_view kChromiumCommit =
    "b8c2be851f62f6a394ec57955d7f31335d7cb6d4";

// Stringa mostrata nelle pagine informative, es. "Umbrella 0.1.0
// (Chromium 158.0.8127.37)".
std::string GetProductVersionString();

// Stringa compatta per metadati e diagnostica.
std::string GetBuildInfoString();

}  // namespace umbrella

#endif  // CHROME_BROWSER_UMBRELLA_COMMON_UMBRELLA_VERSION_H_
