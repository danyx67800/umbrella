"""Punti di aggancio di Umbrella nel sorgente Chromium.

Ogni anchor è stato verificato sul tag 158.0.8127.37. Se un aggiornamento
upstream cambia una di queste righe, integrate.py --check fallisce e la
specifica va aggiornata leggendo il nuovo sorgente.
"""

from __future__ import annotations

from pathlib import Path

from .engine import (
    GnListAdd,
    InsertAfter,
    Operation,
    RegexReplace,
    Replace,
    ReplaceFile,
)

ROOT = Path(__file__).resolve().parents[1]
BRANDING = (ROOT / "design" / "BRANDING").read_text(encoding="utf-8")

CORE_TARGET = 'source_set("core")'
CONFIGS_TARGET = 'source_set("configs")'
RESOURCES_GROUP_ANCHOR = 'public_deps = [\n    "contextual_tasks:resources",'

UMBRELLA_SOURCES = [
    "umbrella/common/umbrella_prefs.cc",
    "umbrella/common/umbrella_version.cc",
    "umbrella/umbrella_browser_main_extra_parts.cc",
    "umbrella/umbrella_default_search.cc",
    "umbrella/umbrella_new_tab_page.cc",
]

WEBUI_CONFIG_ANCHOR = (
    "  map.AddWebUIConfig(std::make_unique<skills::SkillsUIConfig>());")

NEW_TAB_FUNCTION = """GURL GetNewTabPageURL(Profile* profile) {
  return NewTabURLDetails::ForProfile(profile).url;
}
"""

NEW_TAB_FUNCTION_PATCHED = """GURL GetNewTabPageURL(Profile* profile) {
  if (::umbrella::IsUmbrellaNewTabPageEnabled(profile)) {
    return ::umbrella::GetUmbrellaNewTabURL();
  }
  return NewTabURLDetails::ForProfile(profile).url;
}
"""


def _gn_source(value: str, description: str) -> GnListAdd:
    return GnListAdd(
        file="chrome/browser/BUILD.gn",
        marker=f'"{value}"',
        description=description,
        target=CORE_TARGET,
        list_name="sources",
        value=value,
    )


