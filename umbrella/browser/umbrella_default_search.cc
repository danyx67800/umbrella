// Copyright 2026 The Umbrella Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "chrome/browser/umbrella/umbrella_default_search.h"

#include <string>

#include "chrome/browser/profiles/profile.h"
#include "chrome/browser/search_engines/template_url_service_factory.h"
#include "chrome/browser/umbrella/common/umbrella_constants.h"
#include "chrome/browser/umbrella/common/umbrella_prefs.h"
#include "components/prefs/pref_service.h"
#include "components/search_engines/template_url.h"
#include "components/search_engines/template_url_service.h"

namespace umbrella {

namespace {

TemplateURL* FindDuckDuckGo(TemplateURLService* service) {
  for (TemplateURL* template_url : service->GetTemplateURLs()) {
    if (template_url->url().find(kDuckDuckGoKeyword) != std::string::npos) {
      return template_url;
    }
  }
  return nullptr;
}

}  // namespace

void EnsureDuckDuckGoDefaultSearch(Profile* profile) {
  if (!profile || profile->IsOffTheRecord()) {
    return;
  }

  PrefService* prefs = profile->GetPrefs();
  if (!prefs) {
    return;
  }
  if (prefs->GetBoolean(prefs::kDefaultSearchApplied)) {
    return;
  }

  TemplateURLService* service =
      TemplateURLServiceFactory::GetForProfile(profile);
  if (!service) {
    return;
  }

  // Il servizio può caricare le parole chiave in modo asincrono: in quel caso
  // non si tocca nulla e si riproverà al prossimo avvio.
  if (!service->loaded()) {
    service->Load();
  }
  if (!service->loaded()) {
    return;
  }

  const TemplateURL* current = service->GetDefaultSearchProvider();
  const bool already_duckduckgo =
      current && current->url().find(kDuckDuckGoKeyword) != std::string::npos;
  if (already_duckduckgo) {
    prefs->SetBoolean(prefs::kDefaultSearchApplied, true);
    return;
  }

  // Se l'utente ha scelto un motore diverso da quello predefinito upstream,
  // la scelta va rispettata. Si sostituisce solo il default "ereditato".
  const bool current_is_replaceable =
      !current ||
      current->url().find(kReplaceableSearchHostFragment) != std::string::npos;
  if (!current_is_replaceable) {
    return;
  }

  TemplateURL* duckduckgo = FindDuckDuckGo(service);
  if (!duckduckgo) {
    // Il motore non è nella lista prepopolata per questa configurazione
    // locale: nessuna creazione manuale, si riproverà al prossimo avvio.
    return;
  }

  service->SetUserSelectedDefaultSearchProvider(duckduckgo);
  prefs->SetBoolean(prefs::kDefaultSearchApplied, true);
}

}  // namespace umbrella
