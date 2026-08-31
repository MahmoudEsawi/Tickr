cask "tickr" do
  version "1.0.0"
  sha256 "f160b139c4d999579900be8a5b9080f4c9deb22d523ff4984c94c92e3c55b083"

  url "https://github.com/MahmoudEsawi/Tickr/releases/download/v#{version}/Tickr-v#{version}.dmg"
  name "Tickr"
  desc "Minimalist macOS menu bar task engine with bidirectional JSON sync and 1-click CI/CD"
  homepage "https://github.com/MahmoudEsawi/Tickr"

  livecheck do
    url :url
    strategy :github_latest
  end

  auto_updates true
  depends_on macos: ">= :ventura"

  app "Tickr.app"

  zap trash: [
    "~/Library/Application Support/Tickr",
    "~/Library/LaunchAgents/com.mahmoudesawi.tickr.plist",
  ]
end
