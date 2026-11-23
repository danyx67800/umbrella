// Copyright 2026 The Umbrella Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "chrome/browser/umbrella/umbrella_new_tab_page.h"

#include "chrome/browser/profiles/profile.h"
#include "chrome/browser/umbrella/common/umbrella_constants.h"
#include "chrome/browser/umbrella/common/umbrella_prefs.h"
#include "components/prefs/pref_service.h"
#include "url/gurl.h"

namespace umbrella {

bool IsUmbrellaNewTabPageEnabled(Profile* profile) {
  if (!profile || !profile->GetPrefs()) {
    return false;
  }
  return profile->GetPrefs()->GetBoolean(prefs::kNewTabPageEnabled);
}

GURL GetUmbrellaNewTabURL() {
  return GURL(kUmbrellaNewTabURL);
}

}  // namespace umbrella
