// Copyright 2026 The Umbrella Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "chrome/browser/umbrella/common/umbrella_version.h"

namespace umbrella {

std::string GetProductVersionString() {
  return "Umbrella " + std::string(kVersion) + " (Chromium " +
         std::string(kChromiumVersion) + ")";
}

std::string GetBuildInfoString() {
  return std::string(kChromiumCommit) + " / " + std::string(kVersion);
}

}  // namespace umbrella
