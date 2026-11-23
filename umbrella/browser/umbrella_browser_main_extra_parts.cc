// Copyright 2026 The Umbrella Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "chrome/browser/umbrella/umbrella_browser_main_extra_parts.h"

#include "chrome/browser/profiles/profile.h"
#include "chrome/browser/umbrella/common/umbrella_prefs.h"
#include "chrome/browser/umbrella/umbrella_default_search.h"
#include "chrome/common/pref_names.h"
#include "components/prefs/pref_service.h"

namespace umbrella {

UmbrellaBrowserMainExtraParts::UmbrellaBrowserMainExtraParts() = default;
UmbrellaBrowserMainExtraParts::~UmbrellaBrowserMainExtraParts() = default;

void UmbrellaBrowserMainExtraParts::PostProfileInit(
    Profile* profile,
    bool is_initial_profile) {
  if (!profile || profile->IsOffTheRecord()) {
    return;
  }

  EnsureDuckDuckGoDefaultSearch(profile);

  // Le schede verticali native sono una funzione Chromium: Umbrella ne cambia
  // solo il default al primo avvio. Dopo, la scelta dell'utente vince.
  PrefService* prefs = profile->GetPrefs();
  if (prefs && !prefs->GetBoolean(prefs::kVerticalTabsDefaultApplied)) {
    prefs->SetBoolean(::prefs::kVerticalTabsEnabled, true);
    prefs->SetBoolean(prefs::kVerticalTabsDefaultApplied, true);
  }
}

}  // namespace umbrella
