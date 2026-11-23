// Copyright 2026 The Umbrella Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "chrome/browser/umbrella/common/umbrella_prefs.h"

#include "components/prefs/pref_registry_simple.h"
#include "components/user_prefs/pref_registry_syncable.h"

namespace umbrella::prefs {

void RegisterProfilePrefs(user_prefs::PrefRegistrySyncable* registry) {
  // I default si applicano solo se l'utente non ha già scritto il valore:
  // un'eventuale scelta esplicita nelle impostazioni vince sempre.
  registry->RegisterBooleanPref(kNewTabPageEnabled, true);
  registry->RegisterBooleanPref(kDefaultSearchApplied, false);
  registry->RegisterBooleanPref(kVerticalTabsDefaultApplied, false);
  registry->RegisterIntegerPref(kSchemaVersion, kCurrentSchemaVersion);
}

}  // namespace umbrella::prefs
