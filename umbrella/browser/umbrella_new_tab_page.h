// Copyright 2026 The Umbrella Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef CHROME_BROWSER_UMBRELLA_UMBRELLA_NEW_TAB_PAGE_H_
#define CHROME_BROWSER_UMBRELLA_UMBRELLA_NEW_TAB_PAGE_H_

class GURL;
class Profile;

namespace umbrella {

// True quando la nuova scheda proprietaria è attiva per il profilo.
bool IsUmbrellaNewTabPageEnabled(Profile* profile);

// URL canonico della nuova scheda.
GURL GetUmbrellaNewTabURL();

}  // namespace umbrella

#endif  // CHROME_BROWSER_UMBRELLA_UMBRELLA_NEW_TAB_PAGE_H_
