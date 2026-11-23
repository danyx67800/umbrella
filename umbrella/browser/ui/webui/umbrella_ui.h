// Copyright 2026 The Umbrella Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef CHROME_BROWSER_UMBRELLA_UI_WEBUI_UMBRELLA_UI_H_
#define CHROME_BROWSER_UMBRELLA_UI_WEBUI_UMBRELLA_UI_H_

#include "content/public/browser/web_ui_controller.h"
#include "content/public/browser/webui_config.h"

namespace umbrella {

// Controller della nuova scheda. Serve esclusivamente risorse locali incluse
// nei pak del browser: nessuna richiesta di rete, nessun contenuto remoto.
class UmbrellaUI : public content::WebUIController {
 public:
  explicit UmbrellaUI(content::WebUI* web_ui);
  ~UmbrellaUI() override;

  UmbrellaUI(const UmbrellaUI&) = delete;
  UmbrellaUI& operator=(const UmbrellaUI&) = delete;
};

// Registrata nella WebUIConfigMap di Chrome. Stesso pattern usato da
// AboutUIConfigBase nel sorgente upstream (content::DefaultWebUIConfig).
class UmbrellaUIConfig : public content::DefaultWebUIConfig<UmbrellaUI> {
 public:
  UmbrellaUIConfig();
};

}  // namespace umbrella

#endif  // CHROME_BROWSER_UMBRELLA_UI_WEBUI_UMBRELLA_UI_H_
