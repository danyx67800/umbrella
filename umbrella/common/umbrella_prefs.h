// Copyright 2026 The Umbrella Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef CHROME_BROWSER_UMBRELLA_COMMON_UMBRELLA_PREFS_H_
#define CHROME_BROWSER_UMBRELLA_COMMON_UMBRELLA_PREFS_H_

#include "build/build_config.h"

namespace user_prefs {
class PrefRegistrySyncable;
}  // namespace user_prefs

namespace umbrella::prefs {

// Attiva la nuova scheda Umbrella. Default: true.
inline constexpr char kNewTabPageEnabled[] = "umbrella.new_tab_page_enabled";

// Applicazione del motore DuckDuckGo già eseguita. Evita di ripetere la
// migrazione a ogni avvio.
inline constexpr char kDefaultSearchApplied[] =
    "umbrella.default_search_applied";

// Default delle schede verticali applicato una sola volta, per non
// sovrascrivere una scelta successiva dell'utente.
inline constexpr char kVerticalTabsDefaultApplied[] =
    "umbrella.vertical_tabs_default_applied";

// Versione dello schema delle preferenze proprietarie, per migrazioni future.
inline constexpr char kSchemaVersion[] = "umbrella.schema_version";

// Versione corrente dello schema. Incrementare solo insieme a una migrazione
// esplicita che preservi i dati utente.
inline constexpr int kCurrentSchemaVersion = 1;

// Registra le preferenze nel profilo. Chiamata da
// chrome::RegisterProfilePrefs() nel checkout upstream.
void RegisterProfilePrefs(user_prefs::PrefRegistrySyncable* registry);

}  // namespace umbrella::prefs

#endif  // CHROME_BROWSER_UMBRELLA_COMMON_UMBRELLA_PREFS_H_