OPERATIONS: list[Operation] = [
    # 1. Sorgenti proprietarie nel target che contiene chrome_browser_main.cc.
    *[_gn_source(value, "overlay C++ Umbrella")
      for value in UMBRELLA_SOURCES],
    GnListAdd(
        file="chrome/browser/BUILD.gn",
        marker='"//components/search_engines",',
        description="TemplateURLService per il default search",
        target=CORE_TARGET,
        list_name="deps",
        value="//components/search_engines",
    ),
    GnListAdd(
        file="chrome/browser/BUILD.gn",
        marker='"//components/user_prefs",',
        description="registrazione preferenze di profilo",
        target=CORE_TARGET,
        list_name="deps",
        value="//components/user_prefs",
    ),

    # 2. Registrazione delle preferenze proprietarie.
    InsertAfter(
        file="chrome/browser/prefs/browser_prefs.cc",
        marker="umbrella/common/umbrella_prefs.h",
        description="include delle preferenze Umbrella",
        anchor='#include "chrome/browser/prefs/browser_prefs.h"',
        text='\n#include "chrome/browser/umbrella/common/umbrella_prefs.h"',
    ),
    InsertAfter(
        file="chrome/browser/prefs/browser_prefs.cc",
        marker="umbrella::prefs::RegisterProfilePrefs",
        description="registrazione preferenze nel profilo",
        anchor='  TRACE_EVENT0("browser", "chrome::RegisterProfilePrefs");\n',
        text="  umbrella::prefs::RegisterProfilePrefs(registry);\n",
    ),

    # 3. Nuova scheda: unico punto di verità per l'URL NTP.
    InsertAfter(
        file="chrome/browser/search/search.cc",
        marker="umbrella/umbrella_new_tab_page.h",
        description="include helper nuova scheda",
        anchor='#include "chrome/browser/search/search.h"',
        text='\n#include "chrome/browser/umbrella/umbrella_new_tab_page.h"',
    ),
    Replace(
        file="chrome/browser/search/search.cc",
        marker="::umbrella::IsUmbrellaNewTabPageEnabled",
        description="GetNewTabPageURL usa la nuova scheda Umbrella",
        old=NEW_TAB_FUNCTION,
        new=NEW_TAB_FUNCTION_PATCHED,
    ),

    # 4. Extra parts ufficiali: primo avvio.
    InsertAfter(
        file="chrome/browser/chrome_browser_main.cc",
        marker="umbrella/umbrella_browser_main_extra_parts.h",
        description="include extra parts Umbrella",
        anchor='#include "chrome/browser/chrome_browser_main_extra_parts.h"',
        text=('\n#include "chrome/browser/umbrella/'
              'umbrella_browser_main_extra_parts.h"'),
    ),
    InsertAfter(
        file="chrome/browser/chrome_browser_main.cc",
        marker="UmbrellaBrowserMainExtraParts",
        description="registrazione extra parts accanto a Views",
        anchor=("  main_parts->AddParts(std::make_unique<"
                "ChromeBrowserMainExtraPartsViews>());"),
        text=("\n\n  // Umbrella: impostazioni di primo avvio.\n"
              "  main_parts->AddParts(\n"
              "      std::make_unique<umbrella::"
              "UmbrellaBrowserMainExtraParts>());"),
    ),

    # 5. Registrazione della WebUI chrome://umbrella/.
    InsertAfter(
        file="chrome/browser/ui/webui/chrome_web_ui_configs.cc",
        marker="umbrella/ui/webui/umbrella_ui.h",
        description="include UmbrellaUIConfig",
        anchor='#include "chrome/browser/ui/webui/chrome_web_ui_configs.h"',
        text=('\n#include "chrome/browser/umbrella/'
              'ui/webui/umbrella_ui.h"'),
    ),
    InsertAfter(
        file="chrome/browser/ui/webui/chrome_web_ui_configs.cc",
        marker="umbrella::UmbrellaUIConfig",
        description="mappa host chrome://umbrella/",
        anchor=WEBUI_CONFIG_ANCHOR,
        text=("\n\n  // Umbrella new tab page.\n"
              "  map.AddWebUIConfig("
              "std::make_unique<umbrella::UmbrellaUIConfig>());"),
    ),

    # 6. Target GN della WebUI: sorgente + risorse grit.
    GnListAdd(
        file="chrome/browser/ui/webui/BUILD.gn",
        marker='"umbrella/ui/webui/umbrella_ui.cc",',
        description="controller WebUI Umbrella",
        target=CONFIGS_TARGET,
        list_name="sources",
        value="umbrella/ui/webui/umbrella_ui.cc",
    ),
    GnListAdd(
        file="chrome/browser/ui/webui/BUILD.gn",
        marker='"//chrome/browser/resources/umbrella:build_grd",',
        description="ID risorse della nuova scheda",
        target=CONFIGS_TARGET,
        list_name="deps",
        value="//chrome/browser/resources/umbrella:build_grd",
    ),

    # 7. Inclusione del pak della nuova scheda nei resources del browser.
    InsertAfter(
        file="chrome/browser/resources/BUILD.gn",
        marker='"umbrella:resources",',
        description="pak risorse nuova scheda",
        anchor=RESOURCES_GROUP_ANCHOR,
        text='\n    "umbrella:resources",',
    ),

    # 8. Branding: nome prodotto e metadati.
    ReplaceFile(
        file="chrome/app/theme/chromium/BRANDING",
        marker="PRODUCT_FULLNAME=Umbrella",
        description="metadati di prodotto Umbrella",
        expected_sha256=(
            "15ac20cb8744ebac0815961059231baefa71fd4ed3023cb2094aaf8a34ae423b"),
        content=BRANDING,
    ),
    RegexReplace(
        file="chrome/app/chromium_strings.grd",
        marker='desc="The Chrome application name" translateable="false">\n'
               "            Umbrella",
        description="IDS_PRODUCT_NAME",
        pattern=(
            r'(<message name="IDS_PRODUCT_NAME" '
            r'desc="The Chrome application name" translateable="false">\s*)'
            r"Chromium(\s*</message>)"),
        replacement=r"\1Umbrella\2",
        max_count=1,
    ),
    RegexReplace(
        file="chrome/app/chromium_strings.grd",
        marker='desc="The Chrome application short name." '
               'translateable="false">\n            Umbrella',
        description="IDS_SHORT_PRODUCT_NAME",
        pattern=(
            r'(<message name="IDS_SHORT_PRODUCT_NAME" '
            r'desc="The Chrome application short name." '
            r'translateable="false">\s*)Chromium(\s*</message>)'),
        replacement=r"\1Umbrella\2",
        max_count=1,
    ),
]
