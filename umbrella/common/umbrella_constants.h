// Copyright 2026 The Umbrella Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef CHROME_BROWSER_UMBRELLA_COMMON_UMBRELLA_CONSTANTS_H_
#define CHROME_BROWSER_UMBRELLA_COMMON_UMBRELLA_CONSTANTS_H_

#include <string_view>

namespace umbrella {

// Host della nuova scheda, sullo schema chrome:// già registrato da Chromium.
// Non viene introdotto un nuovo schema URL.
inline constexpr char kUmbrellaHost[] = "umbrella";
inline constexpr char kUmbrellaNewTabURL[] = "chrome://umbrella/";

// Motore di ricerca predefinito del prodotto.
inline constexpr char kDuckDuckGoURL[] = "https://duckduckgo.com/";
inline constexpr char kDuckDuckGoSearchURL[] =
    "https://duckduckgo.com/?q={searchTerms}";
inline constexpr char kDuckDuckGoName[] = "DuckDuckGo";
inline constexpr char kDuckDuckGoKeyword[] = "duckduckgo.com";

// Frammento usato per riconoscere i motori che Umbrella può sostituire al
// primo avvio senza mai scavalcare una scelta esplicita dell'utente.
inline constexpr char kReplaceableSearchHostFragment[] = "google.";

inline constexpr std::string_view kUmbrellaMarkURL = "umbrella-mark.svg";

}  // namespace umbrella

#endif  // CHROME_BROWSER_UMBRELLA_COMMON_UMBRELLA_CONSTANTS_H_
