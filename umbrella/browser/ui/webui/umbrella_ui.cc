// Copyright 2026 The Umbrella Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "chrome/browser/umbrella/ui/webui/umbrella_ui.h"

#include "chrome/grit/umbrella_resources.h"
#include "chrome/browser/umbrella/common/umbrella_constants.h"
#include "content/public/browser/browser_context.h"
#include "content/public/browser/web_contents.h"
#include "content/public/browser/web_ui.h"
#include "content/public/browser/web_ui_data_source.h"

namespace umbrella {

UmbrellaUI::UmbrellaUI(content::WebUI* web_ui) : content::WebUIController(web_ui) {
  content::BrowserContext* browser_context =
      web_ui->GetWebContents()->GetBrowserContext();

  content::WebUIDataSource* source =
      content::WebUIDataSource::CreateAndAdd(browser_context, kUmbrellaHost);
  source->SetDefaultResource(IDR_UMBRELLA_INDEX_HTML);
  source->AddResourcePath("app.css", IDR_UMBRELLA_APP_CSS);
  source->AddResourcePath("app.js", IDR_UMBRELLA_APP_JS);
  source->AddResourcePath("umbrella-mark.svg", IDR_UMBRELLA_UMBRELLA_MARK_SVG);
}

UmbrellaUI::~UmbrellaUI() = default;

UmbrellaUIConfig::UmbrellaUIConfig()
    : content::DefaultWebUIConfig<UmbrellaUI>(kUmbrellaHost) {}

}  // namespace umbrella
