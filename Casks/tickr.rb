cask "tickr" do
  version "1.0.0"
  sha256 "23593aa71376b5acce4e9404e674767cc52a273b87fa3987f891887a8a49d73d"

  url "https://github.com/MahmoudEsawi/Tickr/releases/download/v#{version}/Tickr-v#{version}-macOS.zip"
  name "Tickr"
  desc "Minimalist macOS menu bar task engine, Pomodoro timer & scratchpad"
  homepage "https://github.com/MahmoudEsawi/Tickr"

  app "Tickr.app"

  zap trash: [
    "~/Library/Application Support/Tickr",
    "~/Library/LaunchAgents/com.mahmoudesawi.tickr.plist",
  ]
end
