// Copyright 2026 The Umbrella Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef CHROME_BROWSER_UMBRELLA_UMBRELLA_DEFAULT_SEARCH_H_
#define CHROME_BROWSER_UMBRELLA_UMBRELLA_DEFAULT_SEARCH_H_

class Profile;

namespace umbrella {

// Imposta DuckDuckGo come motore predefinito al primo avvio, riusando il
// TemplateURLService nativo. Non fa nulla se:
//  - il profilo è off-the-record;
//  - l'utente ha già scelto un motore diverso da quello predefinito upstream;
//  - il servizio non è ancora caricato (riprova al prossimo avvio).
void EnsureDuckDuckGoDefaultSearch(Profile* profile);

}  // namespace umbrella

#endif  // CHROME_BROWSER_UMBRELLA_UMBRELLA_DEFAULT_SEARCH_H_
