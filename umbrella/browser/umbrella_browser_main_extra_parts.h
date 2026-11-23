// Copyright 2026 The Umbrella Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef CHROME_BROWSER_UMBRELLA_UMBRELLA_BROWSER_MAIN_EXTRA_PARTS_H_
#define CHROME_BROWSER_UMBRELLA_UMBRELLA_BROWSER_MAIN_EXTRA_PARTS_H_

#include "chrome/browser/chrome_browser_main_extra_parts.h"

class Profile;

namespace umbrella {

// Punto di estensione ufficiale del browser process: viene registrato in
// chrome_browser_main.cc accanto agli extra parts di Views e profili.
class UmbrellaBrowserMainExtraParts : public ChromeBrowserMainExtraParts {
 public:
  UmbrellaBrowserMainExtraParts();
  ~UmbrellaBrowserMainExtraParts() override;

  UmbrellaBrowserMainExtraParts(const UmbrellaBrowserMainExtraParts&) = delete;
  UmbrellaBrowserMainExtraParts& operator=(
      const UmbrellaBrowserMainExtraParts&) = delete;

  // PostProfileInit è virtuale in ChromeBrowserMainExtraParts (Chromium 158).
  void PostProfileInit(Profile* profile, bool is_initial_profile) override;
};

}  // namespace umbrella

#endif  // CHROME_BROWSER_UMBRELLA_UMBRELLA_BROWSER_MAIN_EXTRA_PARTS_H_
